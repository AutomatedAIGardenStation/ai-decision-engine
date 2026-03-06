from typing import List
from datetime import timedelta
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class PollinationEvaluator:
    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions: List[Action] = []

        if snapshot.system_config.maintenance_mode:
            return actions

        hour = snapshot.timestamp.hour
        last_pollination = snapshot.history.last_pollination

        for profile in snapshot.plant_profiles:
            if profile.pollination_window is not None:
                start = profile.pollination_window.start_hour
                end = profile.pollination_window.end_hour
                interval = profile.pollination_window.interval_days

                # Note: `end` is typically exclusive for simple hour-based windows (e.g., 08:00-12:00 means 8, 9, 10, 11)
                # Following `start_hour <= hour < end_hour` logic seen in lighting evaluator
                if start <= hour < end:
                    if last_pollination is None or (snapshot.timestamp - last_pollination) > timedelta(days=interval):
                        actions.append(
                            Action(
                                action="pollinate",
                                parameters={"plant_id": profile.id},
                                reason="Within pollination window and interval has elapsed",
                                priority="medium"
                            )
                        )

        return actions
