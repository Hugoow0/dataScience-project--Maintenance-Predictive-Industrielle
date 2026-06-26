from fastapi import FastAPI
from .schemas import SensorInput, PredictionOutput

app = FastAPI(
    title="Predictive Maintenance API",
    description="API pour la prédiction de pannes industrielles sous 24h",
    version="1.0.0"
)

@app.post("/predict", response_model=PredictionOutput)
async def predict(data: SensorInput):
    # Ici, plus tard, on fera : model.predict(data) || Pour l'instant, on renvoie une réponse fictive
    mock_prob = 0.15 
    
    return {
        "prediction": 0,
        "probability": mock_prob
    }

@app.get("/health", tags=["System"])
async def health_check():
    # Plus tard, nous ajouterons ici une vérification du chargement du modèle.
    return {
        "status": "online",
        "model_loaded": False,  # Sera mis à True quand on chargera le .pkl
        "version": "1.0.0"
    }

@app.get("/", tags=["System"])
async def root():
    return {"message": "Bienvenue sur l'API de Maintenance Prédictive. Accédez à /docs pour la documentation."}
