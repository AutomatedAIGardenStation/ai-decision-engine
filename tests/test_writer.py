from src.arduino.writer import send_command, _is_socket_address, _is_serial_port

def test_writer_coverage():
    send_command("")

    assert _is_socket_address("localhost:9999")
    assert not _is_socket_address("COM1")

    assert _is_serial_port("COM1")
    assert _is_serial_port("/dev/ttyUSB0")
    assert not _is_serial_port("sim.log")

def test_writer_send_file(tmp_path):
    f = tmp_path / "sim.log"
    send_command("W1", port=str(f))
    assert f.read_bytes() == b"W1\n"
