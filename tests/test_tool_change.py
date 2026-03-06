from src.evaluators.tool_change import ToolChangeEvaluator
from src.schemas.state_snapshot import StateSnapshot

def test_tool_change_evaluator_requires_dock_and_release():
    snapshot = StateSnapshot(
        trigger_event="EVT:HARVEST",
        tool_state="CAMERA",
        harvest_queue=[1]
    )

    actions = ToolChangeEvaluator.evaluate(snapshot)
    assert len(actions) == 2
    assert actions[0].action == "TOOL_DOCK"
    assert actions[1].action == "TOOL_RELEASE"
    assert actions[1].parameters["required_tool"] == "GRIPPER"

def test_tool_change_evaluator_only_release():
    snapshot = StateSnapshot(
        trigger_event="EVT:HARVEST",
        tool_state="NONE",
        harvest_queue=[1]
    )

    actions = ToolChangeEvaluator.evaluate(snapshot)
    assert len(actions) == 1
    assert actions[0].action == "TOOL_RELEASE"
    assert actions[0].parameters["required_tool"] == "GRIPPER"

def test_tool_change_evaluator_no_action_needed():
    snapshot = StateSnapshot(
        trigger_event="EVT:HARVEST",
        tool_state="GRIPPER",
        harvest_queue=[1]
    )

    actions = ToolChangeEvaluator.evaluate(snapshot)
    assert len(actions) == 0

def test_tool_change_evaluator_camera_needed():
    # If no harvest queue, defaults to CAMERA
    snapshot = StateSnapshot(
        trigger_event="EVT:SOIL_DRY",
        tool_state="GRIPPER",
        harvest_queue=[]
    )

    actions = ToolChangeEvaluator.evaluate(snapshot)
    assert len(actions) == 2
    assert actions[0].action == "TOOL_DOCK"
    assert actions[1].action == "TOOL_RELEASE"
    assert actions[1].parameters["required_tool"] == "CAMERA"
