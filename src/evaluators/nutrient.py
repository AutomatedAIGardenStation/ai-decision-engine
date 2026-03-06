from typing import List
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class NutrientEvaluator:
    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions: List[Action] = []

        if snapshot.system_config.maintenance_mode:
            return actions

        zone_count = snapshot.system_config.zone_count

        for zone in range(zone_count):
            if zone >= len(snapshot.plant_profiles):
                continue

            ec = snapshot.sensor_readings.ec
            ph = snapshot.sensor_readings.ph
            profile = snapshot.plant_profiles[zone]

            if ec < profile.ec_target * 0.9:
                actions.append(
                    Action(
                        action="DOSE_RECIPE",
                        parameters={"NutA": 500, "NutB": 500},
                        reason="EC below target",
                        priority="high"
                    )
                )
            elif ec > profile.ec_target * 1.15:
                actions.append(
                    Action(
                        action="WATER_FLUSH",
                        parameters={"zone": zone},
                        reason="EC above target",
                        priority="high"
                    )
                )

            if ph < profile.ph_min:
                actions.append(
                    Action(
                        action="DOSE_RECIPE",
                        parameters={"pH_Up": 500},
                        reason="pH below minimum",
                        priority="high"
                    )
                )
                actions.append(
                    Action(
                        action="alert",
                        parameters={"zone": zone},
                        reason="pH below minimum",
                        priority="high"
                    )
                )
            elif ph > profile.ph_max:
                actions.append(
                    Action(
                        action="DOSE_RECIPE",
                        parameters={"pH_Down": 500},
                        reason="pH above maximum",
                        priority="high"
                    )
                )
                actions.append(
                    Action(
                        action="alert",
                        parameters={"zone": zone},
                        reason="pH above maximum",
                        priority="high"
                    )
                )

        return actions
