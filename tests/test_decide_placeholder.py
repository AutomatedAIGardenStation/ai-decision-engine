from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_decide_placeholder():
    valid_payload = {
        "sensor_readings": {
            "temp": 24.5,
            "humidity": 60.0,
            "ph": 6.0,
            "ec": 1.5,
            "soil_moisture": [30.5, 32.0],
            "tank_level_pct": 85.0
        },
        "ml_results": [
            {
                "plant_id": 1,
                "ripeness": "ripe",
                "disease": None,
                "confidence": 0.95
            }
        ],
        "plant_profiles": [
            {
                "id": 1,
                "name": "Tomato",
                "species": "Solanum lycopersicum",
                "moisture_target": 35.0,
                "ec_target": 1.6,
                "ph_min": 5.5,
                "ph_max": 6.5,
                "pollination_window": "08:00-12:00"
            }
        ],
        "queue_state": {
            "harvest_pending_ids": [1],
            "active_harvest_id": None
        },
        "system_config": {
            "maintenance_mode": False,
            "zone_count": 2,
            "max_pump_time_s": 120
        },
        "history": {
            "last_watering": {"1": "2023-10-26T10:00:00Z"},
            "last_pollination": "2023-10-25T14:00:00Z"
        },
        "timestamp": "2023-10-26T12:00:00Z"
    }

    response = client.post("/decide", json=valid_payload)
    assert response.status_code == 200

    response_json = response.json()
    assert "metadata" in response_json
    assert response_json["metadata"] == {
        "engine_version": "0.1.0",
        "decision_time_ms": 0
    }

    # Assert that Climate and Lighting actions are present (based on defaults)
    actions = response_json["actions"]
    assert len(actions) == 2

    # 24.5 is in range [18.0, 30.0], proportional cooling: pct = ((24.5 - 18.0) / 12.0) * 80 = 43.33 -> 43
    assert actions[0] == {
        "action": "fan_set",
        "parameters": {"pct": 43},
        "priority": "medium",
        "reason": "proportional cooling"
    }

    # No light schedule provided -> outside schedule -> pct 0
    assert actions[1] == {
        "action": "light_set",
        "parameters": {"pct": 0},
        "priority": "low",
        "reason": "outside light schedule"
    }

def test_decide_missing_sensor_readings():
    invalid_payload = {
        # "sensor_readings" missing
        "ml_results": [],
        "plant_profiles": [],
        "queue_state": {
            "harvest_pending_ids": [],
            "active_harvest_id": None
        },
        "system_config": {
            "maintenance_mode": False,
            "zone_count": 2,
            "max_pump_time_s": 120
        },
        "history": {
            "last_watering": {},
            "last_pollination": None
        },
        "timestamp": "2023-10-26T12:00:00Z"
    }

    response = client.post("/decide", json=invalid_payload)
    assert response.status_code == 422
