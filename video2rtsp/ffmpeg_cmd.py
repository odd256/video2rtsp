from __future__ import annotations

from video2rtsp.config import AppConfig, StreamConfig


def build_rtsp_url(cfg: AppConfig, stream: StreamConfig) -> str:
    if stream.output.rtsp_url_override:
        return stream.output.rtsp_url_override
    return f"rtsp://{cfg.server.host}:{cfg.server.port}/{stream.path}"


def build_ffmpeg_argv(cfg: AppConfig, stream: StreamConfig, current_input_file: str) -> list[str]:
    bin_path = stream.ffmpeg.bin or cfg.defaults.ffmpeg_bin
    argv: list[str] = [bin_path]

    argv.extend(cfg.defaults.global_args)

    if stream.realtime:
        argv.append("-re")

    argv.extend(stream.ffmpeg.input_args)

    if stream.source.type == "file" and stream.loop:
        argv.extend(["-stream_loop", "-1"])

    argv.extend(["-i", current_input_file])

    argv.extend(["-rtsp_transport", stream.rtsp_transport])

    argv.extend(["-c:v", stream.output.video_codec])
    argv.extend(["-c:a", stream.output.audio_codec])

    argv.extend(stream.ffmpeg.output_args)

    argv.append(build_rtsp_url(cfg, stream))
    return argv

