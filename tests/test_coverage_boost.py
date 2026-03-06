from src.evaluators.dosing import DosingEvaluator
from src.evaluators.harvest import HarvestEvaluator
from src.evaluators.tool_change import ToolChangeEvaluator
from src.decision.constraints import SafetyGates
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action
from src.api.server import app
from fastapi.testclient import TestClient

def test_dosing_zero_plant_targets():
    snapshot = StateSnapshot(
        trigger_event="EVT:DOSING_CHECK",
        sensor_snapshot={"ec": 1.0, "ph": 6.0, "water_temp": 20.0, "air_temp": 20.0, "air_humidity": 50.0},
        plant_targets=[]
    )
    assert len(DosingEvaluator.evaluate(snapshot)) == 0

def test_dosing_no_trigger_event():
    snapshot = StateSnapshot()
    assert len(DosingEvaluator.evaluate(snapshot)) == 0

def test_tool_change_no_trigger():
    snapshot = StateSnapshot()
    assert len(ToolChangeEvaluator.evaluate(snapshot)) == 0

def test_harvest_missing_queue():
    # To hit line 45
    snapshot = StateSnapshot(queue_state={"harvest_pending_ids": [1], "active_harvest_id": 1}, ml_results=[{"plant_id": 1, "ripeness": "ripe", "confidence": 0.4}])
    HarvestEvaluator.evaluate(snapshot)

def test_safety_gates_no_trigger():
    snapshot = StateSnapshot()
    actions = [Action(action="water", parameters={}, reason="", priority="low")]
    assert SafetyGates.apply(actions, snapshot) == actions

def test_main_startup():
    with TestClient(app):
        pass
