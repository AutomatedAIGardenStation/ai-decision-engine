import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import ActionList

def get_valid_state_snapshot_data():
    return {
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
            "active_harvest_id": None,
            "active_waterings": [0]
        },
        "system_config": {
            "maintenance_mode": False,
            "zone_count": 2,
            "max_pump_time_s": 120
        },
        "history": {
            "last_watering": {1: "2023-10-26T10:00:00Z"},
            "last_pollination": "2023-10-25T14:00:00Z"
        },
        "timestamp": "2023-10-26T12:00:00Z"
    }

def test_state_snapshot_valid():
    data = get_valid_state_snapshot_data()
    snapshot = StateSnapshot(**data)
    assert snapshot.sensor_readings.temp == 24.5
    assert snapshot.ml_results[0].plant_id == 1
    assert snapshot.timestamp.tzinfo is not None  # Verify timezone awareness

def test_state_snapshot_missing_sensor_readings():
    data = get_valid_state_snapshot_data()
    del data["sensor_readings"]

    with pytest.raises(ValidationError) as exc:
        StateSnapshot(**data)

    assert "sensor_readings" in str(exc.value)

def test_state_snapshot_extra_fields_ignored():
    data = get_valid_state_snapshot_data()
    data["extra_unknown_field"] = "should be ignored"

    snapshot = StateSnapshot(**data)
    assert not hasattr(snapshot, "extra_unknown_field")

def test_action_list_valid():
    data = {
        "actions": [
            {
                "action": "water",
                "parameters": {"zone": 1, "duration_s": 30},
                "reason": "Soil moisture below target",
                "priority": "high"
            }
        ],
        "metadata": {
            "decision_time_ms": 15,
            "engine_version": "1.0.0"
        }
    }
    action_list = ActionList(**data)
    assert len(action_list.actions) == 1
    assert action_list.actions[0].action == "water"
    assert action_list.actions[0].parameters["duration_s"] == 30
    assert action_list.metadata.decision_time_ms == 15
