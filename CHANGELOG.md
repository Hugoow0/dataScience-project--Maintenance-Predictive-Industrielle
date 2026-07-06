# Changelog — Maintenance Prédictive Industrielle

> **Date:** 2026-07-04
> **Scope:** FastAPI backend + React/Vite dashboard + model registry

---

## Summary

Full-stack wiring of the predictive-maintenance ML models into a production-ready API and a live dashboard. The two newly trained models (`voting_classifier` and `modele_deep_learning_sgd`) are now callable from the dashboard through the same dynamic endpoints that already served the logistic-regression and random-forest artifacts.

---

## 1. Backend — `api/`

### `api/main.py`
- Replaced the placeholder API with a **cached model-discovery registry**.
- Added endpoints:

  | Route | Method | Description |
  |---|---|---|
  | `/health` | GET | Liveness probe |
  | `/model-info` | GET | Lists all registered models and their metadata |
  | `/dataset/stats` | GET | Returns class balance, sensor statistics |
  | `/dataset/model-comparison` | GET | Returns cached per-model evaluation metrics |
  | `/predict` | POST | Runs inference with the selected model |

- Added **CORS** middleware and consistent JSON error handling.
- Introduced a **`ModelBundle`** abstraction so each model's preprocessing is encapsulated:
  - **Logistic Regression** — uses saved `logistic_regression-preprocessor.pkl` (two files treated as one logical model).
  - **Random Forest** — standard sklearn pipeline, no extra preprocessing.
  - **Ensemble** (`voting_classifier`) — label-encodes categorical columns (`machine_type`, `operating_mode`) before inference; **no scaling**.
  - **Deep Learning / SGD** (`modele_deep_learning_sgd`) — label-encodes categoricals **then** applies `StandardScaler` (fitted on an 80 % sample of the training data at API startup).
- Fixed a **double-encoding bug** where the ensemble path was running `LabelEncoder.transform` twice, causing integer labels to be treated as unseen categories.
- Added `resolve_bundle(alias)` helper and the `DEFAULT_MACHINE_TYPE` constant (`"CNC"` — the modal value in the dataset) for requests that omit `machine_type`.
- Aliases exposed: `rf`, `lr`, `ensemble`, `dl`.

### `api/schemas.py`
- Added Pydantic v2 models for:
  - `FeatureInput` — eight numeric fields + `operating_mode` enum + optional `machine_type`
  - `PredictRequest` / `PredictResponse`
  - `ModelMetadata`, `DatasetStats`, `ModelComparisonRow`, `ErrorResponse`

### `api/tests/test_api.py`
- Added `pytest` coverage:
  - `GET /health` — 200, `status: ok`
  - `GET /model-info` — lists all four models
  - `POST /predict` with `rf` — valid prediction shape
  - `POST /predict` with `ensemble` — valid prediction shape *(new)*
  - `POST /predict` with `dl` — valid prediction shape *(new)*
  - `POST /predict` with unknown model name — 404
  - `POST /predict` with missing required fields — 422
- **Result: 6 passed ✅**

---

## 2. Models & Metrics — `models/`

| File | Description |
|---|---|
| `logistic_regression_metrics.json` | Cached metrics from stratified holdout split |
| `random_forest_metrics.json` | Cached metrics from stratified holdout split |
| `voting_classifier_model.pkl` | Voting/stacking ensemble trained in notebook |
| `modele_deep_learning_sgd.pkl` | SGD-based neural-network surrogate trained in notebook |

Metrics for the ensemble and SGD models are computed at API startup from the holdout set and merged into the `/dataset/model-comparison` response dynamically.

---

## 3. Frontend — `dashboard/`

### Architecture
- **Vite + React + TypeScript** scaffold via shadcn/ui.
- Routing via `react-router-dom`.
- Form validation via `react-hook-form` + `zod` + `@hookform/resolvers`.
- Charts via `recharts` (wrapped by the shadcn `chart` primitive).

### Files added/modified

| File | What it does |
|---|---|
| `src/App.tsx` | Router shell, nav bar, live API status indicator |
| `src/main.tsx` | App bootstrap and theme-provider wiring |
| `src/index.css` | Base polish and intentional background |
| `src/lib/api.ts` | Typed fetch wrapper for the FastAPI backend |
| `src/types/api.ts` | TypeScript mirror of all backend API contracts |
| `src/pages/DashboardPage.tsx` | KPI overview, loading states, dashboard data fetch |
| `src/pages/PredictPage.tsx` | Live prediction route + data bootstrapping |
| `src/components/PredictionForm.tsx` | RHF/Zod prediction form and result panel |
| `src/components/KpiCard.tsx` | Reusable KPI card |
| `src/components/ModelSelector.tsx` | Model picker (populated from `/model-info`) |
| `src/components/charts/ClassBalanceChart.tsx` | Failure-balance bar chart |
| `src/components/charts/SensorDistributionChart.tsx` | Histogram charts for sensor distributions |
| `src/components/charts/ModelComparisonChart.tsx` | Grouped model-metrics bar chart |
| `src/components/charts/CorrelationHeatmap.tsx` | Correlation matrix view |
| `src/components/ui/*` | shadcn primitives: card, table, tabs, select, input, badge, skeleton, sonner, chart |

### Key design decisions
- The dashboard consumes **`/model-info`** dynamically, so all four models appear in the model selector and comparison views **without any frontend code changes** — new models added to the API are automatically surfaced.
- The prediction form omits `machine_type`; the API defaults it to `"CNC"` server-side.

### Dependencies added (`package.json`)
```
react-router-dom
react-hook-form
zod
@hookform/resolvers
recharts
```

---

## 4. Root — `requirements.txt`

Added backend packages:
```
fastapi
uvicorn[standard]
pydantic
scikit-learn
joblib
pandas
numpy
pytest
httpx
```

---

## 5. Debugging Timeline

| Step | Finding | Fix |
|---|---|---|
| Ensemble fails in API | Exception inside inference, not request validation | Isolated to `bundle.predict()` call |
| `LabelEncoder` gets `0` instead of string | `OperatingMode` enum serializes as integer in some paths | Confirmed `features.model_dump(mode='json')` was already correct |
| Double-encoding bug | Ensemble path encoded categoricals once in the frame builder **and again** inside the bundle transform | Removed the second `LabelEncoder.transform` loop |
| Deep-learning model needs scaling | SGD model was trained on standardized features | Added a `StandardScaler` step (fitted on 80 % sample at startup) only for the `dl` branch |

---

## 6. Verification

```bash
# Backend unit tests
python -m pytest api/tests/test_api.py -q
# 6 passed

# Frontend type check
cd dashboard && npm run typecheck

# Frontend build
cd dashboard && npm run build
```

---

## 7. Open Improvements (not yet done)

- [ ] Add a visual badge in the dashboard to distinguish `classification` vs `multi_class` vs `regression` model types.
- [ ] Serve model metrics for `ensemble` and `dl` from pre-computed JSON files (same pattern as `logistic_regression_metrics.json`) to avoid recomputation on cold start.
- [ ] Add `machine_type` as an optional field in the prediction form with a sensible default dropdown.
- [ ] Add end-to-end tests that spin up the actual Uvicorn server and hit it with `httpx.AsyncClient`.
