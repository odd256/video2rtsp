from __future__ import annotations

import argparse
import subprocess
import time

from video2rtsp.config import load_config
from video2rtsp.manager import StreamManager
from video2rtsp.mediamtx import make_tcp_probe, start_mediamtx, stop_mediamtx, wait_port_ready
from video2rtsp.validate import validate_config


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="video2rtsp")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run")
    run_p.add_argument("-c", "--config", required=True)

    status_p = sub.add_parser("status")
    status_p.add_argument("-c", "--config", required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])
    if args.command == "run":
        return _cmd_run(args.config)
    if args.command == "status":
        return _cmd_status(args.config)
    return 2


def _cmd_status(config_path: str) -> int:
    cfg = load_config(config_path)
    validate_config(cfg)
    for s in cfg.streams:
        url = f"rtsp://{cfg.server.host}:{cfg.server.port}/{s.path}"
        print(f"{s.name}\t{'enabled' if s.enabled else 'disabled'}\t{url}")
    return 0


def _cmd_run(config_path: str) -> int:
    cfg = load_config(config_path)
    validate_config(cfg)

    mediamtx_proc: subprocess.Popen | None = None
    if cfg.mediamtx and cfg.mediamtx.auto_start:
        mediamtx_proc = start_mediamtx(cfg.mediamtx.bin, cfg.mediamtx.config, cfg.mediamtx.extra_args)
        probe = make_tcp_probe(cfg.server.host, cfg.server.port)
        if not wait_port_ready(timeout_sec=cfg.mediamtx.ready_timeout_sec, probe=probe):
            if mediamtx_proc:
                stop_mediamtx(mediamtx_proc)
            raise RuntimeError("mediamtx not ready")

    def popen_factory(argv: list[str]) -> subprocess.Popen:
        return subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    mgr = StreamManager(popen_factory=popen_factory, sleep=lambda sec: time.sleep(sec))
    mgr.start_all(cfg)

    try:
        while True:
            mgr.tick()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        if mediamtx_proc:
            stop_mediamtx(mediamtx_proc)

    return 0

