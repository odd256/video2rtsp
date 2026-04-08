from __future__ import annotations

import socket
import subprocess
import time
from collections.abc import Callable


def make_tcp_probe(host: str, port: int) -> Callable[[], bool]:
    def probe() -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            return False

    return probe


def wait_port_ready(
    timeout_sec: int,
    probe: Callable[[], bool],
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    deadline = time.monotonic() + float(timeout_sec)
    while time.monotonic() < deadline:
        if probe():
            return True
        sleep(0.1)
    return probe()


def start_mediamtx(bin_path: str, config_path: str, extra_args: list[str] | None = None) -> subprocess.Popen:
    args = [bin_path, config_path]
    if extra_args:
        args.extend(extra_args)
    return subprocess.Popen(args)


def stop_mediamtx(proc: subprocess.Popen, timeout_sec: float = 3.0) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=timeout_sec)
    except Exception:
        proc.kill()

