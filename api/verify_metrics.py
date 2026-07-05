"""
verify_metrics.py  --  Independent metric recomputation
========================================================
Recomputes all model metrics from scratch, independently from the API,
using the same methodology as ensure_metrics_file() in main.py:

  1. Load the raw CSV dataset
  2. Stratified 80/20 train-test split (random_state=42)
  3. Apply per-model preprocessing (label encoding, scaling)
  4. Evaluate: accuracy, precision, recall, F1, ROC-AUC
  5. Compare against the stored JSON files and flag discrepancies

Usage:
    python -m api.verify_metrics
    python -m api.verify_metrics --delete-cache   # force-delete json files first

Source of each JSON file:
  logistic_regression_metrics.json   -> pre-computed in the training notebook
  random_forest_metrics.json         -> pre-computed in the training notebook
  modele_deep_learning_sgd_metrics.json -> computed by ensure_metrics_file() on
                                          first API startup when file was absent
  voting_classifier_metrics.json     -> MANUALLY EDITED during the rename
                                        (stale values, not computed from data!)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

BASE_DIR   = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
RAW_DATA   = BASE_DIR / "data" / "raw" / "industrial_machine_maintenance.csv"

FEATURE_ORDER = [
    "machine_type",
    "vibration_rms",
    "temperature_motor",
    "current_phase_avg",
    "pressure_level",
    "rpm",
    "operating_mode",
    "hours_since_maintenance",
    "ambient_temp",
]
TARGET = "failure_within_24h"
LEGACY_MODELS = {"voting_classifier", "modele_deep_learning_sgd"}

SEP  = "-" * 82
DSEP = "=" * 82


# ─── helpers ─────────────────────────────────────────────────────────────────

def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(RAW_DATA)
    df = df.dropna(subset=FEATURE_ORDER + [TARGET]).copy()
    X = df[FEATURE_ORDER].copy()
    y = df[TARGET].astype(int)
    return X, y


def label_encode(X: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    X = X.copy()
    encoders: dict[str, LabelEncoder] = {}
    for col in X.select_dtypes(include=["object"]).columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le
    return X, encoders


def split_data(X: pd.DataFrame, y: pd.Series):
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def compute_metrics(y_true, y_pred, y_prob=None) -> dict[str, float]:
    m: dict[str, float] = {
        "accuracy":  round(float(accuracy_score(y_true, y_pred)),  4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall":    round(float(recall_score(y_true, y_pred, zero_division=0)),    4),
        "f1":        round(float(f1_score(y_true, y_pred, zero_division=0)),        4),
    }
    if y_prob is not None:
        m["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
    return m


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("metrics", payload)


def compare(label: str, stored: dict | None, computed: dict) -> bool:
    """Print side-by-side comparison. Returns True if values match."""
    all_ok = True
    keys = sorted(set((stored or {}).keys()) | set(computed.keys()))
    print(f"\n  {'METRIC':<12} {'STORED':>10} {'RECOMPUTED':>12} {'DELTA':>10} {'OK?':>5}")
    print(f"  {'-'*52}")
    for k in keys:
        s = stored.get(k) if stored else None
        c = computed.get(k)
        if s is None:
            print(f"  {k:<12} {'[missing]':>10} {c:>12.4f} {'---':>10}  ???")
            all_ok = False
        elif c is None:
            print(f"  {k:<12} {s:>10.4f} {'[missing]':>12} {'---':>10}  ???")
        else:
            delta = abs(s - c)
            ok = delta < 0.01          # allow 1% rounding tolerance
            sym = "OK" if ok else "MISMATCH"
            if not ok:
                all_ok = False
            print(f"  {k:<12} {s:>10.4f} {c:>12.4f} {delta:>+10.4f}  {sym}")
    return all_ok


# ─── per-model evaluators ─────────────────────────────────────────────────────

def evaluate_standard(pkl_path: Path, canonical: str, X_train, X_test, y_test) -> dict:
    """Standard sklearn pipeline: predict directly on raw features."""
    model = joblib.load(pkl_path)
    preprocessor_path = None
    for candidate in MODELS_DIR.glob("*.pkl"):
        if "preprocessor" in candidate.stem.lower():
            stem = candidate.stem.replace("-preprocessor", "").replace("_preprocessor", "")
            if canonical in stem or stem in canonical:
                preprocessor_path = candidate
                break

    if preprocessor_path and preprocessor_path.exists():
        pre = joblib.load(preprocessor_path)
        X_eval = pre.transform(X_test)
    else:
        X_eval = X_test

    y_pred = model.predict(X_eval)
    y_prob = model.predict_proba(X_eval)[:, 1] if hasattr(model, "predict_proba") else None
    return compute_metrics(y_test, y_pred, y_prob)


def evaluate_legacy(pkl_path: Path, canonical: str, X_train, X_test, y_test) -> dict:
    """Legacy models: label-encode categoricals; SGD also needs StandardScaler."""
    model = joblib.load(pkl_path)

    # Fit encoders on train split
    X_train_enc = X_train.copy()
    encoders: dict[str, LabelEncoder] = {}
    for col in X_train_enc.select_dtypes(include=["object"]).columns:
        le = LabelEncoder()
        X_train_enc[col] = le.fit_transform(X_train_enc[col].astype(str))
        encoders[col] = le

    # Apply to test split
    X_test_enc = X_test.copy()
    for col, le in encoders.items():
        X_test_enc[col] = le.transform(X_test_enc[col].astype(str))

    scale = canonical == "modele_deep_learning_sgd"
    if scale:
        scaler = StandardScaler().fit(X_train_enc)
        X_eval = pd.DataFrame(scaler.transform(X_test_enc), columns=FEATURE_ORDER)
    else:
        X_eval = X_test_enc

    y_raw = model.predict(X_eval)
    y_raw_flat = np.asarray(y_raw).reshape(-1)

    # Deep-learning SGD outputs continuous scores, not class labels
    if y_raw_flat.dtype.kind == "f" and not np.all(np.isin(y_raw_flat, [0.0, 1.0])):
        y_prob = y_raw_flat
        y_pred = (y_raw_flat >= 0.5).astype(int)
    elif hasattr(model, "predict_proba"):
        raw_prob = model.predict_proba(X_eval)
        if raw_prob.ndim == 2 and raw_prob.shape[1] == 2:
            y_prob = raw_prob[:, 1]
        else:
            y_prob = raw_prob.reshape(-1)
        y_pred = y_raw_flat.astype(int)
    else:
        y_prob = None
        y_pred = y_raw_flat.astype(int)

    return compute_metrics(y_test, y_pred, y_prob)


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Independent metric verification")
    parser.add_argument("--delete-cache", action="store_true",
                        help="Delete all *_metrics.json files before re-verifying")
    args = parser.parse_args()

    if args.delete_cache:
        for p in MODELS_DIR.glob("*_metrics.json"):
            p.unlink()
            print(f"  Deleted: {p.name}")

    print(f"\n{DSEP}")
    print("  METRIC VERIFICATION -- recomputing from raw data (same split as API)")
    print(DSEP)
    print(f"\n  Dataset   : {RAW_DATA}")
    print(f"  Split     : 80% train / 20% test, stratified, random_state=42")
    print(f"  Tolerance : delta < 0.01 considered a match\n")

    # Load & split data once
    X, y = load_dataset()
    X_train, X_test, y_train, y_test = split_data(X, y)

    print(f"  Dataset shape : {X.shape[0]} rows x {X.shape[1]} features")
    print(f"  Test set size : {len(y_test)} rows")
    failure_rate = y_test.mean()
    print(f"  Failure rate  : {failure_rate:.1%} positive ({int(y_test.sum())} failures)")

    # Discover model pkl files
    model_files: dict[str, Path] = {}
    for p in MODELS_DIR.glob("*.pkl"):
        if "preprocessor" in p.stem.lower():
            continue
        # canonical name derivation (mirrors main.py)
        import re
        stem = p.stem
        stem = re.sub(r"[-_](model|classifier|pipeline|estimator)$", "", stem, flags=re.IGNORECASE)
        canonical = re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")
        model_files[canonical] = p

    if not model_files:
        print("\n  [!] No model pkl files found in models/. Exiting.")
        sys.exit(1)

    all_pass = True

    for canonical, pkl_path in sorted(model_files.items()):
        json_path = MODELS_DIR / f"{canonical}_metrics.json"
        stored = load_json(json_path)
        origin = "[pre-computed notebook]" if stored and json_path.exists() else "[missing -- would be computed at API startup]"

        print(f"\n{SEP}")
        print(f"  MODEL : {canonical}")
        print(f"  FILE  : {pkl_path.name}")
        print(f"  JSON  : {json_path.name}  {origin}")
        print(SEP)

        try:
            if canonical in LEGACY_MODELS:
                computed = evaluate_legacy(pkl_path, canonical, X_train, X_test, y_test)
            else:
                computed = evaluate_standard(pkl_path, canonical, X_train, X_test, y_test)
        except Exception as exc:
            print(f"  [!] Evaluation FAILED: {exc}")
            all_pass = False
            continue

        ok = compare(canonical, stored, computed)
        if not ok:
            all_pass = False

    print(f"\n{DSEP}")
    if all_pass:
        print("  RESULT: All stored metrics match recomputed values. Files are trustworthy.")
    else:
        print("  RESULT: Some stored metrics do NOT match. See MISMATCH rows above.")
        print("  To refresh all files: python -m api.verify_metrics --delete-cache")
    print(DSEP + "\n")


if __name__ == "__main__":
    main()
