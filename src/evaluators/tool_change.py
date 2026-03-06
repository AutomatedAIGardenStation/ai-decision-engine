from typing import List
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class ToolChangeEvaluator:
    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions: List[Action] = []
        if snapshot.trigger_event is None:
            return actions

        # Tool mapping logic based on event or queue
        required_tool = "CAMERA" # default

        if snapshot.harvest_queue and len(snapshot.harvest_queue) > 0:
            required_tool = "GRIPPER"

        current_tool = snapshot.tool_state

        if current_tool != required_tool:
            if current_tool != "NONE":
                actions.append(
                    Action(
                        action="TOOL_DOCK",
                        parameters={},
                        reason=f"Docking current tool {current_tool}",
                        priority="high"
                    )
                )
            actions.append(
                Action(
                    action="TOOL_RELEASE",
                    parameters={"required_tool": required_tool},
                    reason=f"Attaching required tool {required_tool}",
                    priority="high"
                )
            )

        return actions
