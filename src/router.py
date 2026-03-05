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

class DecisionRouter:
    def __init__(self):
        self.evaluators = [
            WateringEvaluator,
            ClimateEvaluator,
            LightingEvaluator,
            HarvestEvaluator,
            PollinationEvaluator,
            NutrientEvaluator
        ]

        # Priority map for deduplication
        self.priority_map = {
            "low": 1,
            "medium": 2,
            "high": 3
        }

    def evaluate(self, snapshot: StateSnapshot) -> ActionList:
        start_time = time.perf_counter()

        raw_actions: List[Action] = []
        for evaluator in self.evaluators:
            raw_actions.extend(evaluator.evaluate(snapshot))

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

        end_time = time.perf_counter()
        decision_time_ms = int((end_time - start_time) * 1000)
        # Ensure it is positive integer (if very fast, at least 1)
        if decision_time_ms <= 0:
            decision_time_ms = 1

        return ActionList(
            actions=final_actions,
            metadata=DecisionMetadata(
                engine_version="0.1.0",
                decision_time_ms=decision_time_ms
            )
        )
