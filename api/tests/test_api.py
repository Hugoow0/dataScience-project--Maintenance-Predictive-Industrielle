from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_reports_loaded_models():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert isinstance(payload["models_loaded"], list)
    assert payload["models_loaded"]
    assert "modele_deep_learning_sgd" in payload["models_loaded"]
    assert "voting_classifier" in payload["models_loaded"]


def test_model_info_includes_new_models():
    response = client.get("/model-info")
    assert response.status_code == 200
    payload = response.json()
    models = {item["model"]: item for item in payload["models"]}
    assert "modele_deep_learning_sgd" in models
    assert "voting_classifier" in models
    assert models["modele_deep_learning_sgd"]["task_type"] == "classification"
    assert models["voting_classifier"]["task_type"] == "classification"


def test_predict_valid_payload():
    response = client.post(
        "/predict",
        json={
            "model": "rf",
            "features": {
                "vibration_rms": 2.3,
                "temperature_motor": 75.1,
                "current_phase_avg": 12.4,
                "pressure_level": 3.1,
                "rpm": 1450,
                "operating_mode": "normal",
                "hours_since_maintenance": 120,
                "ambient_temp": 24.5,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "random_forest"
    assert "prediction" in payload
    assert "probability" in payload


def test_predict_new_models():
    payload = {
        "features": {
            "vibration_rms": 2.3,
            "temperature_motor": 75.1,
            "current_phase_avg": 12.4,
            "pressure_level": 3.1,
            "rpm": 1450,
            "operating_mode": "normal",
            "hours_since_maintenance": 120,
            "ambient_temp": 24.5,
        },
    }

    voting_classifier_response = client.post("/predict", json={**payload, "model": "voting_classifier"})
    assert voting_classifier_response.status_code == 200
    voting_classifier_payload = voting_classifier_response.json()
    assert voting_classifier_payload["model"] == "voting_classifier"
    assert voting_classifier_payload["task_type"] == "classification"

    dl_response = client.post("/predict", json={**payload, "model": "dl"})
    assert dl_response.status_code == 200
    dl_payload = dl_response.json()
    assert dl_payload["model"] == "modele_deep_learning_sgd"
    assert dl_payload["task_type"] == "classification"


def test_predict_invalid_model_name():
    response = client.post(
        "/predict",
        json={
            "model": "does_not_exist",
            "features": {
                "vibration_rms": 2.3,
                "temperature_motor": 75.1,
                "current_phase_avg": 12.4,
                "pressure_level": 3.1,
                "rpm": 1450,
                "operating_mode": "normal",
                "hours_since_maintenance": 120,
                "ambient_temp": 24.5,
            },
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "Request error"
    assert "available_models" in payload["detail"]


def test_predict_missing_field_returns_validation_error():
    response = client.post(
        "/predict",
        json={
            "model": "rf",
            "features": {
                "temperature_motor": 75.1,
                "current_phase_avg": 12.4,
                "pressure_level": 3.1,
                "rpm": 1450,
                "operating_mode": "normal",
                "hours_since_maintenance": 120,
                "ambient_temp": 24.5,
            },
        },
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"] == "Validation error"
    assert isinstance(payload["detail"], list)