import pytest
from datetime import datetime, timezone
from src.schemas.state_snapshot import StateSnapshot
from src.evaluators.harvest import HarvestEvaluator

def create_base_snapshot(
    maintenance_mode: bool = False,
    ml_results: list = None,
    harvest_pending_ids: list = None,
    active_harvest_id: int = None
) -> dict:
    timestamp = datetime.now(timezone.utc)
    if ml_results is None:
        ml_results = []
    if harvest_pending_ids is None:
        harvest_pending_ids = []

    return {
        "sensor_readings": {
            "temp": 24.5,
            "humidity": 60.0,
            "ph": 6.0,
            "ec": 1.5,
            "soil_moisture": [50.0],
            "tank_level_pct": 85.0
        },
        "ml_results": ml_results,
        "plant_profiles": [],
        "queue_state": {
            "harvest_pending_ids": harvest_pending_ids,
            "active_harvest_id": active_harvest_id
        },
        "system_config": {
            "maintenance_mode": maintenance_mode,
            "zone_count": 1,
            "max_pump_time_s": 120
        },
        "history": {
            "last_watering": {},
            "last_pollination": None
        },
        "timestamp": timestamp
    }

def test_harvest_maintenance_mode():
    data = create_base_snapshot(
        maintenance_mode=True,
        ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.9, "disease": None}]
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_enqueue_ripe_plant():
    data = create_base_snapshot(
        ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.8, "disease": None}]
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "enqueue_harvest"
    assert actions[0].parameters["plant_id"] == 1
    assert actions[0].parameters["confidence"] == 0.8

def test_skip_low_confidence():
    data = create_base_snapshot(
        ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.74, "disease": None}]
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_skip_already_pending():
    data = create_base_snapshot(
        ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.9, "disease": None}],
        harvest_pending_ids=[1]
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_skip_unripe():
    data = create_base_snapshot(
        ml_results=[{"plant_id": 1, "ripeness": "unripe", "confidence": 0.9, "disease": None}]
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_active_harvest_skip_enqueue():
    # If plant is active harvest, it should not be enqueued again
    data = create_base_snapshot(
        ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.9, "disease": None}],
        active_harvest_id=1
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_active_harvest_confirmed():
    # active harvest id is set, and ml result has confidence >= 0.5 for it
    # No alert should be generated
    data = create_base_snapshot(
        ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.6, "disease": None}],
        active_harvest_id=1
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_active_harvest_unconfirmed_no_ml_result():
    # active harvest id is set, but no ml result for it
    data = create_base_snapshot(
        ml_results=[{"plant_id": 2, "ripeness": "ripe", "confidence": 0.9, "disease": None}],
        active_harvest_id=1
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)

    # One for enqueueing plant 2, one for alerting about plant 1
    assert len(actions) == 2

    enqueue_actions = [a for a in actions if a.action == "enqueue_harvest"]
    alert_actions = [a for a in actions if a.action == "alert"]

    assert len(enqueue_actions) == 1
    assert enqueue_actions[0].parameters["plant_id"] == 2

    assert len(alert_actions) == 1
    assert alert_actions[0].parameters["plant_id"] == 1
    assert alert_actions[0].reason == "Harvest in progress — no vision confirmation"

def test_active_harvest_unconfirmed_low_confidence():
    # active harvest id is set, ml result exists but confidence < 0.5
    data = create_base_snapshot(
        ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.4, "disease": None}],
        active_harvest_id=1
    )
    snapshot = StateSnapshot(**data)
    actions = HarvestEvaluator.evaluate(snapshot)

    assert len(actions) == 1
    assert actions[0].action == "alert"
    assert actions[0].parameters["plant_id"] == 1
