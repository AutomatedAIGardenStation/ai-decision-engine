"""
Send a command string to Arduino (or simulation) over serial, TCP socket, or file.
"""
from pathlib import Path

# Optional serial; avoid hard dependency at import if pyserial missing.
try:
    import serial
except ImportError:
    serial = None  # type: ignore

# Default: write to a file for simulation when port is a path.
def send_command(
    command: str | bytes,
    port: str | None = None,
    baud: int = 9600,
    use_file: bool | None = None,
) -> None:
    """
    Send command to Arduino or simulation. If port is host:port (e.g. 127.0.0.1:9999),
    use TCP socket. If port is a file path or use_file is True, append to file.
    Otherwise use serial.
    """
    if command is None or (isinstance(command, str) and not command.strip()):
        return
    payload = command if isinstance(command, bytes) else command.strip().encode("utf-8")
    if not payload:
        return

    if port and _is_socket_address(port):
        _send_to_socket(payload, port)
        return

    path = Path(port) if port else None
    if use_file is True or (port and path and (not _is_serial_port(port))):
        _send_to_file(payload, path or Path("arduino_commands.log"))
        return

    if serial is None:
        raise RuntimeError("pyserial is required for serial output; install with: pip install pyserial")
    with serial.Serial(port or "COM1", baud, timeout=1) as ser:
        ser.write(payload)
        if not payload.endswith(b"\n"):
            ser.write(b"\n")


def _is_socket_address(port: str) -> bool:
    """True if port looks like host:port (e.g. 127.0.0.1:9999 or localhost:9999)."""
    s = port.strip()
    if ":" not in s:
        return False
    host, _, port_part = s.rpartition(":")
    return bool(host and port_part and port_part.isdigit())


def _is_serial_port(port: str) -> bool:
    """Heuristic: COM1, /dev/ttyUSB0 etc. are serial; paths with slashes or .log are file."""
    if _is_socket_address(port):
        return False
    p = port.strip().upper()
    if p.startswith("COM") and p[3:].isdigit():
        return True
    if "/dev/" in port or "tty" in port:
        return True
    return False


def _send_to_socket(payload: bytes, address: str) -> None:
    """Open TCP connection to host:port, send payload + newline, close."""
    import socket
    host, _, port_str = address.strip().rpartition(":")
    port = int(port_str)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect((host, port))
        sock.sendall(payload)
        if not payload.endswith(b"\n"):
            sock.sendall(b"\n")


def _send_to_file(payload: bytes, path: Path) -> None:
    path = Path(path)
    with path.open("ab") as f:
        f.write(payload)
        if not payload.endswith(b"\n"):
            f.write(b"\n")
