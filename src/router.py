import time
from typing import List, Dict, Tuple
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import ActionList, DecisionMetadata, Action
from src.evaluators.watering import WateringEvaluator
from src.evaluators.climate import ClimateEvaluator
from src.evaluators.lighting import LightingEvaluator
from src.evaluators.harvest import HarvestEvaluator
from src.evaluators.pollination import PollinationEvaluator
from src.evaluators.nutrient import NutrientEvaluator
from src.evaluators.dosing import DosingEvaluator
from src.evaluators.tool_change import ToolChangeEvaluator
from src.decision.constraints import SafetyGates

class DecisionRouter:
    def __init__(self):
        # Legacy evaluators
        self.legacy_evaluators = [
            WateringEvaluator,
            ClimateEvaluator,
            LightingEvaluator,
            HarvestEvaluator,
            PollinationEvaluator,
            NutrientEvaluator
        ]

        # Lightweight event context evaluators
        self.event_evaluators = [
            WateringEvaluator,
            DosingEvaluator,
            ToolChangeEvaluator,
            HarvestEvaluator
        ]

        # Priority map for deduplication
        self.priority_map = {
            "low": 1,
            "medium": 2,
            "high": 3
        }

        # For backwards compatibility with old tests accessing self.evaluators
        self.evaluators = self.legacy_evaluators

    def evaluate(self, snapshot: StateSnapshot) -> ActionList:
        start_time = time.perf_counter()

        raw_actions: List[Action] = []

        # Choose which set of evaluators to run based on the payload type
        if snapshot is not None and snapshot.trigger_event is not None:
            active_evaluators = self.event_evaluators
        else:
            active_evaluators = self.evaluators # typically self.legacy_evaluators

        for evaluator in active_evaluators:
            raw_actions.extend(evaluator.evaluate(snapshot))

        # Apply constraints if event-driven payload
        if snapshot is not None and snapshot.trigger_event is not None:
            raw_actions = SafetyGates.apply(raw_actions, snapshot)

        # Deduplication
        dedup_map: Dict[Tuple[str, str], Action] = {}
        for action in raw_actions:
            # Create a hashable key for parameters dict
            params_tuple = tuple(sorted(action.parameters.items()))
            key = (action.action, str(params_tuple))

            if key in dedup_map:
                existing_action = dedup_map[key]
                if self.priority_map[action.priority] > self.priority_map[existing_action.priority]:
                    dedup_map[key] = action
            else:
                dedup_map[key] = action

        final_actions = list(dedup_map.values())

        # Sort actions deterministically:
        # 1. High priority first (descending by priority map value)
        # 2. Alphabetically by action name
        # 3. Alphabetically by string representation of sorted parameters
        final_actions.sort(
            key=lambda a: (
                -self.priority_map.get(a.priority, 0),
                a.action,
                str(tuple(sorted(a.parameters.items())))
            )
        )

        # Additional safety gates step ensuring TOOL_DOCK/RELEASE at front
        if snapshot is not None and snapshot.trigger_event is not None:
            tool_actions = [a for a in final_actions if a.action in ["TOOL_DOCK", "TOOL_RELEASE"]]
            other_actions = [a for a in final_actions if a.action not in ["TOOL_DOCK", "TOOL_RELEASE"]]
            final_actions = tool_actions + other_actions

        end_time = time.perf_counter()
        decision_time_ms = int((end_time - start_time) * 1000)
        # Ensure it is positive integer (if very fast, at least 1)
        if decision_time_ms <= 0:
            decision_time_ms = 1

        # The decision engine is completely stateless and returns canonical actions.
        # Direct serial side effects are explicitly forbidden here and reside in the CLI adapter only.

        return ActionList(
            actions=final_actions,
            metadata=DecisionMetadata(
                engine_version="0.1.0",
                decision_time_ms=decision_time_ms
            )
        )
