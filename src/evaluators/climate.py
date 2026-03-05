from typing import List
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class ClimateEvaluator:
    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions = []

        if snapshot.system_config.maintenance_mode:
            return actions

        temp = snapshot.sensor_readings.temp
        temp_max = snapshot.system_config.temp_max
        temp_min = snapshot.system_config.temp_min

        if temp > temp_max:
            actions.append(
                Action(
                    action="fan_set",
                    parameters={"pct": 100},
                    reason="temp above max",
                    priority="high"
                )
            )
        elif temp < temp_min:
            actions.append(
                Action(
                    action="fan_set",
                    parameters={"pct": 0},
                    reason="temp below min",
                    priority="high"
                )
            )
            actions.append(
                Action(
                    action="alert",
                    parameters={},
                    reason="heating not yet implemented",
                    priority="high"
                )
            )
        else:
            pct = int(((temp - temp_min) / (temp_max - temp_min)) * 80)
            actions.append(
                Action(
                    action="fan_set",
                    parameters={"pct": pct},
                    reason="proportional cooling",
                    priority="medium"
                )
            )

        return actions
