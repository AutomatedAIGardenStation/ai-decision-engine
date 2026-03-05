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
                "pollination_window": {
                    "start_hour": 8,
                    "end_hour": 12,
                    "interval_days": 2
                }
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

    metadata = response_json["metadata"]
    assert metadata["engine_version"] == "0.1.0"
    assert metadata["decision_time_ms"] > 0

    # Assert that Climate, Lighting, Nutrient actions are present (based on defaults)
    actions = response_json["actions"]

    action_names = [a["action"] for a in actions]

    # 24.5 is in range [18.0, 30.0], proportional cooling: pct = ((24.5 - 18.0) / 12.0) * 80 = 43.33 -> 43
    assert "fan_set" in action_names
    for a in actions:
        if a["action"] == "fan_set":
            assert a["parameters"]["pct"] == 43

    # No light schedule provided -> outside schedule -> pct 0
    assert "light_set" in action_names

    # EC target is 1.6. EC = 1.5. Target * 0.9 = 1.44. Target * 1.15 = 1.84. 1.5 is in range.
    # pH min is 5.5, max is 6.5. pH = 6.0. In range.
    # So no Nutrient actions are generated.

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
