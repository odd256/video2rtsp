from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import tomllib


RtspTransport = Literal["tcp", "udp"]
SourceType = Literal["file", "playlist"]
PlaylistMode = Literal["sequential", "random"]
VideoCodec = Literal["copy", "libx264"]
AudioCodec = Literal["copy", "aac"]


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int


@dataclass(frozen=True)
class MediaMTXConfig:
    auto_start: bool
    bin: str
    config: str
    ready_timeout_sec: int
    extra_args: list[str]


@dataclass(frozen=True)
class DefaultsConfig:
    loop: bool
    realtime: bool
    rtsp_transport: RtspTransport
    restart_on_exit: bool
    restart_backoff_sec: int
    ffmpeg_bin: str
    log_ffmpeg: bool
    global_args: list[str]


@dataclass(frozen=True)
class SourceConfig:
    type: SourceType
    file: str | None
    files: list[str] | None
    mode: PlaylistMode | None


@dataclass(frozen=True)
class OutputConfig:
    video_codec: VideoCodec
    audio_codec: AudioCodec
    rtsp_url_override: str | None


@dataclass(frozen=True)
class FfmpegConfig:
    bin: str | None
    input_args: list[str]
    output_args: list[str]


@dataclass(frozen=True)
class StreamConfig:
    name: str
    path: str
    enabled: bool
    loop: bool
    realtime: bool
    rtsp_transport: RtspTransport
    restart_on_exit: bool
    restart_backoff_sec: int
    source: SourceConfig
    output: OutputConfig
    ffmpeg: FfmpegConfig


@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig
    mediamtx: MediaMTXConfig | None
    defaults: DefaultsConfig
    streams: list[StreamConfig]


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path)
    with path.open("rb") as f:
        data = tomllib.load(f)
    return _parse_config_dict(data)


def load_config_from_str(toml_text: str) -> AppConfig:
    data = tomllib.loads(toml_text)
    return _parse_config_dict(data)


def _parse_config_dict(data: dict) -> AppConfig:
    server = _parse_server(data.get("server") or {})
    mediamtx = _parse_mediamtx(data.get("mediamtx"))
    defaults = _parse_defaults(data.get("defaults") or {})
    streams = [_parse_stream(item, defaults) for item in (data.get("streams") or [])]
    return AppConfig(server=server, mediamtx=mediamtx, defaults=defaults, streams=streams)


def _parse_server(data: dict) -> ServerConfig:
    host = str(data.get("host") or "127.0.0.1")
    port = int(data.get("port") or 8554)
    return ServerConfig(host=host, port=port)


def _parse_mediamtx(data: dict | None) -> MediaMTXConfig | None:
    if not data:
        return None
    auto_start = bool(data.get("auto_start", True))
    bin_path = str(data.get("bin") or "tools/mediamtx.exe")
    config_path = str(data.get("config") or "tools/mediamtx.yml")
    ready_timeout_sec = int(data.get("ready_timeout_sec") or 10)
    extra_args = list(data.get("extra_args") or [])
    return MediaMTXConfig(
        auto_start=auto_start,
        bin=bin_path,
        config=config_path,
        ready_timeout_sec=ready_timeout_sec,
        extra_args=extra_args,
    )


def _parse_defaults(data: dict) -> DefaultsConfig:
    loop = bool(data.get("loop", True))
    realtime = bool(data.get("realtime", True))
    rtsp_transport = str(data.get("rtsp_transport") or "tcp")
    restart_on_exit = bool(data.get("restart_on_exit", True))
    restart_backoff_sec = int(data.get("restart_backoff_sec") or 2)
    ffmpeg_bin = str(data.get("ffmpeg_bin") or "ffmpeg")
    log_ffmpeg = bool(data.get("log_ffmpeg", True))
    global_args = list(data.get("global_args") or [])
    return DefaultsConfig(
        loop=loop,
        realtime=realtime,
        rtsp_transport=rtsp_transport,  # type: ignore[arg-type]
        restart_on_exit=restart_on_exit,
        restart_backoff_sec=restart_backoff_sec,
        ffmpeg_bin=ffmpeg_bin,
        log_ffmpeg=log_ffmpeg,
        global_args=global_args,
    )


def _parse_stream(data: dict, defaults: DefaultsConfig) -> StreamConfig:
    name = str(data["name"])
    path = str(data["path"])
    enabled = bool(data.get("enabled", True))
    loop = bool(data.get("loop", defaults.loop))
    realtime = bool(data.get("realtime", defaults.realtime))
    rtsp_transport = str(data.get("rtsp_transport") or defaults.rtsp_transport)
    restart_on_exit = bool(data.get("restart_on_exit", defaults.restart_on_exit))
    restart_backoff_sec = int(data.get("restart_backoff_sec") or defaults.restart_backoff_sec)

    source = _parse_source(data.get("source") or {})
    output = _parse_output(data.get("output") or {})
    ffmpeg = _parse_ffmpeg(data.get("ffmpeg") or {})

    return StreamConfig(
        name=name,
        path=path,
        enabled=enabled,
        loop=loop,
        realtime=realtime,
        rtsp_transport=rtsp_transport,  # type: ignore[arg-type]
        restart_on_exit=restart_on_exit,
        restart_backoff_sec=restart_backoff_sec,
        source=source,
        output=output,
        ffmpeg=ffmpeg,
    )


def _parse_source(data: dict) -> SourceConfig:
    source_type = str(data.get("type") or "file")
    if source_type == "file":
        return SourceConfig(type="file", file=str(data.get("file") or ""), files=None, mode=None)
    files = list(data.get("files") or [])
    mode = str(data.get("mode") or "sequential")
    return SourceConfig(type="playlist", file=None, files=[str(x) for x in files], mode=mode)  # type: ignore[arg-type]


def _parse_output(data: dict) -> OutputConfig:
    video_codec = str(data.get("video_codec") or "copy")
    audio_codec = str(data.get("audio_codec") or "copy")
    rtsp_url_override = data.get("rtsp_url_override")
    return OutputConfig(
        video_codec=video_codec,  # type: ignore[arg-type]
        audio_codec=audio_codec,  # type: ignore[arg-type]
        rtsp_url_override=str(rtsp_url_override) if rtsp_url_override else None,
    )


def _parse_ffmpeg(data: dict) -> FfmpegConfig:
    bin_path = data.get("bin")
    input_args = list(data.get("input_args") or [])
    output_args = list(data.get("output_args") or [])
    return FfmpegConfig(
        bin=str(bin_path) if bin_path else None,
        input_args=[str(x) for x in input_args],
        output_args=[str(x) for x in output_args],
    )

