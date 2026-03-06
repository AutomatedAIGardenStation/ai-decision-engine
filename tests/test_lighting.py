from datetime import datetime, timezone
from typing import List
from src.schemas.state_snapshot import StateSnapshot
from src.evaluators.lighting import LightingEvaluator

def create_snapshot(hour: int, schedule: List[dict], maintenance_mode: bool = False, zone_count: int = 2) -> StateSnapshot:
    dt = datetime(2023, 10, 10, hour, 30, 0, tzinfo=timezone.utc)
    return StateSnapshot(
        sensor_readings={
            "temp": 25.0,
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
            "zone_count": zone_count,
            "max_pump_time_s": 60,
            "temp_max": 30.0,
            "temp_min": 18.0,
            "light_schedule": schedule
        },
        history={
            "last_watering": {},
            "last_pollination": None
        },
        timestamp=dt
    )

def test_maintenance_mode():
    snapshot = create_snapshot(hour=12, schedule=[{"start_hour": 8, "end_hour": 20, "intensity_pct": 100}], maintenance_mode=True)
    actions = LightingEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_within_schedule():
    schedule = [{"start_hour": 8, "end_hour": 20, "intensity_pct": 80}]
    # Hour 14 is between 8 and 20
    snapshot = create_snapshot(hour=14, schedule=schedule, zone_count=3)
    actions = LightingEvaluator.evaluate(snapshot)

    assert len(actions) == 3
    for i, action in enumerate(actions):
        assert action.action == "LIGHT_SET"
        assert action.parameters["ch"] == i
        assert action.parameters["pct"] == 80
        assert action.reason == "scheduled lighting"
        assert action.priority == "low"

def test_outside_schedule():
    schedule = [{"start_hour": 8, "end_hour": 20, "intensity_pct": 80}]
    # Hour 22 is outside 8 to 20
    snapshot = create_snapshot(hour=22, schedule=schedule, zone_count=3)
    actions = LightingEvaluator.evaluate(snapshot)

    assert len(actions) == 3
    for i, action in enumerate(actions):
        assert action.action == "LIGHT_SET"
        assert action.parameters["ch"] == i
        assert action.parameters["pct"] == 0
        assert action.reason == "outside light schedule"
        assert action.priority == "low"

def test_empty_schedule():
    schedule = []
    snapshot = create_snapshot(hour=12, schedule=schedule, zone_count=2)
    actions = LightingEvaluator.evaluate(snapshot)

    assert len(actions) == 2
    for i, action in enumerate(actions):
        assert action.action == "LIGHT_SET"
        assert action.parameters["pct"] == 0
        assert action.parameters["ch"] == i

def test_schedule_edge_cases():
    schedule = [{"start_hour": 8, "end_hour": 20, "intensity_pct": 100}]

    # Exactly on start_hour should be active
    snapshot = create_snapshot(hour=8, schedule=schedule, zone_count=1)
    actions = LightingEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "LIGHT_SET"
    assert actions[0].parameters["pct"] == 100

    # Exactly on end_hour should be inactive
    snapshot = create_snapshot(hour=20, schedule=schedule, zone_count=1)
    actions = LightingEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "LIGHT_SET"
    assert actions[0].parameters["pct"] == 0
