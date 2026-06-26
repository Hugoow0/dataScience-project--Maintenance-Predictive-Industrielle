import pandas as pd
from fastapi import FastAPI, HTTPException
from typing import List
import os
import joblib
from .schemas import PredictionOutput, ModelName

app = FastAPI(title="Predictive Maintenance API", version="1.6.0")

DATA_PATH = "data/processed/maintenance_cleaned.csv"

MODEL_PATHS = {
    ModelName.model1: "models/model1.pkl",
    ModelName.model2: "models/random_forest_model.pkl",
    ModelName.model3: "models/model3.pkl"
}

def load_models():
    loaded = {}
    for name, path in MODEL_PATHS.items():
        if os.path.exists(path):
            try:
                loaded[name] = joblib.load(path)
                print(f"Succès : {name} chargé depuis {path}")
            except Exception as e:
                print(f"Erreur chargement {name}: {e}")
                loaded[name] = None
        else:
            loaded[name] = None
    return loaded

models = load_models()

@app.post("/predict", response_model=List[PredictionOutput], tags=["ML"])
async def predict(model_name: ModelName = ModelName.model2):
    try:
        if not os.path.exists(DATA_PATH):
            raise HTTPException(status_code=404, detail=f"Fichier de données introuvable : {DATA_PATH}")

        df = pd.read_csv(DATA_PATH)
        
        target_model = models.get(model_name)
        
        results = []

        if target_model is not None:
            features = [
                "machine_type", "vibration_rms", "temperature_motor", 
                "current_phase_avg", "pressure_level", "rpm", 
                "operating_mode", "hours_since_maintenance", "ambient_temp"
            ]
            
            X = df[features]
            
            probabilities = target_model.predict_proba(X)[:, 1]
            predictions = target_model.predict(X)

            for prob, pred in zip(probabilities, predictions):
                results.append({
                    "probability": round(float(prob), 3),
                    "prediction": int(pred)
                })
            
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction : {str(e)}")

@app.get("/model-info")
async def get_model_info(model_name: ModelName = ModelName.model2):
    is_loaded = models.get(model_name) is not None
    return {
        "model": model_name,
        "status": "Opérationnel (Réel)" if is_loaded else "Non chargé",
        "file_path": MODEL_PATHS.get(model_name)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "data_file_exists": os.path.exists(DATA_PATH),
        "models_loaded": {name: (m is not None) for name, m in models.items()}
    }
