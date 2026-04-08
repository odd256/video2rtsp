from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from video2rtsp.config import AppConfig


class ConfigError(ValueError):
    pass


def validate_config(cfg: AppConfig, file_exists: Callable[[str], bool] | None = None) -> None:
    exists = file_exists or (lambda p: Path(p).exists())

    if cfg.server.port < 1 or cfg.server.port > 65535:
        raise ConfigError(f"server.port out of range: {cfg.server.port}")

    seen_names: set[str] = set()
    seen_paths: set[str] = set()

    for s in cfg.streams:
        if s.name in seen_names:
            raise ConfigError(f"duplicate stream name: {s.name}")
        seen_names.add(s.name)

        if s.path in seen_paths:
            raise ConfigError(f"duplicate stream path: {s.path}")
        seen_paths.add(s.path)

        if s.enabled:
            if s.source.type == "file":
                if not s.source.file:
                    raise ConfigError(f"stream {s.name} source.file is required")
                if not exists(s.source.file):
                    raise ConfigError(f"stream {s.name} source.file not found: {s.source.file}")
            else:
                if not s.source.files:
                    raise ConfigError(f"stream {s.name} source.files is required")
                if len(s.source.files) == 0:
                    raise ConfigError(f"stream {s.name} source.files is empty")
                for f in s.source.files:
                    if not exists(f):
                        raise ConfigError(f"stream {s.name} source file not found: {f}")

        if s.rtsp_transport not in ("tcp", "udp"):
            raise ConfigError(f"stream {s.name} rtsp_transport invalid: {s.rtsp_transport}")

        if s.restart_backoff_sec < 0:
            raise ConfigError(f"stream {s.name} restart_backoff_sec must be >= 0")

    if cfg.mediamtx and cfg.mediamtx.auto_start:
        if not exists(cfg.mediamtx.bin):
            raise ConfigError(f"mediamtx.bin not found: {cfg.mediamtx.bin}")
        if not exists(cfg.mediamtx.config):
            raise ConfigError(f"mediamtx.config not found: {cfg.mediamtx.config}")

