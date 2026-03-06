from typing import List
from datetime import timedelta
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class WateringEvaluator:
    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions = []

        if snapshot.trigger_event is not None:
            # New lightweight event context logic
            if snapshot.trigger_event == "EVT:SOIL_DRY":
                actions.append(
                    Action(
                        action="PUMP_RUN",
                        parameters={"ms": 3000},
                        reason="Soil is dry, running pump",
                        priority="high"
                    )
                )
            return actions

        # Legacy logic
        if snapshot.system_config and snapshot.system_config.maintenance_mode:
            return actions

        if not snapshot.system_config or not snapshot.sensor_readings or not snapshot.plant_profiles or not snapshot.history:
            return actions

        zone_count = snapshot.system_config.zone_count

        for zone in range(zone_count):
            # Prevent out-of-bounds access if data is missing/malformed
            if zone >= len(snapshot.sensor_readings.soil_moisture) or zone >= len(snapshot.plant_profiles):
                continue

            moisture = snapshot.sensor_readings.soil_moisture[zone]
            profile = snapshot.plant_profiles[zone]

            last_watering_time = snapshot.history.last_watering.get(zone)

            # Check cooldown
            if last_watering_time is not None:
                time_diff = snapshot.timestamp - last_watering_time
                if time_diff < timedelta(minutes=30):
                    if moisture < 10.0:
                        actions.append(
                            Action(
                                action="alert",
                                parameters={"zone": zone},
                                reason="Critical moisture — watering blocked by cooldown",
                                priority="high"
                            )
                        )
                    continue

            target = profile.moisture_target

            if moisture < target * 0.85:
                deficit = target - moisture
                duration_s = min(60, max(1, int(deficit)))
                actions.append(
                    Action(
                        action="water",
                        parameters={"zone": zone, "duration_s": duration_s},
                        reason=f"Moisture {moisture}% below target {target}%",
                        priority="high"
                    )
                )
            elif moisture > target * 1.1:
                actions.append(
                    Action(
                        action="stop_watering",
                        parameters={"zone": zone},
                        reason=f"Moisture {moisture}% above target {target}%",
                        priority="high"
                    )
                )

        return actions
