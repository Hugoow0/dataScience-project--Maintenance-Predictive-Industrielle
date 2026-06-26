import pandas as pd
from typing import List
from enum import Enum
from fastapi import FastAPI, HTTPException
from .schemas import SensorInput, PredictionOutput
import joblib
import os

app = FastAPI(
    title="Predictive Maintenance API",
    description="API pour la prédiction de pannes industrielles sous 24h",
    version="1.0.0"
)

class ModelName(str, Enum):
    model1 = "model1"
    model2 = "model2"
    model3 = "model3"

MODEL_PATHS = {
    ModelName.model1: "models/model1.pkl",
    ModelName.model2: "models/model2.pkl",
    ModelName.model3: "models/model3.pkl"
}

def load_models():
    loaded = {}
    for name, path in MODEL_PATHS.items():
        if os.path.exists(path):
            try:
                loaded[name] = joblib.load(path)
            except:
                loaded[name] = None
        else:
            loaded[name] = None
    return loaded

models = load_models()

@app.get("/model-info", tags=["Data"])
async def get_model_info(model_name: ModelName = ModelName.model1):
    # Pour l'instant, nous renvoyons des informations fictives sur le modèle. Plus tard, nous chargerons un modèle réel et fournirons ses détails.
    info = {
        ModelName.model1: {"name": "Logistic Regression", "f1": 0.78},
        ModelName.model2: {"name": "Random Forest", "f1": 0.85},
        ModelName.model3: {"name": "XGBoost", "f1": 0.89},
    }

    selected = info.get(model_name)
    return {
        "selected_model": model_name,
        "details": selected,
    }


@app.post("/predict", response_model=List[PredictionOutput], tags=["ML"])
async def predict(model_name: ModelName = ModelName.model1):
    file_path = "data/raw/industrial_machine_maintenance.csv"

    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Fichier non trouvé : {file_path}")

        df = pd.read_csv(file_path)
        
        target_model = models.get(model_name)
        
        results = []

        for index, row in df.iterrows():
            # Pour l'instant, nous renvoyons des informations fictives, on mettra la vraie logique plus tard
            rpm_value = row.get('rpm', 0)
            prob = (rpm_value % 100) / 100.0
            
            results.append({
                "probability": round(prob, 3),
                "prediction": 1 if prob > 0.3 else 0
            })
            
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture ou prédiction : {str(e)}")

@app.get("/health", tags=["System"])
async def health_check():
    # Plus tard, nous ajouterons ici une vérification du chargement du modèle.
    status_models = {name: (os.path.exists(path)) for name, path in MODEL_PATHS.items()}
    return {
        "status": "online",
        "models_available": status_models,
        "version": "1.1.0"
    }

@app.get("/", tags=["System"])
async def root():
    return {"message": "Bienvenue sur l'API de Maintenance Prédictive. Accédez à /docs pour la documentation."}
