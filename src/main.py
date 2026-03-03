"""
Main controller: read recognition -> features -> rules/tree -> command -> send to Arduino/simulation.
"""
import argparse
from pathlib import Path

import yaml

from src.decision.features import recognition_to_features
from src.decision.tree import predict_action
from src.decision.rules import evaluate_rules
from src.recognition.reader import read_recognition
from src.arduino.writer import send_command


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_arduino_commands(config_dir: Path | None = None) -> dict[str, str]:
    """Load config/arduino_commands.yaml."""
    base = config_dir or _project_root() / "config"
    path = base / "arduino_commands.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {k: str(v).strip() for k, v in data.items() if v}


def run_once(
    recognition_source: str | Path | None = None,
    config_dir: Path | None = None,
    models_dir: Path | None = None,
    serial_port: str | None = None,
    serial_baud: int = 9600,
    dry_run: bool = False,
) -> str:
    """
    One decision cycle: read recognition, decide action, optionally send command.
    Returns the chosen action.
    """
    root = _project_root()
    config_dir = config_dir or root / "config"
    models_dir = models_dir or root / "models"

    rec = read_recognition(recognition_source)
    features = recognition_to_features(rec)
    rec["feature_vector"] = features

    action = evaluate_rules(rec, config_dir)
    if action is None:
        action = predict_action(features, models_dir)

    commands = load_arduino_commands(config_dir)
    command = commands.get(action, commands.get("no_action", "NOP"))

    if not dry_run and command:
        send_command(command, port=serial_port, baud=serial_baud)
    return action


def main() -> None:
    parser = argparse.ArgumentParser(description="GardenStation AI: recognition -> decision -> Arduino")
    parser.add_argument(
        "--recognition",
        type=str,
        default=None,
        help="Path to recognition JSON file; omit for stub",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=None,
        help="Config directory (default: project config/)",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=None,
        help="Models directory (default: project models/)",
    )
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="Serial port (e.g. COM3) or file path for simulation",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=9600,
        help="Serial baud rate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not send command to serial",
    )
    args = parser.parse_args()

    action = run_once(
        recognition_source=args.recognition,
        config_dir=args.config_dir,
        models_dir=args.models_dir,
        serial_port=args.port,
        serial_baud=args.baud,
        dry_run=args.dry_run,
    )
    print(action)


if __name__ == "__main__":
    main()
