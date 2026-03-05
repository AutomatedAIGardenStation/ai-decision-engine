from datetime import datetime, timedelta, timezone
import pytest
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action
from src.evaluators.watering import WateringEvaluator

def create_base_snapshot(
    maintenance_mode: bool = False,
    zone_count: int = 1,
    soil_moisture: list[float] = [50.0],
    moisture_target: float = 50.0,
    last_watering_time_diff: timedelta = None
) -> dict:

    timestamp = datetime.now(timezone.utc)

    last_watering = {}
    if last_watering_time_diff is not None:
        last_watering = {0: timestamp - last_watering_time_diff}

    plant_profiles = []
    for i in range(zone_count):
        plant_profiles.append({
            "id": i,
            "name": f"Plant {i}",
            "species": "Test Species",
            "moisture_target": moisture_target,
            "ec_target": 1.6,
            "ph_min": 5.5,
            "ph_max": 6.5,
            "pollination_window": {
                "start_hour": 8,
                "end_hour": 12,
                "interval_days": 2
            }
        })

    return {
        "sensor_readings": {
            "temp": 24.5,
            "humidity": 60.0,
            "ph": 6.0,
            "ec": 1.5,
            "soil_moisture": soil_moisture,
            "tank_level_pct": 85.0
        },
        "ml_results": [],
        "plant_profiles": plant_profiles,
        "queue_state": {
            "harvest_pending_ids": [],
            "active_harvest_id": None
        },
        "system_config": {
            "maintenance_mode": maintenance_mode,
            "zone_count": zone_count,
            "max_pump_time_s": 120
        },
        "history": {
            "last_watering": last_watering,
            "last_pollination": None
        },
        "timestamp": timestamp
    }

def test_maintenance_mode():
    data = create_base_snapshot(maintenance_mode=True, soil_moisture=[10.0], moisture_target=50.0)
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_below_threshold_water():
    # target 50, 0.85 * 50 = 42.5. Moisture is 40.0. Deficit = 10.0.
    data = create_base_snapshot(soil_moisture=[40.0], moisture_target=50.0)
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "water"
    assert actions[0].parameters["zone"] == 0
    assert actions[0].parameters["duration_s"] == 10

def test_above_threshold_stop():
    # target 50, 1.1 * 50 = 55.0. Moisture is 60.0.
    data = create_base_snapshot(soil_moisture=[60.0], moisture_target=50.0)
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "stop_watering"
    assert actions[0].parameters["zone"] == 0

def test_cooldown_active_no_action():
    # target 50, moisture 40 (< 42.5), but watered 15 mins ago
    data = create_base_snapshot(soil_moisture=[40.0], moisture_target=50.0, last_watering_time_diff=timedelta(minutes=15))
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_cooldown_active_critical_alert():
    # target 50, moisture 5 (< 10), watered 15 mins ago
    data = create_base_snapshot(soil_moisture=[5.0], moisture_target=50.0, last_watering_time_diff=timedelta(minutes=15))
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "alert"
    assert actions[0].reason == "Critical moisture — watering blocked by cooldown"
    assert actions[0].parameters["zone"] == 0

def test_multiple_zones():
    data = create_base_snapshot(zone_count=2, soil_moisture=[40.0, 60.0], moisture_target=50.0)
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 2
    assert actions[0].action == "water"
    assert actions[0].parameters["zone"] == 0
    assert actions[1].action == "stop_watering"
    assert actions[1].parameters["zone"] == 1

def test_on_target_no_action():
    # target 50, moisture 50
    data = create_base_snapshot(soil_moisture=[50.0], moisture_target=50.0)
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_duration_capped_at_60s():
    # target 100, moisture 20. deficit = 80.
    data = create_base_snapshot(soil_moisture=[20.0], moisture_target=100.0)
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "water"
    assert actions[0].parameters["duration_s"] == 60

def test_missing_last_watering_time():
    # target 50, moisture 40. Last watering time not present for zone 0.
    data = create_base_snapshot(soil_moisture=[40.0], moisture_target=50.0)
    # create_base_snapshot defaults to None which translates to missing or not having it in dict if omitted
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "water"
    assert actions[0].parameters["duration_s"] == 10

def test_out_of_bounds_handling():
    data = create_base_snapshot(zone_count=2, soil_moisture=[40.0], moisture_target=50.0) # Only 1 moisture reading
    snapshot = StateSnapshot(**data)
    actions = WateringEvaluator.evaluate(snapshot)
    assert len(actions) == 1 # Only zone 0 evaluated, zone 1 skipped
    assert actions[0].action == "water"
    assert actions[0].parameters["zone"] == 0
