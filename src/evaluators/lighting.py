from typing import List
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class LightingEvaluator:
    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions: List[Action] = []

        if snapshot.system_config.maintenance_mode:
            return actions

        hour = snapshot.timestamp.hour
        active_period = None

        for period in snapshot.system_config.light_schedule:
            if period.start_hour <= hour < period.end_hour:
                active_period = period
                break

        zone_count = snapshot.system_config.zone_count

        if active_period is not None:
            for ch in range(zone_count):
                actions.append(
                    Action(
                        action="LIGHT_SET",
                        parameters={"ch": ch, "pct": active_period.intensity_pct},
                        reason="scheduled lighting",
                        priority="low"
                    )
                )
        else:
            # If no active period: add LIGHT_SET {"ch": ch, "pct": 0} for all channels
            for ch in range(zone_count):
                actions.append(
                    Action(
                        action="LIGHT_SET",
                        parameters={"ch": ch, "pct": 0},
                        reason="outside light schedule",
                        priority="low"
                    )
                )

        return actions
