import yaml
import os
from typing import List
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import Action

class DosingEvaluator:
    @staticmethod
    def _load_calibration() -> dict:
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'arduino_commands.yaml'
        )
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('calibration', {})
        except Exception:
            return {}

    @staticmethod
    def evaluate(snapshot: StateSnapshot) -> List[Action]:
        actions = []
        if snapshot.trigger_event is None:
            return actions

        if not snapshot.sensor_snapshot or not snapshot.plant_targets:
            return actions

        # Calculate average targets from all plant targets
        if len(snapshot.plant_targets) == 0:
            return actions

        avg_ec_target = sum(pt.ec_target for pt in snapshot.plant_targets) / len(snapshot.plant_targets)
        avg_ph_target = sum(pt.ph_target for pt in snapshot.plant_targets) / len(snapshot.plant_targets)

        current_ec = snapshot.sensor_snapshot.ec
        current_ph = snapshot.sensor_snapshot.ph

        ec_deficit = avg_ec_target - current_ec
        ph_deficit = avg_ph_target - current_ph

        # Only dose if there is a noticeable deficit or surplus
        if ec_deficit <= 0.1 and abs(ph_deficit) <= 0.2:
            return actions

        calib = DosingEvaluator._load_calibration()
        nutA_factor = calib.get('NutA_ms_per_unit', 100)
        nutB_factor = calib.get('NutB_ms_per_unit', 80)
        ph_up_factor = calib.get('pH_Up_ms_per_unit', 50)
        ph_down_factor = calib.get('pH_Down_ms_per_unit', 50)

        NutA_ms = max(0, int(ec_deficit * nutA_factor)) if ec_deficit > 0 else 0
        NutB_ms = max(0, int(ec_deficit * nutB_factor)) if ec_deficit > 0 else 0

        pH_Up_ms = 0
        pH_Down_ms = 0
        if ph_deficit > 0:
            pH_Up_ms = int(ph_deficit * ph_up_factor)
        elif ph_deficit < 0:
            pH_Down_ms = int(abs(ph_deficit) * ph_down_factor)

        if NutA_ms > 0 or NutB_ms > 0 or pH_Up_ms > 0 or pH_Down_ms > 0:
            actions.append(
                Action(
                    action="DOSE_RECIPE",
                    parameters={
                        "NutA": NutA_ms,
                        "NutB": NutB_ms,
                        "pH_Up": pH_Up_ms,
                        "pH_Down": pH_Down_ms
                    },
                    reason="Deficit in EC/pH requiring dosing",
                    priority="high"
                )
            )

        return actions
