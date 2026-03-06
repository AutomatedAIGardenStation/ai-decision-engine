import argparse
import json
import sys
from pathlib import Path

from src.router import DecisionRouter
from src.schemas.state_snapshot import StateSnapshot

try:
    import serial
except ImportError:
    serial = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Optional CLI Adapter for AI Decision Engine")
    parser.add_argument("--recognition", type=Path, help="Path to JSON file with recognition data/state snapshot")
    parser.add_argument("--port", type=str, help="Serial port to send commands to (e.g., COM3, /dev/ttyACM0) or file")
    parser.add_argument("--dry-run", action="store_true", help="Print commands instead of sending to serial")

    args = parser.parse_args()

    if not args.recognition:
        print("Error: --recognition argument is required.")
        sys.exit(1)

    if not args.recognition.exists():
        print(f"Error: File not found: {args.recognition}")
        sys.exit(1)

    with open(args.recognition, "r", encoding="utf-8") as f:
        data = json.load(f)

    # In legacy README, it says it reads recognition output (species, ripeness, confidence)
    # But the API endpoint `/decide` takes a StateSnapshot.
    # Let's assume the file contains a valid StateSnapshot JSON.
    try:
        snapshot = StateSnapshot(**data)
    except Exception as e:
        print(f"Error parsing StateSnapshot: {e}")
        sys.exit(1)

    router = DecisionRouter()
    action_list = router.evaluate(snapshot)

    output = action_list.model_dump()
    json_output = json.dumps(output, indent=2)

    if args.dry_run or not args.port:
        print(json_output)
    else:
        # Check if the port is a real port or a file (like sim_out.txt)
        if args.port.endswith(".txt") or args.port.endswith(".log"):
            with open(args.port, "w", encoding="utf-8") as f:
                f.write(json_output + "\n")
            print(f"Wrote actions to {args.port}")
        else:
            if serial is None:
                print("Error: pyserial is not installed. Cannot send to serial port.")
                sys.exit(1)
            try:
                ser = serial.Serial(args.port, 115200, timeout=1)
                ser.write((json_output + "\n").encode("utf-8"))
                ser.close()
                print(f"Sent actions to serial port {args.port}")
            except Exception as e:
                print(f"Failed to write to serial port {args.port}: {e}")
                sys.exit(1)

if __name__ == "__main__":
    main()
