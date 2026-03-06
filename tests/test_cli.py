import json
import sys
from unittest.mock import patch, mock_open, MagicMock

import pytest

from src.cli import main
from src.schemas.action_list import ActionList, DecisionMetadata, Action


@pytest.fixture
def mock_snapshot_data():
    return {
        "sensor_readings": {
            "temp": 24.5,
            "humidity": 60.0,
            "ph": 6.0,
            "ec": 1.5,
            "soil_moisture": [30.5, 32.0],
            "tank_level_pct": 85.0
        },
        "ml_results": [],
        "plant_profiles": [],
        "queue_state": {
            "harvest_pending_ids": [],
            "active_harvest_id": None
        },
        "system_config": {
            "maintenance_mode": False,
            "zone_count": 2,
            "max_pump_time_s": 120
        },
        "history": {
            "last_watering": {},
            "last_pollination": None
        },
        "timestamp": "2023-10-26T12:00:00Z"
    }


def test_cli_missing_recognition():
    with patch.object(sys, "argv", ["cli.py"]), patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
        mock_print.assert_called_with("Error: --recognition argument is required.")


@patch("pathlib.Path.exists")
def test_cli_file_not_found(mock_exists):
    mock_exists.return_value = False
    with patch.object(sys, "argv", ["cli.py", "--recognition", "nonexistent.json"]), patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
        mock_print.assert_called_with("Error: File not found: nonexistent.json")


@patch("pathlib.Path.exists")
@patch("builtins.open", new_callable=mock_open)
@patch("src.cli.DecisionRouter")
def test_cli_dry_run(mock_router_cls, mock_open_file, mock_exists, mock_snapshot_data):
    mock_exists.return_value = True
    mock_open_file.return_value.read.return_value = json.dumps(mock_snapshot_data)

    mock_router = MagicMock()
    mock_router.evaluate.return_value = ActionList(
        actions=[Action(action="PUMP_RUN", parameters={"ms": 3000}, reason="test", priority="high")],
        metadata=DecisionMetadata(engine_version="0.1.0", decision_time_ms=10)
    )
    mock_router_cls.return_value = mock_router

    with patch.object(sys, "argv", ["cli.py", "--recognition", "fake.json", "--dry-run"]), patch("builtins.print") as mock_print:
        main()
        mock_print.assert_called()
        output = mock_print.call_args[0][0]
        assert "PUMP_RUN" in output


@patch("pathlib.Path.exists")
@patch("builtins.open", new_callable=mock_open)
@patch("src.cli.DecisionRouter")
def test_cli_write_to_file(mock_router_cls, mock_open_file, mock_exists, mock_snapshot_data):
    mock_exists.return_value = True
    mock_open_file.return_value.read.return_value = json.dumps(mock_snapshot_data)

    mock_router = MagicMock()
    mock_router.evaluate.return_value = ActionList(
        actions=[],
        metadata=DecisionMetadata(engine_version="0.1.0", decision_time_ms=10)
    )
    mock_router_cls.return_value = mock_router

    with patch.object(sys, "argv", ["cli.py", "--recognition", "fake.json", "--port", "out.txt"]), patch("builtins.print") as mock_print:
        main()
        mock_print.assert_called_with("Wrote actions to out.txt")
        # Ensure it wrote to the file
        mock_open_file.assert_any_call("out.txt", "w", encoding="utf-8")


@patch("pathlib.Path.exists")
@patch("builtins.open", new_callable=mock_open)
@patch("src.cli.DecisionRouter")
@patch("src.cli.serial")
def test_cli_write_to_serial(mock_serial, mock_router_cls, mock_open_file, mock_exists, mock_snapshot_data):
    mock_exists.return_value = True
    mock_open_file.return_value.read.return_value = json.dumps(mock_snapshot_data)

    mock_router = MagicMock()
    mock_router.evaluate.return_value = ActionList(
        actions=[],
        metadata=DecisionMetadata(engine_version="0.1.0", decision_time_ms=10)
    )
    mock_router_cls.return_value = mock_router

    mock_ser_instance = MagicMock()
    mock_serial.Serial.return_value = mock_ser_instance

    with patch.object(sys, "argv", ["cli.py", "--recognition", "fake.json", "--port", "COM3"]), patch("builtins.print") as mock_print:
        main()
        mock_print.assert_called_with("Sent actions to serial port COM3")
        mock_serial.Serial.assert_called_with("COM3", 115200, timeout=1)
        mock_ser_instance.write.assert_called()
        mock_ser_instance.close.assert_called()
