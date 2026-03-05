from datetime import datetime, timedelta, timezone
from src.schemas.state_snapshot import StateSnapshot
from src.evaluators.pollination import PollinationEvaluator

def create_base_snapshot(
    maintenance_mode: bool = False,
    current_hour: int = 10,
    pollination_window: dict = None,
    last_pollination_time_diff: timedelta = None
) -> dict:
    # Build a timestamp with the specific hour
    now = datetime.now(timezone.utc)
    timestamp = now.replace(hour=current_hour, minute=0, second=0, microsecond=0)

    last_pollination = None
    if last_pollination_time_diff is not None:
        last_pollination = timestamp - last_pollination_time_diff

    return {
        "sensor_readings": {
            "temp": 24.5,
            "humidity": 60.0,
            "ph": 6.0,
            "ec": 1.5,
            "soil_moisture": [50.0],
            "tank_level_pct": 85.0
        },
        "ml_results": [],
        "plant_profiles": [
            {
                "id": 1,
                "name": "Tomato",
                "species": "Solanum lycopersicum",
                "moisture_target": 35.0,
                "ec_target": 1.6,
                "ph_min": 5.5,
                "ph_max": 6.5,
                "pollination_window": pollination_window
            }
        ],
        "queue_state": {
            "harvest_pending_ids": [],
            "active_harvest_id": None
        },
        "system_config": {
            "maintenance_mode": maintenance_mode,
            "zone_count": 1,
            "max_pump_time_s": 120
        },
        "history": {
            "last_watering": {},
            "last_pollination": last_pollination
        },
        "timestamp": timestamp
    }

def test_pollination_maintenance_mode():
    data = create_base_snapshot(
        maintenance_mode=True,
        pollination_window={"start_hour": 8, "end_hour": 12, "interval_days": 2}
    )
    snapshot = StateSnapshot(**data)
    actions = PollinationEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_pollination_no_window():
    data = create_base_snapshot(pollination_window=None)
    snapshot = StateSnapshot(**data)
    actions = PollinationEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_pollination_in_window_no_history():
    # current hour 10, window 8-12
    data = create_base_snapshot(
        current_hour=10,
        pollination_window={"start_hour": 8, "end_hour": 12, "interval_days": 2}
    )
    snapshot = StateSnapshot(**data)
    actions = PollinationEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "pollinate"
    assert actions[0].parameters["plant_id"] == 1

def test_pollination_out_of_window_early():
    # current hour 7, window 8-12
    data = create_base_snapshot(
        current_hour=7,
        pollination_window={"start_hour": 8, "end_hour": 12, "interval_days": 2}
    )
    snapshot = StateSnapshot(**data)
    actions = PollinationEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_pollination_out_of_window_late():
    # current hour 12, window 8-12 (exclusive end)
    data = create_base_snapshot(
        current_hour=12,
        pollination_window={"start_hour": 8, "end_hour": 12, "interval_days": 2}
    )
    snapshot = StateSnapshot(**data)
    actions = PollinationEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_pollination_interval_not_elapsed():
    # current hour 10, window 8-12, last pollination 1 day ago (interval is 2 days)
    data = create_base_snapshot(
        current_hour=10,
        pollination_window={"start_hour": 8, "end_hour": 12, "interval_days": 2},
        last_pollination_time_diff=timedelta(days=1)
    )
    snapshot = StateSnapshot(**data)
    actions = PollinationEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_pollination_interval_elapsed():
    # current hour 10, window 8-12, last pollination 3 days ago (interval is 2 days)
    data = create_base_snapshot(
        current_hour=10,
        pollination_window={"start_hour": 8, "end_hour": 12, "interval_days": 2},
        last_pollination_time_diff=timedelta(days=3)
    )
    snapshot = StateSnapshot(**data)
    actions = PollinationEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "pollinate"
    assert actions[0].parameters["plant_id"] == 1
