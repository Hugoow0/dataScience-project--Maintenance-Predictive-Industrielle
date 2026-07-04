import pandas as pd
from fastapi import FastAPI, HTTPException
from typing import List
import os
from pathlib import Path
import joblib
from .schemas import PredictionOutput, ModelName

app = FastAPI(title="Predictive Maintenance API", version="1.6.0")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "maintenance_cleaned.csv"

MODEL_PATHS = {
    ModelName.model1: BASE_DIR / "models" / "logistic_regression-model.pkl",
    ModelName.model2: BASE_DIR / "models" / "random_forest_model.pkl",
    ModelName.model3: BASE_DIR / "models" / "model3.pkl"
}

PREPROCESSOR_PATHS = {
    ModelName.model1: BASE_DIR / "models" / "logistic_regression-preprocessor.pkl"
}

def load_artifacts(paths):
    loaded = {}
    errors = {}
    for name, path in paths.items():
        if os.path.exists(path):
            try:
                loaded[name] = joblib.load(path)
                print(f"Succès : {name} chargé depuis {path}")
            except Exception as e:
                print(f"Erreur chargement {name}: {e}")
                loaded[name] = None
                errors[name] = str(e)
        else:
            loaded[name] = None
            errors[name] = f"Fichier introuvable : {path}"
    return loaded, errors

models, model_load_errors = load_artifacts(MODEL_PATHS)
preprocessors, preprocessor_load_errors = load_artifacts(PREPROCESSOR_PATHS)

@app.post("/predict", response_model=List[PredictionOutput], tags=["ML"])
async def predict(model_name: ModelName = ModelName.model1):
    try:
        if not os.path.exists(DATA_PATH):
            raise HTTPException(status_code=404, detail=f"Fichier de données introuvable : {DATA_PATH}")

        df = pd.read_csv(DATA_PATH)
        
        target_model = models.get(model_name)
        
        if target_model is None:
            detail = model_load_errors.get(model_name, "Modèle non chargé")
            raise HTTPException(status_code=503, detail=f"Modèle indisponible ({model_name}) : {detail}")

        features = [
            "machine_type", "vibration_rms", "temperature_motor",
            "current_phase_avg", "pressure_level", "rpm",
            "operating_mode", "hours_since_maintenance", "ambient_temp"
        ]

        X = df[features]
        preprocessor = preprocessors.get(model_name)
        if preprocessor is not None:
            X = preprocessor.transform(X)

        probabilities = target_model.predict_proba(X)[:, 1]
        predictions = target_model.predict(X)

        results = []
        for prob, pred in zip(probabilities, predictions):
            results.append({
                "probability": round(float(prob), 3),
                "prediction": int(pred)
            })

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction : {str(e)}")

@app.get("/model-info")
async def get_model_info(model_name: ModelName = ModelName.model1):
    is_loaded = models.get(model_name) is not None
    model_error = model_load_errors.get(model_name)
    preproc_error = preprocessor_load_errors.get(model_name)
    details = []
    if model_error:
        details.append(f"model: {model_error}")
    if preproc_error:
        details.append(f"preprocessor: {preproc_error}")
    return {
        "model": model_name,
        "status": "Opérationnel (Réel)" if is_loaded else "Non chargé",
        "file_path": str(MODEL_PATHS.get(model_name)),
        "details": " | ".join(details) if details else None
    }

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "data_file_exists": os.path.exists(DATA_PATH),
        "models_loaded": {name: (m is not None) for name, m in models.items()},
        "model_load_errors": model_load_errors,
        "preprocessors_loaded": {name: (p is not None) for name, p in preprocessors.items()}
    }
