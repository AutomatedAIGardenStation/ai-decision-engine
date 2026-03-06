from datetime import datetime, timezone
from src.schemas.state_snapshot import StateSnapshot
from src.evaluators.climate import ClimateEvaluator

def create_snapshot(temp: float, maintenance_mode: bool = False, temp_max: float = 30.0, temp_min: float = 18.0) -> StateSnapshot:
    return StateSnapshot(
        sensor_readings={
            "temp": temp,
            "humidity": 50.0,
            "ph": 6.0,
            "ec": 1.0,
            "soil_moisture": [50.0],
            "tank_level_pct": 100.0
        },
        ml_results=[],
        plant_profiles=[],
        queue_state={
            "harvest_pending_ids": [],
            "active_harvest_id": None
        },
        system_config={
            "maintenance_mode": maintenance_mode,
            "zone_count": 1,
            "max_pump_time_s": 60,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "light_schedule": []
        },
        history={
            "last_watering": {},
            "last_pollination": None
        },
        timestamp=datetime.now(timezone.utc)
    )

def test_maintenance_mode():
    snapshot = create_snapshot(temp=35.0, maintenance_mode=True)
    actions = ClimateEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_temp_above_max():
    snapshot = create_snapshot(temp=35.0)
    actions = ClimateEvaluator.evaluate(snapshot)

    assert len(actions) == 1
    action = actions[0]
    assert action.action == "FAN_SET"
    assert action.parameters["pct"] == 100
    assert action.reason == "temp above max"
    assert action.priority == "high"

def test_temp_below_min():
    snapshot = create_snapshot(temp=15.0)
    actions = ClimateEvaluator.evaluate(snapshot)

    assert len(actions) == 2

    fan_action = actions[0]
    assert fan_action.action == "FAN_SET"
    assert fan_action.parameters["pct"] == 0
    assert fan_action.reason == "temp below min"
    assert fan_action.priority == "high"

    alert_action = actions[1]
    assert alert_action.action == "alert"
    assert alert_action.reason == "heating not yet implemented"
    assert alert_action.priority == "high"

def test_proportional_cooling():
    # Test middle of range: 18 to 30, temp = 24 -> 50% of range -> 50% of 80 = 40
    snapshot = create_snapshot(temp=24.0)
    actions = ClimateEvaluator.evaluate(snapshot)

    assert len(actions) == 1
    action = actions[0]
    assert action.action == "FAN_SET"
    assert action.parameters["pct"] == 40
    assert action.reason == "proportional cooling"
    assert action.priority == "medium"

    # Test exact min bound: temp = 18 -> 0% of range -> 0
    snapshot = create_snapshot(temp=18.0)
    actions = ClimateEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].parameters["pct"] == 0

    # Test exact max bound: temp = 30 -> 100% of range -> 80
    snapshot = create_snapshot(temp=30.0)
    actions = ClimateEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].parameters["pct"] == 80
