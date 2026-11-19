import socket

import run


def test_find_free_port_skips_occupied_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        busy = s.getsockname()[1]
        free = run.find_free_port(preferred=busy, host="127.0.0.1")
        assert free != busy
        assert free > 0
