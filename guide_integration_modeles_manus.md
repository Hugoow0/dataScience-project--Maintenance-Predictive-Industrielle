# Guide d'Intégration des Modèles de Maintenance Prédictive dans le Dashboard Streamlit

Ce document détaille l'utilité de chaque modèle de Machine Learning identifié dans votre projet et propose des stratégies pour les intégrer efficacement dans votre dashboard Streamlit, en s'appuyant sur l'architecture existante.

## 1. Utilité des Modèles de Machine Learning

Votre projet de maintenance prédictive utilise plusieurs modèles, chacun ayant un rôle spécifique dans l'anticipation des pannes industrielles. Voici un aperçu de leur fonction :

*   **`logistic_regression-model.pkl` (Régression Logistique)** :
    *   **Type :** Modèle de classification linéaire.
    *   **Utilité :** Souvent utilisé comme **modèle de base (baseline)** en raison de sa simplicité et de son interprétabilité. Il prédit la probabilité qu'une machine tombe en panne dans un futur proche (par exemple, 24 heures) en fonction des caractéristiques des capteurs. Il est utile pour établir une première référence de performance.

*   **`logistic_regression-preprocessor.pkl` (Préprocesseur)** :
    *   **Type :** `ColumnTransformer` de Scikit-learn.
    *   **Utilité :** Ce n'est pas un modèle de prédiction en soi, mais un composant essentiel du pipeline de Machine Learning. Il est responsable de la **transformation des données brutes** (nettoyage, encodage des variables catégorielles, normalisation des variables numériques) avant qu'elles ne soient passées aux modèles. Son utilisation garantit que les données d'entrée pour la prédiction sont dans le même format et la même échelle que celles utilisées lors de l'entraînement des modèles.

*   **`modele_deep_learning_sgd.pkl` (Modèle de Deep Learning)** :
    *   **Type :** Modèle `Sequential` de Keras (TensorFlow) entraîné avec un optimiseur SGD (Stochastic Gradient Descent).
    *   **Utilité :** Les modèles de Deep Learning peuvent capturer des relations complexes et non linéaires dans les données, potentiellement offrant une meilleure précision que les modèles classiques pour des jeux de données volumineux ou complexes. Il est utilisé pour prédire la probabilité de panne, potentiellement avec une performance supérieure si les données le justifient.

*   **`modele_ensemble_maintenance.pkl` (Modèle d'Ensemble)** :
    *   **Type :** `VotingClassifier` de Scikit-learn (un classifieur d'ensemble).
    *   **Utilité :** Un modèle d'ensemble combine les prédictions de plusieurs modèles individuels (par exemple, Régression Logistique, Random Forest, XGBoost, LightGBM) pour améliorer la robustesse et la précision globale. En agrégeant les forces de différents algorithmes, il réduit le risque de surapprentissage et peut offrir une meilleure généralisation. Il est souvent le modèle le plus performant en production.

*   **`random_forest_model.pkl` (Forêt Aléatoire)** :
    *   **Type :** `RandomForestClassifier` de Scikit-learn.
    *   **Utilité :** La Forêt Aléatoire est un algorithme d'apprentissage ensembliste basé sur des arbres de décision. Il est très efficace pour la classification, robuste au surapprentissage et capable de gérer un grand nombre de caractéristiques. Il est utilisé pour prédire la probabilité de panne et est souvent un excellent choix pour sa performance et sa capacité à gérer des données hétérogènes.

## 2. Stratégies d'Intégration dans le Dashboard Streamlit

Votre dashboard Streamlit (`app.py`) utilise déjà une approche modulaire et la mise en cache des ressources, ce qui est excellent.

### Utilisation d'une API FastAPI pour l'Inférence (Recommandé pour la Production)

Votre `onglet/simulation.py` actuel utilise déjà une API (`http://localhost:8000/predict`). C'est une excellente approche pour la production, car elle sépare clairement le frontend (Streamlit) du backend (API d'inférence).

**Avantages :**
*   **Scalabilité :** L'API peut être déployée indépendamment et mise à l'échelle pour gérer un grand nombre de requêtes.
*   **Découplage :** Le dashboard n'a pas besoin de charger les modèles ou de gérer les dépendances ML.
*   **Flexibilité :** L'API peut être consommée par d'autres applications, pas seulement Streamlit.
*   **Sécurité :** Les modèles et la logique d'inférence sont encapsulés côté serveur.

**Inconvénients :**
*   Nécessite de maintenir une application backend séparée (FastAPI).
*   Ajoute une couche de complexité au déploiement.

**Étapes d'intégration :**

1.  **Créer une application FastAPI** (par exemple, `api.py` dans le dossier `api/` de votre projet) qui charge les modèles et le préprocesseur au démarrage et expose un endpoint `/predict`.

    ```python
    # api/api.py (Exemple de structure FastAPI)
    from fastapi import FastAPI
    from pydantic import BaseModel
    import joblib
    import pandas as pd
    import os
    import tensorflow as tf # Pour les modèles Keras

    app = FastAPI()

    # Chemin vers le dossier des modèles (ajuster si nécessaire)
    MODELS_DIR = "/home/ubuntu/projects/stp-data-cbb04cc1/"

    # Charger les modèles et le préprocesseur au démarrage de l'API
    preprocessor = joblib.load(os.path.join(MODELS_DIR, "logistic_regression-preprocessor.pkl"))
    model_lr = joblib.load(os.path.join(MODELS_DIR, "logistic_regression-model.pkl"))
    model_rf = joblib.load(os.path.join(MODELS_DIR, "random_forest_model.pkl"))
    model_dl = tf.keras.models.load_model(os.path.join(MODELS_DIR, "modele_deep_learning_sgd.pkl")) # Keras models are best loaded this way
    model_ensemble = joblib.load(os.path.join(MODELS_DIR, "modele_ensemble_maintenance.pkl"))

    # Définir le schéma des données d'entrée pour l'API
    class MachineFeatures(BaseModel):
        machine_type: str
        vibration_rms: float
        temperature_motor: float
        current_phase_avg: float
        pressure_level: float
        rpm: int
        operating_mode: str
        hours_since_maintenance: float
        ambient_temp: float

    @app.post("/predict")
    async def predict(features: MachineFeatures):
        input_df = pd.DataFrame([features.dict()])
        processed_input = preprocessor.transform(input_df)

        predictions = {}
        # Prédiction avec chaque modèle
        models_to_predict = {
            "logistic_regression": model_lr,
            "random_forest": model_rf,
            "deep_learning": model_dl,
            "ensemble_model": model_ensemble
        }

        for name, model in models_to_predict.items():
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(processed_input)[:, 1][0]
            elif hasattr(model, 'predict'):
                probability = model.predict(processed_input)[0][0]
            else:
                probability = 0.0
            predictions[name] = float(probability)

        # Vous pouvez choisir de retourner la prédiction du modèle d'ensemble par défaut
        # ou toutes les prédictions pour comparaison.
        ensemble_prob = predictions.get("ensemble_model", 0.0)
        risk_level = "FAIBLE"
        if ensemble_prob > 0.7:
            risk_level = "ÉLEVÉ"
        elif ensemble_prob > 0.4:
            risk_level = "MOYEN"

        return {"risk_level": risk_level, "probability": ensemble_prob, "all_probabilities": predictions, "model_version": "1.0"}

    ```

2.  **Lancer l'API FastAPI** (par exemple, avec `uvicorn api.api:app --host 0.0.0.0 --port 8000`).

3.  **Maintenir `onglet/simulation.py` tel quel**, en s'assurant que `API_URL` pointe vers l'adresse correcte de votre API FastAPI.

    ```python
    # onglet/simulation.py (extrait)
    # ...
    API_URL = "http://localhost:8000" # Assurez-vous que cette URL est correcte
    # ...
    # Le reste du code de simulation.py peut rester inchangé car il appelle déjà l'API.
    ```

## 3. Considérations Importantes

*   **Versions des Bibliothèques :** Les avertissements `InconsistentVersionWarning` lors du chargement des modèles indiquent que les modèles ont été sauvegardés avec une version de Scikit-learn différente de celle installée dans l'environnement actuel. Il est crucial d'utiliser les **mêmes versions de bibliothèques** (Scikit-learn, Keras/TensorFlow, XGBoost, LightGBM, Joblib, Pandas, NumPy) pour l'entraînement et le chargement des modèles afin d'éviter des erreurs ou des comportements inattendus. Idéalement, spécifiez ces versions dans votre `requirements.txt`.
*   **Chargement des Modèles Keras :** Pour les modèles Keras (`modele_deep_learning_sgd.pkl`), il est généralement plus fiable d'utiliser `tf.keras.models.load_model()` si le modèle a été sauvegardé au format HDF5 ou SavedModel, plutôt que `joblib.load()`. Si `joblib` a été utilisé pour sérialiser un modèle Keras, cela peut fonctionner, mais `tf.keras.models.load_model` est la méthode recommandée par TensorFlow.
*   **Gestion des Erreurs :** Implémentez une gestion robuste des erreurs pour le chargement des modèles et les prédictions, comme vous l'avez déjà fait avec les blocs `try-except`.
*   **Dépendances :** Assurez-vous que toutes les bibliothèques nécessaires (scikit-learn, tensorflow, xgboost, lightgbm, joblib, pandas, numpy) sont installées dans l'environnement où le dashboard ou l'API s'exécute.

En suivant ces directives, vous pourrez intégrer vos modèles de maintenance prédictive dans votre dashboard Streamlit de manière structurée et performante.
