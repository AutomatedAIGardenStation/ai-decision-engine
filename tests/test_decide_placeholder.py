from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_decide_placeholder():
    response = client.post("/decide", json={}) # Empty json payload for now
    assert response.status_code == 200
    assert response.json() == {
        "actions": [],
        "metadata": {
            "engine_version": "0.1.0",
            "decision_time_ms": 0
        }
    }
