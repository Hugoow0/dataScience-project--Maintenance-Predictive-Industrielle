# Projet de Maintenance Prédictive Industrielle

Ce projet vise à développer une solution de maintenance prédictive pour des machines industrielles, en utilisant des modèles de machine learning pour anticiper les pannes et optimiser les opérations. Il comprend une API backend pour les prédictions, un dashboard frontend pour la visualisation et l'interaction, ainsi que des outils pour l'analyse et l'entraînement des modèles.

## Arborescence du Projet

```
.
├── README.md
├── SETUP_GUIDE.MD
├── api/
│   ├── __init__.py
│   ├── batch_test.py
│   ├── main.py
│   ├── schemas.py
│   └── tests/
│       └── test_api.py
├── dashboard/
│   ├── README.md
│   ├── components.json
│   ├── eslint.config.js
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── public/
│   │   └── vite.svg
│   ├── src/
│   │   ├── App.tsx
│   │   ├── assets/
│   │   ├── components/
│   │   ├── index.css
│   │   ├── lib/
│   │   ├── main.tsx
│   │   ├── pages/
│   │   └── types/
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── data/
│   ├── processed/
│   │   └── maintenance_cleaned.csv
│   └── raw/
│       └── industrial_machine_maintenance.csv
├── models/
│   ├── logistic_regression-model.pkl
│   ├── logistic_regression-preprocessor.pkl
│   ├── logistic_regression_metrics.json
│   ├── modele_deep_learning_sgd.pkl
│   ├── modele_deep_learning_sgd_metrics.json
│   ├── random_forest_metrics.json
│   ├── random_forest_model.pkl
│   ├── voting_classifier_metrics.json
│   └── voting_classifier_model.pkl
├── notebook/
│   ├── data_cleaning.ipynb
│   ├── logistic_regression-Maintenance_Predictive_Industrielle.ipynb
│   ├── random_forest.ipynb
│   └── training_XG_Boost_and_DeepLearning.ipynb
├── requirements.txt
└── results.json
```

## Description des Dossiers et Fichiers Clés

*   **`api/`**: Contient le code de l'API FastAPI. C'est le cœur du backend, exposant des points de terminaison pour la prédiction de maintenance.
    *   `main.py`: Le fichier principal de l'application FastAPI, gérant les routes, la logique métier et l'intégration des modèles.
    *   `schemas.py`: Définit les schémas de données (Pydantic) pour les requêtes et réponses de l'API, assurant la validation des données.
    *   `tests/`: Contient les tests unitaires pour l'API.
*   **`dashboard/`**: L'application frontend développée avec React et Vite. Elle fournit une interface utilisateur pour visualiser les données, les prédictions et interagir avec l'API.
    *   `package.json`: Définit les dépendances et les scripts de construction pour l'application frontend.
    *   `src/`: Contient le code source de l'application React, incluant les composants, les pages et les assets.
*   **`data/`**: Stocke les jeux de données utilisés pour l'entraînement et l'évaluation des modèles.
    *   `raw/`: Données brutes, par exemple `industrial_machine_maintenance.csv`.
    *   `processed/`: Données nettoyées et prétraitées, par exemple `maintenance_cleaned.csv`.
*   **`models/`**: Répertoire pour les modèles de machine learning entraînés et les artefacts associés.
    *   Contient des fichiers `.pkl` pour les modèles sérialisés (ex: `logistic_regression-model.pkl`, `random_forest_model.pkl`, `modele_deep_learning_sgd.pkl`) et des fichiers `.json` pour leurs métriques (ex: `logistic_regression_metrics.json`).
*   **`notebook/`**: Dossier contenant les notebooks Jupyter utilisés pour l'exploration des données, le nettoyage, l'entraînement et l'évaluation des différents modèles de machine learning.
*  **`results.json`**: Fichier JSON contenant les résultats des évaluations des modèles, incluant les métriques de performance pour chaque modèle testé.
*   **`requirements.txt`**: Liste des dépendances Python nécessaires pour le backend et les scripts d'analyse.
*   **`SETUP_GUIDE.MD`**: Guide détaillé pour la mise en place et le lancement du projet.

## Comment Lancer le Dashboard

Pour lancer le dashboard, vous devez d'abord démarrer l'API backend, puis l'application frontend. Assurez-vous d'avoir **Python 3.10+**, **Node.js 18+** et **npm 9+** installés sur votre système.

### 1. Démarrer le Backend (API FastAPI)

Toutes les commandes suivantes doivent être exécutées depuis la **racine du projet** (`repo_maintenance/`).

1.  **Créer un environnement virtuel**:
    ```bash
    python -m venv .venv
    ```

2.  **Activer l'environnement virtuel**:
    *   **macOS / Linux**:
        ```bash
        source .venv/bin/activate
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
    *   **Windows (CMD)**:
        ```cmd
        .\.venv\Scripts\activate.bat
        ```
    > Votre invite de commande devrait maintenant afficher `(.venv)` pour confirmer que l'environnement est actif.

3.  **Installer les dépendances Python**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Démarrer l'API**:
    ```bash
    uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
    ```
    L'API sera disponible à l'adresse : [http://127.0.0.1:8000](http://127.0.0.1:8000).
    La documentation interactive (Swagger UI) sera accessible à : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Démarrer le Frontend (Dashboard React / Vite)

Toutes les commandes suivantes doivent être exécutées depuis le répertoire **`dashboard/`**.

1.  **Naviguer vers le répertoire du dashboard**:
    ```bash
    cd dashboard
    ```

2.  **Installer les modules Node.js**:
    ```bash
    npm install
    ```

3.  **Démarrer le serveur de développement**:
    ```bash
    npm run dev
    ```
    Le dashboard sera disponible à l'adresse : [http://localhost:5173](http://localhost:5173).

    > **Important**: Assurez-vous que l'API backend est en cours d'exécution avant de lancer le dashboard, car le dashboard l'appelle au démarrage.

---

### Images

![dashboard](https://github.com/Hugoow0/dataScience-project--Maintenance-Predictive-Industrielle/raw/dev/images/dashboard.png)

![predict](https://github.com/Hugoow0/dataScience-project--Maintenance-Predictive-Industrielle/raw/dev/images/predict.png)

