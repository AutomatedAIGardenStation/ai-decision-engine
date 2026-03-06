from typing import List
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class HarvestEvaluator:
    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions = []

        if snapshot.trigger_event is not None:
            # New lightweight event context logic
            if snapshot.harvest_queue and len(snapshot.harvest_queue) > 0:
                target_id = snapshot.harvest_queue[0]
                # Find plant coordinates if available in plant_targets
                x, y, z = 0, 0, 0
                if snapshot.plant_targets:
                    for pt in snapshot.plant_targets:
                        if pt.plant_id == target_id:
                            x, y, z = pt.x, pt.y, pt.z
                            break

                actions.append(
                    Action(
                        action="ARM_MOVE_TO",
                        parameters={"x": x, "y": y, "z": z},
                        reason=f"Moving to harvest plant {target_id}",
                        priority="high"
                    )
                )
                actions.append(
                    Action(
                        action="GRIPPER_CLOSE",
                        parameters={},
                        reason=f"Harvesting plant {target_id}",
                        priority="high"
                    )
                )
            return actions

        # Legacy logic
        if snapshot.system_config and snapshot.system_config.maintenance_mode:
            return actions

        if not snapshot.queue_state or not snapshot.ml_results:
            return actions

        active_harvest_id = snapshot.queue_state.active_harvest_id
        active_harvest_confirmed = False

        for ml_result in snapshot.ml_results:
            if ml_result.plant_id == active_harvest_id and ml_result.confidence >= 0.5:
                active_harvest_confirmed = True

            if (
                ml_result.ripeness == "ripe"
                and ml_result.confidence >= 0.75
                and ml_result.plant_id not in snapshot.queue_state.harvest_pending_ids
                and ml_result.plant_id != active_harvest_id
            ):
                actions.append(
                    Action(
                        action="enqueue_harvest",
                        parameters={"plant_id": ml_result.plant_id, "confidence": ml_result.confidence},
                        reason="Plant is ripe and not already pending harvest",
                        priority="high"
                    )
                )

        if active_harvest_id is not None and not active_harvest_confirmed:
            actions.append(
                Action(
                    action="alert",
                    parameters={"plant_id": active_harvest_id},
                    reason="Harvest in progress — no vision confirmation",
                    priority="high"
                )
            )

        return actions
