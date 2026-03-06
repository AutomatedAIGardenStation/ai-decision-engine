from src.evaluators.dosing import DosingEvaluator
from src.schemas.state_snapshot import StateSnapshot, SensorSnapshot, PlantTarget

def create_dosing_snapshot(ec: float, ph: float, targets: list) -> StateSnapshot:
    return StateSnapshot(
        trigger_event="EVT:DOSING_CHECK",
        sensor_snapshot=SensorSnapshot(
            ec=ec,
            ph=ph,
            water_temp=22.0,
            air_temp=25.0,
            air_humidity=60.0
        ),
        plant_targets=targets
    )

def test_dosing_no_action_needed():
    # Targets match current sensor values
    snapshot = create_dosing_snapshot(
        ec=2.0, ph=6.0,
        targets=[PlantTarget(plant_id=1, x=0, y=0, z=0, ec_target=2.0, ph_target=6.0)]
    )
    actions = DosingEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_dosing_requires_nutrients():
    # EC target 2.5, current EC 1.5 -> Deficit = 1.0
    # NutA_factor=100, NutB_factor=80 -> NutA=100, NutB=80
    snapshot = create_dosing_snapshot(
        ec=1.5, ph=6.0,
        targets=[PlantTarget(plant_id=1, x=0, y=0, z=0, ec_target=2.5, ph_target=6.0)]
    )
    actions = DosingEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    action = actions[0]
    assert action.action == "DOSE_RECIPE"
    assert action.parameters["NutA"] == 100
    assert action.parameters["NutB"] == 80
    assert action.parameters["pH_Up"] == 0
    assert action.parameters["pH_Down"] == 0

def test_dosing_requires_ph_down():
    # pH target 6.0, current 6.5 -> Deficit = -0.5 -> pH_Down_factor=50 -> 25
    snapshot = create_dosing_snapshot(
        ec=2.0, ph=6.5,
        targets=[PlantTarget(plant_id=1, x=0, y=0, z=0, ec_target=2.0, ph_target=6.0)]
    )
    actions = DosingEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    action = actions[0]
    assert action.action == "DOSE_RECIPE"
    assert action.parameters["pH_Down"] == 25
    assert action.parameters["pH_Up"] == 0

def test_dosing_requires_ph_up():
    # pH target 6.5, current 6.0 -> Deficit = 0.5 -> pH_Up_factor=50 -> 25
    snapshot = create_dosing_snapshot(
        ec=2.0, ph=6.0,
        targets=[PlantTarget(plant_id=1, x=0, y=0, z=0, ec_target=2.0, ph_target=6.5)]
    )
    actions = DosingEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    action = actions[0]
    assert action.action == "DOSE_RECIPE"
    assert action.parameters["pH_Up"] == 25
    assert action.parameters["pH_Down"] == 0
