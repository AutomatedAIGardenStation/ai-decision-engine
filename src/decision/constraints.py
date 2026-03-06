from typing import List
from src.schemas.action_list import Action
from src.schemas.state_snapshot import StateSnapshot

class SafetyGates:
    @staticmethod
    def apply(actions: List[Action], snapshot: StateSnapshot) -> List[Action]:
        if snapshot.trigger_event is None:
            return actions

        filtered_actions = []


        # Determine required tool from tool_change evaluation
        required_tool = snapshot.tool_state
        if snapshot.harvest_queue and len(snapshot.harvest_queue) > 0:
            required_tool = "GRIPPER"
        else:
            required_tool = "CAMERA"

        is_tool_ready = (snapshot.tool_state == required_tool)

        for action in actions:
            # Block physical movement/actuator commands if the correct tool isn't attached,
            # EXCEPT tool change commands themselves!
            if action.action in ["ARM_MOVE_TO", "GRIPPER_CLOSE"] and not is_tool_ready:
                # Discard these actions, they will be generated again once the tool is correct
                continue

            filtered_actions.append(action)

        # Ensure TOOL_DOCK and TOOL_RELEASE are at the front of the queue
        tool_actions = [a for a in filtered_actions if a.action in ["TOOL_DOCK", "TOOL_RELEASE"]]
        other_actions = [a for a in filtered_actions if a.action not in ["TOOL_DOCK", "TOOL_RELEASE"]]

        return tool_actions + other_actions
