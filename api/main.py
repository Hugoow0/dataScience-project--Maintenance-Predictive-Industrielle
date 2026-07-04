from __future__ import annotations

import json
import math
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .schemas import (
    ClassificationPredictionResponse,
    CorrelationPoint,
    DatasetStatsResponse,
    DateRange,
    FeatureInput,
    HealthResponse,
    HistogramBin,
    ModelComparisonResponse,
    ModelInfoItem,
    ModelInfoResponse,
    ModelMetricSet,
    NumericSummary,
    PredictRequest,
    RegressionPredictionResponse,
    TaskType,
    TimeSeriesPoint,
    ValueCount,
)


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "industrial_machine_maintenance.csv"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "maintenance_cleaned.csv"
MODELS_DIR = BASE_DIR / "models"

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

NUMERIC_FEATURES = [
    "vibration_rms",
    "temperature_motor",
    "current_phase_avg",
    "pressure_level",
    "rpm",
    "hours_since_maintenance",
    "ambient_temp",
]

CATEGORICAL_FEATURES = ["operating_mode", "machine_type", "failure_type"]
DEFAULT_MACHINE_TYPE = "CNC"


@dataclass(frozen=True)
class ModelBundle:
    canonical_name: str
    file_name: str
    file_path: Path
    estimator: Any
    task_type: str
    target_variable: str
    aliases: tuple[str, ...]
    preprocessor: Any | None = None
    metrics_path: Path | None = None
    metrics: dict[str, float] | None = None

    @property
    def loaded(self) -> bool:
        return self.estimator is not None

    def _prepare_frame(self, features: FeatureInput) -> pd.DataFrame:
        payload = features.model_dump(mode="json", exclude_none=True)
        payload.setdefault("machine_type", DEFAULT_MACHINE_TYPE)
        ordered = {column: payload[column] for column in FEATURE_ORDER}
        return pd.DataFrame([ordered], columns=FEATURE_ORDER)

    def predict_frame(self, frame: pd.DataFrame) -> np.ndarray:
        if self.preprocessor is not None and not hasattr(self.estimator, "named_steps"):
            transformed = self.preprocessor.transform(frame)
            return np.asarray(self.estimator.predict(transformed))
        return np.asarray(self.estimator.predict(frame))

    def predict_proba_frame(self, frame: pd.DataFrame) -> np.ndarray | None:
        if not hasattr(self.estimator, "predict_proba"):
            return None
        if self.preprocessor is not None and not hasattr(self.estimator, "named_steps"):
            transformed = self.preprocessor.transform(frame)
            return np.asarray(self.estimator.predict_proba(transformed))
        return np.asarray(self.estimator.predict_proba(frame))

    def predict(self, features: FeatureInput) -> np.ndarray:
        return self.predict_frame(self._prepare_frame(features))

    def predict_proba(self, features: FeatureInput) -> np.ndarray | None:
        return self.predict_proba_frame(self._prepare_frame(features))


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def canonical_model_name(file_name: str) -> str:
    stem = Path(file_name).stem
    stem = re.sub(r"[-_](model|classifier|pipeline|estimator)$", "", stem, flags=re.IGNORECASE)
    stem = stem.replace("-preprocessor", "").replace("_preprocessor", "")
    return normalize_name(stem)


def infer_task_type(bundle: Any) -> str:
    if hasattr(bundle, "classes_"):
        return "multi_class" if len(getattr(bundle, "classes_", [])) > 2 else "classification"
    if hasattr(bundle, "predict_proba"):
        return "classification"
    return "regression"


def infer_target_variable(model_name: str, task_type: str) -> str:
    name = model_name.lower()
    if "rul" in name or task_type == "regression":
        return "rul_hours"
    if "cost" in name:
        return "estimated_repair_cost"
    if "type" in name:
        return "failure_type"
    return "failure_within_24h"


def infer_unit(target_variable: str) -> str:
    if "rul" in target_variable or "hour" in target_variable:
        return "hours"
    if "cost" in target_variable:
        return "currency"
    return "value"


def label_for_prediction(prediction: Any, task_type: str) -> str:
    if task_type == "classification":
        return "failure" if str(prediction) in {"1", "True", "true"} else "no_failure"
    if task_type == "multi_class":
        return str(prediction)
    return infer_unit(str(prediction))


@lru_cache(maxsize=1)
def load_raw_dataset() -> pd.DataFrame:
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset introuvable: {RAW_DATA_PATH}")
    return pd.read_csv(RAW_DATA_PATH, parse_dates=["timestamp"])


@lru_cache(maxsize=1)
def load_processed_dataset() -> pd.DataFrame:
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset nettoyé introuvable: {PROCESSED_DATA_PATH}")
    return pd.read_csv(PROCESSED_DATA_PATH)


def load_metrics_file(path: Path) -> dict[str, float] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    metrics = payload.get("metrics", payload)
    return {key: float(value) for key, value in metrics.items() if isinstance(value, (int, float))}


def discover_bundles() -> dict[str, ModelBundle]:
    bundles: dict[str, ModelBundle] = {}
    preprocessor_paths: dict[str, Path] = {}
    estimator_paths: dict[str, Path] = {}

    for path in MODELS_DIR.glob("*.pkl"):
        normalized = canonical_model_name(path.name)
        if "preprocessor" in path.stem.lower():
            preprocessor_paths[normalized] = path
            continue
        estimator_paths[normalized] = path

    for canonical_name, estimator_path in estimator_paths.items():
        estimator = joblib.load(estimator_path)
        preprocessor_path = preprocessor_paths.get(canonical_name)
        preprocessor = joblib.load(preprocessor_path) if preprocessor_path else None
        task_type = infer_task_type(estimator)
        target_variable = infer_target_variable(canonical_name, task_type)
        aliases = {canonical_name, normalize_name(estimator_path.stem)}
        if "random_forest" in canonical_name:
            aliases.add("rf")
        if "logistic_regression" in canonical_name:
            aliases.add("lr")
        if "xgb" in canonical_name:
            aliases.add("xgb")
        metrics_path = MODELS_DIR / f"{canonical_name}_metrics.json"
        bundles[canonical_name] = ModelBundle(
            canonical_name=canonical_name,
            file_name=estimator_path.name,
            file_path=estimator_path,
            estimator=estimator,
            task_type=task_type,
            target_variable=target_variable,
            aliases=tuple(sorted(aliases)),
            preprocessor=preprocessor,
            metrics_path=metrics_path,
            metrics=load_metrics_file(metrics_path),
        )
    return bundles


def build_alias_lookup(bundles: dict[str, ModelBundle]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical_name, bundle in bundles.items():
        for alias in bundle.aliases:
            lookup[normalize_name(alias)] = canonical_name
    return lookup


def resolve_bundle(model_name: str) -> ModelBundle:
    alias = normalize_name(model_name)
    canonical_name = MODEL_ALIAS_LOOKUP.get(alias)
    if canonical_name is None:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Unknown model '{model_name}'.",
                "available_models": sorted(MODEL_ALIAS_LOOKUP.keys()),
            },
        )
    return MODEL_REGISTRY[canonical_name]


def make_error_response(error: str, detail: Any, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error, "detail": detail})


def get_bundle_metrics(bundle: ModelBundle) -> dict[str, float] | None:
    if bundle.metrics is not None:
        return bundle.metrics
    if bundle.metrics_path is None:
        return None
    return load_metrics_file(bundle.metrics_path)


def ensure_metrics_file(bundle: ModelBundle) -> dict[str, float] | None:
    existing = get_bundle_metrics(bundle)
    if existing is not None:
        return existing

    dataset = load_raw_dataset()
    if bundle.target_variable not in dataset.columns:
        return None

    dataset = dataset.dropna(subset=FEATURE_ORDER + [bundle.target_variable]).copy()

    features = dataset[FEATURE_ORDER].copy()
    if "machine_type" not in features.columns:
        features["machine_type"] = DEFAULT_MACHINE_TYPE
    features = features[FEATURE_ORDER]
    target = dataset[bundle.target_variable]

    stratify = target if bundle.task_type != "regression" and target.nunique() > 1 else None
    _, X_test, _, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    if bundle.task_type == "regression":
        predictions = bundle.predict_frame(X_test)
        metrics = {
            "mae": float(mean_absolute_error(y_test, predictions)),
            "rmse": float(math.sqrt(mean_squared_error(y_test, predictions))),
            "r2": float(r2_score(y_test, predictions)),
        }
    else:
        predictions = bundle.predict_frame(X_test)
        average = "binary" if bundle.task_type == "classification" else "weighted"
        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(precision_score(y_test, predictions, zero_division=0, average=average)),
            "recall": float(recall_score(y_test, predictions, zero_division=0, average=average)),
            "f1": float(f1_score(y_test, predictions, zero_division=0, average=average)),
        }
        probabilities = bundle.predict_proba_frame(X_test)
        if probabilities is not None:
            if len(np.unique(y_test)) == 2:
                metrics["roc_auc"] = float(roc_auc_score(y_test, probabilities[:, 1]))
            else:
                metrics["roc_auc"] = float(roc_auc_score(y_test, probabilities, multi_class="ovr", average="weighted"))

    bundle.metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with bundle.metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "model": bundle.canonical_name,
                "task_type": bundle.task_type,
                "target_variable": bundle.target_variable,
                "metrics": metrics,
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
    return metrics


def build_numeric_summary(series: pd.Series) -> NumericSummary:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    histogram_counts, histogram_edges = np.histogram(clean, bins=20)
    histogram = [
        HistogramBin(left=float(left), right=float(right), count=int(count))
        for left, right, count in zip(histogram_edges[:-1], histogram_edges[1:], histogram_counts)
    ]
    return NumericSummary(
        min=float(clean.min()),
        max=float(clean.max()),
        mean=float(clean.mean()),
        median=float(clean.median()),
        std=float(clean.std(ddof=0)),
        histogram=histogram,
    )


def build_dataset_stats() -> DatasetStatsResponse:
    dataset = load_raw_dataset()
    row_count = int(dataset.shape[0])
    column_count = int(dataset.shape[1])

    timestamp_series = pd.to_datetime(dataset["timestamp"], errors="coerce") if "timestamp" in dataset.columns else None
    date_range = None
    if timestamp_series is not None and timestamp_series.notna().any():
        date_range = DateRange(start=timestamp_series.min().isoformat(), end=timestamp_series.max().isoformat())

    class_balance = {
        "no_failure": float((dataset["failure_within_24h"] == 0).mean() * 100.0),
        "failure": float((dataset["failure_within_24h"] == 1).mean() * 100.0),
    }

    numeric_summary = {column: build_numeric_summary(dataset[column]) for column in NUMERIC_FEATURES if column in dataset.columns}

    categorical_summary: dict[str, dict[str, ValueCount]] = {}
    for column in CATEGORICAL_FEATURES:
        if column not in dataset.columns:
            continue
        counts = dataset[column].fillna("Unknown").value_counts(dropna=False)
        total = counts.sum() or 1
        categorical_summary[column] = {
            str(index): ValueCount(count=int(count), percentage=float(count / total * 100.0))
            for index, count in counts.items()
        }

    numeric_for_corr = [column for column in NUMERIC_FEATURES if column in dataset.columns]
    corr_frame = dataset[numeric_for_corr].corr(method="pearson") if numeric_for_corr else pd.DataFrame()
    correlation_matrix = [
        CorrelationPoint(x=str(x), y=str(y), value=float(corr_frame.loc[x, y]))
        for i, x in enumerate(corr_frame.columns)
        for y in corr_frame.columns[i:]
    ]

    missing_values = {
        column: ValueCount(count=int(dataset[column].isna().sum()), percentage=float(dataset[column].isna().mean() * 100.0))
        for column in dataset.columns
    }

    if timestamp_series is not None:
        sample_step = max(len(dataset) // 150, 1)
        sample_frame = dataset.iloc[::sample_step].copy()
        sample_frame["timestamp"] = pd.to_datetime(sample_frame["timestamp"], errors="coerce")
        time_series_sample = [
            TimeSeriesPoint(
                timestamp=row.timestamp.isoformat() if pd.notna(row.timestamp) else "",
                vibration_rms=float(row.vibration_rms),
                temperature_motor=float(row.temperature_motor),
            )
            for row in sample_frame.itertuples(index=False)
        ]
    else:
        time_series_sample = None

    return DatasetStatsResponse(
        row_count=row_count,
        column_count=column_count,
        date_range=date_range,
        class_balance=class_balance,
        numeric_summary=numeric_summary,
        categorical_summary=categorical_summary,
        correlation_matrix=correlation_matrix,
        missing_values=missing_values,
        time_series_sample=time_series_sample,
    )


def build_model_info() -> ModelInfoResponse:
    items: list[ModelInfoItem] = []
    for bundle in MODEL_REGISTRY.values():
        metrics = get_bundle_metrics(bundle)
        items.append(
            ModelInfoItem(
                model=bundle.canonical_name,
                file_name=bundle.file_name,
                task_type=TaskType(bundle.task_type),
                target_variable=bundle.target_variable,
                loaded=bundle.loaded,
                aliases=list(bundle.aliases),
                metrics=metrics,
            )
        )
    return ModelInfoResponse(models=sorted(items, key=lambda item: item.model))


def build_model_comparison() -> ModelComparisonResponse:
    rows: list[ModelMetricSet] = []
    for bundle in MODEL_REGISTRY.values():
        metrics = ensure_metrics_file(bundle)
        rows.append(
            ModelMetricSet(
                model=bundle.canonical_name,
                task_type=TaskType(bundle.task_type),
                target_variable=bundle.target_variable,
                file_name=bundle.file_name,
                metrics=metrics or {},
            )
        )
    return ModelComparisonResponse(models=sorted(rows, key=lambda item: item.model))


MODEL_REGISTRY = discover_bundles()
MODEL_ALIAS_LOOKUP = build_alias_lookup(MODEL_REGISTRY)
DATASET_STATS = build_dataset_stats()
MODEL_INFO = build_model_info()
MODEL_COMPARISON = build_model_comparison()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="Predictive Maintenance API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return make_error_response("Validation error", exc.errors(), status_code=422)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, (str, list, dict)) else str(exc.detail)
    return make_error_response("Request error", detail, status_code=exc.status_code)


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return make_error_response("Internal server error", "An unexpected error occurred during inference.", status_code=500)


@app.on_event("startup")
def warm_up_caches() -> None:
    _ = MODEL_REGISTRY
    _ = DATASET_STATS
    _ = MODEL_INFO
    _ = MODEL_COMPARISON


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", models_loaded=[bundle.canonical_name for bundle in MODEL_REGISTRY.values() if bundle.loaded])


@app.get("/model-info", response_model=ModelInfoResponse, tags=["models"])
async def get_model_info() -> ModelInfoResponse:
    return MODEL_INFO


@app.get("/dataset/stats", response_model=DatasetStatsResponse, tags=["dataset"])
async def get_dataset_stats() -> DatasetStatsResponse:
    return DATASET_STATS


@app.get("/dataset/model-comparison", response_model=ModelComparisonResponse, tags=["dataset"])
async def get_model_comparison() -> ModelComparisonResponse:
    return MODEL_COMPARISON


@app.post("/predict", response_model=ClassificationPredictionResponse | RegressionPredictionResponse, tags=["inference"])
async def predict(payload: PredictRequest):
    bundle = resolve_bundle(payload.model)

    try:
        prediction = bundle.predict(payload.features)[0]
        if bundle.task_type == "regression":
            return RegressionPredictionResponse(
                task_type="regression",
                model=bundle.canonical_name,
                prediction=float(prediction),
                unit=infer_unit(bundle.target_variable),
            )

        probabilities = bundle.predict_proba(payload.features)
        probability = float(np.max(probabilities[0])) if probabilities is not None else 1.0
        return ClassificationPredictionResponse(
            task_type=bundle.task_type,  # type: ignore[arg-type]
            model=bundle.canonical_name,
            prediction=int(prediction) if str(prediction).isdigit() else str(prediction),
            probability=probability,
            label=label_for_prediction(prediction, bundle.task_type),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed for model '{bundle.canonical_name}'.") from exc
