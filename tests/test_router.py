from datetime import datetime, timezone
from src.schemas.state_snapshot import (
    StateSnapshot,
    SensorReadings,
    MLResult,
    PlantProfile,
    PollinationWindow,
    QueueState,
    SystemConfig,
    History
)
from src.schemas.action_list import ActionList
from src.router import DecisionRouter

def test_router_end_to_end():
    snapshot = StateSnapshot(
        sensor_readings=SensorReadings(
            temp=32.0,            # high -> cooling needed
            humidity=80.0,
            ph=7.5,               # max is 6.5 -> add_acid + alert
            ec=1.0,               # target is 2.0 -> add_concentrate
            soil_moisture=[10.0], # low -> water
            tank_level_pct=20.0
        ),
        ml_results=[
            MLResult(
                plant_id=1,
                ripeness="ripe",
                confidence=0.9
            )
        ],
        plant_profiles=[
            PlantProfile(
                id=1,
                name="Tomato",
                species="Solanum lycopersicum",
                moisture_target=60.0,
                ec_target=2.0,
                ph_min=5.5,
                ph_max=6.5,
                pollination_window=PollinationWindow(
                    start_hour=0,
                    end_hour=23,
                    interval_days=1
                )
            )
        ],
        queue_state=QueueState(
            harvest_pending_ids=[],
            active_harvest_id=None
        ),
        system_config=SystemConfig(
            maintenance_mode=False,
            zone_count=1,
            max_pump_time_s=60,
            temp_min=18.0,
            temp_max=30.0,
            light_schedule=[] # no light -> light_set pct=0
        ),
        history=History(
            last_watering={},
            last_pollination=datetime(2020, 1, 1, tzinfo=timezone.utc)
        ),
        timestamp=datetime.now(timezone.utc)
    )

    router = DecisionRouter()
    action_list = router.evaluate(snapshot)

    assert isinstance(action_list, ActionList)

    # decision_time_ms must be a positive integer
    assert action_list.metadata.decision_time_ms > 0
    assert isinstance(action_list.metadata.decision_time_ms, int)

    actions = action_list.actions
    assert len(actions) > 0

    action_names = [a.action for a in actions]

    # 1. Watering: soil_moisture=10.0 < target*0.85
    assert "water" in action_names

    # 2. Climate: temp=32.0 > max(30.0) -> max cooling -> fan_set pct=100
    assert "fan_set" in action_names

    # 3. Lighting: light_set pct=0
    assert "light_set" in action_names

    # 4. Harvest: MLResult is ripe -> enqueue_harvest
    assert "enqueue_harvest" in action_names

    # 5. Pollination: window matches, interval passed
    assert "pollinate" in action_names

    # 6. Nutrient: EC is 1.0 (low) -> add_concentrate, pH is 7.5 (high) -> add_acid, alert
    assert "add_concentrate" in action_names
    assert "add_acid" in action_names
    assert "alert" in action_names

def test_deduplication():
    # If an evaluator somehow generates duplicates, or if we mock evaluators to generate duplicates,
    # the router should deduplicate. We will mock the evaluators.
    router = DecisionRouter()

    class DummyEvaluator1:
        @staticmethod
        def evaluate(snap):
            from src.schemas.action_list import Action
            return [Action(action="test", parameters={"x": 1}, reason="a", priority="low")]

    class DummyEvaluator2:
        @staticmethod
        def evaluate(snap):
            from src.schemas.action_list import Action
            return [Action(action="test", parameters={"x": 1}, reason="b", priority="high")]

    router.evaluators = [DummyEvaluator1, DummyEvaluator2]

    action_list = router.evaluate(None) # we mock evaluate so snapshot can be None
    actions = action_list.actions

    assert len(actions) == 1
    # The higher priority should win
    assert actions[0].priority == "high"
    assert actions[0].reason == "b"
