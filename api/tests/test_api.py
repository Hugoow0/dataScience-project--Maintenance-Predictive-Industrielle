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