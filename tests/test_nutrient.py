from datetime import datetime, timezone
from src.evaluators.nutrient import NutrientEvaluator
from src.schemas.state_snapshot import (
    StateSnapshot,
    SensorReadings,
    PlantProfile,
    QueueState,
    SystemConfig,
    History
)

def create_base_snapshot(ec: float, ph: float, maintenance_mode: bool = False) -> StateSnapshot:
    return StateSnapshot(
        sensor_readings=SensorReadings(
            temp=25.0,
            humidity=60.0,
            ph=ph,
            ec=ec,
            soil_moisture=[50.0],
            tank_level_pct=100.0
        ),
        ml_results=[],
        plant_profiles=[
            PlantProfile(
                id=1,
                name="Lettuce",
                species="Lactuca sativa",
                moisture_target=60.0,
                ec_target=1.5,
                ph_min=5.5,
                ph_max=6.5
            )
        ],
        queue_state=QueueState(harvest_pending_ids=[], active_harvest_id=None),
        system_config=SystemConfig(
            maintenance_mode=maintenance_mode,
            zone_count=1,
            max_pump_time_s=60,
            temp_min=18.0,
            temp_max=30.0,
            light_schedule=[]
        ),
        history=History(last_watering={}, last_pollination=None),
        timestamp=datetime.now(timezone.utc)
    )

def test_maintenance_mode():
    snapshot = create_base_snapshot(ec=1.0, ph=5.0, maintenance_mode=True)
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_ec_below_target():
    # target * 0.9 = 1.35. ec = 1.2 -> should DOSE_RECIPE
    snapshot = create_base_snapshot(ec=1.2, ph=6.0)
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "DOSE_RECIPE"
    assert actions[0].parameters == {"NutA": 500, "NutB": 500}

def test_ec_above_target():
    # target * 1.15 = 1.725. ec = 1.8 -> should WATER_FLUSH
    snapshot = create_base_snapshot(ec=1.8, ph=6.0)
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "WATER_FLUSH"
    assert actions[0].parameters == {"zone": 0}

def test_ph_below_min():
    # min = 5.5. ph = 5.0 -> should DOSE_RECIPE + alert
    snapshot = create_base_snapshot(ec=1.5, ph=5.0)
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 2
    assert actions[0].action == "DOSE_RECIPE"
    assert actions[0].parameters == {"pH_Up": 500}
    assert actions[1].action == "alert"

def test_ph_above_max():
    # max = 6.5. ph = 7.0 -> should DOSE_RECIPE + alert
    snapshot = create_base_snapshot(ec=1.5, ph=7.0)
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 2
    assert actions[0].action == "DOSE_RECIPE"
    assert actions[0].parameters == {"pH_Down": 500}
    assert actions[1].action == "alert"

def test_ec_and_ph_combined():
    # ec = 1.2 (low), ph = 7.0 (high) -> 3 actions
    snapshot = create_base_snapshot(ec=1.2, ph=7.0)
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 3
    actions_names = [a.action for a in actions]
    # We expect 2 DOSE_RECIPE actions and 1 alert
    assert actions_names.count("DOSE_RECIPE") == 2
    assert "alert" in actions_names

def test_no_actions_needed():
    # ec = 1.5, ph = 6.0 -> ideal range
    snapshot = create_base_snapshot(ec=1.5, ph=6.0)
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_out_of_bounds_zone():
    snapshot = create_base_snapshot(ec=1.5, ph=6.0)
    snapshot.system_config.zone_count = 5 # only 1 profile exists
    # Should not crash, and should still evaluate zone 0 fine
    actions = NutrientEvaluator.evaluate(snapshot)
    assert len(actions) == 0
