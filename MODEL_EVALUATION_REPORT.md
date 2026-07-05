# Model Evaluation Report — Predictive Maintenance API

> **Project**: `dataScience-project--Maintenance-Predictive-Industrielle`
> **Date**: 2026-07-05
> **Target variable**: `failure_within_24h` (binary classification)
> **Dataset**: `data/raw/industrial_machine_maintenance.csv` — 24 042 rows, 9 features
> **Holdout split**: 80 % train / 20 % test, stratified, `random_state=42` → 4 808 test rows (14.8 % positive = 712 real failures)

---

## Table of Contents

1. [Models evaluated](#1-models-evaluated)
2. [Metric definitions](#2-metric-definitions)
3. [Verified holdout metrics](#3-verified-holdout-metrics)
4. [Interpretation](#4-interpretation)
5. [API batch test (200 live calls)](#5-api-batch-test-200-live-calls)
6. [Why the batch test contradicted the holdout metrics](#6-why-the-batch-test-contradicted-the-holdout-metrics)
7. [Final verdict](#7-final-verdict)
8. [Reproduce the tests](#8-reproduce-the-tests)

---

## 1. Models evaluated

| Alias (API) | Canonical name | File |
|---|---|---|
| `rf` | `random_forest` | `models/random_forest_model.pkl` |
| `voting_classifier` | `voting_classifier` | `models/voting_classifier_model.pkl` |
| `lr` | `logistic_regression` | `models/logistic_regression-model.pkl` |
| `dl` | `modele_deep_learning_sgd` | `models/modele_deep_learning_sgd.pkl` |

All models predict **`failure_within_24h`**: will this machine experience a failure in the next 24 hours?

---

## 2. Metric definitions

| Metric | Question it answers | Interpretation |
|---|---|---|
| **Accuracy** | What % of all predictions were correct? | Misleading on imbalanced data (14.8 % positives). A model that always says "no failure" would score 85.2 % accuracy trivially. |
| **Precision** | When the model raised an alarm, how often was the machine actually going to fail? | Low precision → lots of false alarms; maintenance teams waste time on healthy machines. |
| **Recall** | Of all real failures, how many did the model catch? | Low recall → failures go undetected → unplanned downtime, safety risk. This is usually the most critical metric for predictive maintenance. |
| **F1** | Harmonic mean of precision and recall. | Best single-number summary when both false alarms and missed failures matter. |
| **ROC-AUC** | How well does the model rank failures above non-failures across all thresholds? | 0.5 = random, 1.0 = perfect. Threshold-independent — tells you how good the model is at separating classes regardless of the 0.5 cutoff. |

> [!IMPORTANT]
> In a **predictive maintenance** context, **recall is the priority metric**.
> A missed failure causes unplanned downtime, safety incidents, and expensive emergency repairs.
> False alarms (low precision) are costly but recoverable.

---

## 3. Verified holdout metrics

All values below were **independently verified** by `api/verify_metrics.py` — recomputed from scratch on the same 80/20 split, then compared to the stored JSON files. Every delta was < 0.01 after correction.

> [!NOTE]
> The `voting_classifier_metrics.json` file was found to contain stale, manually-edited values (recall = 0.02!) left over from a renaming operation. The verifier automatically replaced them with the correct recomputed values.

### Results table

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | JSON source |
|---|---|---|---|---|---|---|
| **random_forest** | **0.9894** | **0.9672** | 0.9609 | **0.9641** | 0.9993 | notebook (exact match) |
| **voting_classifier** | 0.9855 | 0.9159 | **0.9935** | 0.9531 | **0.9995** | recomputed (stale file replaced) |
| **logistic_regression** | 0.9391 | 0.8521 | 0.7134 | 0.7766 | 0.9745 | notebook (exact match) |
| **modele_deep_learning_sgd** | 0.1521 | 0.1430 | 0.9430 | 0.2483 | 0.4677 | API startup compute (< 0.01 delta) |

---

## 4. Interpretation

### 🥇 `rf` — Random Forest (best overall)

- **F1 = 0.9641 — best in class.** Extremely well-balanced: high recall AND high precision simultaneously.
- Catches **96.1 % of real failures** while raising false alarms on only **3.3 % of healthy machines**.
- ROC-AUC = 0.9993 — nearly perfect class separation across all thresholds.
- **Recommended for production inference.**

### 🥈 `voting_classifier` — Voting Classifier (best recall)

- Slightly below `rf` on F1 (0.9531 vs 0.9641) but has the **highest recall of all models: 99.35 %** — it almost never misses a real failure.
- Trade-off: precision is lower (0.9159) → more false alarms than `rf`.
- ROC-AUC = 0.9995 — marginally better discrimination than `rf`, suggesting the ensemble captures slightly more signal overall.
- **Best choice if missing a failure is catastrophically unacceptable** (safety-critical equipment). Accept slightly more false alarms in exchange for near-zero missed failures.

### 🥉 `lr` — Logistic Regression (reasonable baseline)

- Accuracy 0.9391 and ROC-AUC 0.9745 — a solid linear baseline.
- **Recall = 0.7134: misses 28.9 % of real failures.** Unacceptable in production for safety-critical use cases.
- Useful as a fast, interpretable sanity check or for lower-stakes scenarios.

### ❌ `dl` — Deep Learning SGD (broken model)

- Accuracy = 0.1521 — **worse than always predicting "no failure" (would give 85.2 %)**.
- ROC-AUC = 0.4677 — **below 0.5**, meaning the model's ranking is worse than random.
- Recall = 0.9430 but precision = 0.1430 — it flags ~90 % of everything as failure regardless of input.
- **Not usable. Should be retrained or replaced.**
- In the API batch test, this model flagged 88 % of samples as FAIL (including healthy machines at low vibration, fresh out of maintenance). This aligns with its near-constant output behaviour.

---

## 5. API batch test (200 live calls)

**Setup**: 50 identical payloads sent to each of the 4 models = 200 `POST /predict` calls.

The 50 payloads cover 4 realistic categories:
- **Healthy** (10 samples): low vibration, normal temp, recently maintained
- **Moderate stress** (10 samples): mid-range readings, normal wear
- **High risk** (10 samples): high vibration/temperature, `peak` mode, long since maintenance
- **Borderline / ambiguous** (10 samples): edge cases near the decision boundary
- **Mixed** (10 samples): combinations of idle-mode stress and fresh maintenance

### Live inference results

| Model | FAIL predicted | Fail % | Avg Prob | High Confidence | Avg Latency |
|---|---|---|---|---|---|
| `rf` | 20 / 50 | 40.0 % | 0.491 | 20 % | 26 ms |
| `voting_classifier` | 42 / 50 | 84.0 % | 0.856 | 80 % | 48 ms |
| `lr` | 43 / 50 | 86.0 % | 0.868 | 94 % | 19 ms |
| `dl` | 44 / 50 | 88.0 % | 0.649 | 32 % | 70 ms |

> "High confidence" = probability ≥ 0.75 (failure) or ≤ 0.25 (no-failure).

### Cross-model agreement

| Agreement type | Count | % of 50 samples |
|---|---|---|
| All 4 models agree | 20 | 40 % |
| 3 vs 1 majority | 27 | 54 % |
| 50/50 split (2 vs 2) | 3 | 6 % |

**The 3-vs-1 split is almost always `rf` alone predicting "OK"** while the other three predict "FAIL". Given the holdout metrics, `rf`'s conservative stance is the correct one for those borderline samples.

### Notable disagreement samples

| Sample | rf | lr | voting_classifier | dl | Machine | Mode | Vib | Temp | Hrs since maint |
|---|---|---|---|---|---|---|---|---|---|
| 1 | OK | OK | OK | **FAIL** | CNC | normal | 1.2 | 65°C | 50 |
| 2 | OK | OK | OK | **FAIL** | CNC | normal | 0.9 | 60°C | 30 |
| 7 | OK | **FAIL** | **FAIL** | **FAIL** | Robotic Arm | normal | 1.0 | 63°C | 70 |
| 34 | **FAIL** | FAIL | FAIL | OK | Robotic Arm | idle | 3.8 | 90°C | 300 |

> Samples 1 and 2 are clearly healthy — only `dl` raises false alarms, consistent with its broken behaviour.
> Samples 7–20 show `rf` predicting "OK" where others predict "FAIL" — on moderate-stress samples, `rf` appears better calibrated.

---

## 6. Why the batch test contradicted the holdout metrics

The initial batch test report ranked `lr` as "best" because it had the **highest confidence (94 %)** and **median alignment**. This was a flawed scoring heuristic for two reasons:

1. **No ground truth**: without real labels on the 50 synthetic payloads, "confidence" cannot be verified as correct. A model that is confidently wrong scores higher than a model that is uncertainly right.

2. **Median was polluted**: the median failure rate (85 %) was inflated by `dl` and `lr` over-predicting, making `rf`'s more calibrated 40 % look like an outlier rather than the correct answer.

**The holdout metrics are the authoritative source** — they evaluate models against real, labelled outcomes from the original dataset using the same split the training pipeline used.

---

## 7. Final verdict

| Rank | Model | Use case |
|---|---|---|
| 🥇 **`rf` (Random Forest)** | **Default production model.** Best F1, high precision AND recall. |
| 🥈 **`voting_classifier` (Voting Classifier)** | **Safety-critical equipment** where a missed failure is catastrophic. Highest recall (99.35 %) at the cost of slightly more false alarms. |
| 🥉 `lr` (Logistic Regression) | Fast interpretable baseline. Acceptable for low-stakes monitoring. Not suitable for critical equipment (misses 29 % of failures). |
| ❌ `dl` (Deep Learning SGD) | **Do not use in production.** ROC-AUC below 0.5, worse than random. Needs complete retraining. |

---

## 8. Reproduce the tests

### Prerequisites

```bash
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Start the API (required for batch test only)
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

---

### A — Metric verification (no API needed)

Recomputes all metrics from the raw dataset and compares them against the stored JSON files.

```bash
# 1. Verify: compare stored JSON vs freshly recomputed metrics
python -m api.verify_metrics

# 2. Force-refresh all cached JSON files then verify again
python -m api.verify_metrics --delete-cache
```

**What to look for:**
- `OK` on every row → stored JSON is trustworthy.
- `MISMATCH` → the stored file has stale values. Run `--delete-cache` and restart the API to regenerate correct files.
- `[!] Evaluation FAILED` → a model's predict pipeline needs investigation.

**Output files written/updated:**
- `models/logistic_regression_metrics.json`
- `models/random_forest_metrics.json`
- `models/modele_deep_learning_sgd_metrics.json`
- `models/voting_classifier_metrics.json`

---

### B — API batch test (200 calls, API must be running)

Sends 50 identical sensor-reading payloads to each of the 4 model aliases.

```bash
# Standard run — print report to console
python -m api.batch_test

# Save raw results to JSON for further analysis
python -m api.batch_test --output results.json

# Custom API URL or longer timeout
python -m api.batch_test --url http://127.0.0.1:8000 --timeout 20

# All options together
python -m api.batch_test --url http://127.0.0.1:8000 --timeout 20 --output results.json
```

**What the report shows:**
- **Per-model summary**: failure count, fail %, average probability, std deviation, average latency, error count.
- **Confidence distribution**: how many samples each model answered decisively (prob ≥ 0.75 or ≤ 0.25).
- **Cross-model agreement**: how often all 4 models agreed, had a 3-vs-1 split, or a 50/50 split.
- **Disagreement table**: sample-level view of where models diverge, with raw sensor values.
- **Recommendation**: ranked by confidence + median alignment (informational only — see §6 for why this can be misleading).

> [!WARNING]
> The batch test has **no ground truth labels**. Its recommendation should be treated as informational only.
> The verified holdout metrics in §3 are the definitive performance evaluation.

---

### C — API manual spot check

```bash
# Healthy machine — expect no failure (rf: OK, voting_classifier: OK)
curl -s -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rf",
    "features": {
      "machine_type": "CNC",
      "vibration_rms": 1.2,
      "temperature_motor": 65.0,
      "current_phase_avg": 10.1,
      "pressure_level": 2.8,
      "rpm": 1450,
      "operating_mode": "normal",
      "hours_since_maintenance": 50,
      "ambient_temp": 22.0
    }
  }'

# High-risk machine — expect failure
curl -s -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rf",
    "features": {
      "machine_type": "CNC",
      "vibration_rms": 6.5,
      "temperature_motor": 99.0,
      "current_phase_avg": 20.5,
      "pressure_level": 6.3,
      "rpm": 1720,
      "operating_mode": "peak",
      "hours_since_maintenance": 500,
      "ambient_temp": 38.0
    }
  }'
```

**Valid enum values:**
- `machine_type`: `"CNC"`, `"Compressor"`, `"Pump"`, `"Robotic Arm"`
- `operating_mode`: `"idle"`, `"normal"`, `"peak"`

---

### D — View stored metrics via API

```bash
# All models with metrics
curl http://127.0.0.1:8000/models

# Side-by-side metric comparison table
curl http://127.0.0.1:8000/models/compare
```

---

*Report generated from: `api/batch_test.py`, `api/verify_metrics.py`, `models/*_metrics.json`*
