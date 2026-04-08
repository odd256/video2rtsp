import unittest


class TestFfmpegCmd(unittest.TestCase):
    def test_file_loop_includes_stream_loop(self):
        from video2rtsp.config import (
            AppConfig,
            DefaultsConfig,
            FfmpegConfig,
            OutputConfig,
            ServerConfig,
            SourceConfig,
            StreamConfig,
        )
        from video2rtsp.ffmpeg_cmd import build_ffmpeg_argv

        cfg = AppConfig(
            server=ServerConfig(host="127.0.0.1", port=8554),
            mediamtx=None,
            defaults=DefaultsConfig(
                loop=True,
                realtime=True,
                rtsp_transport="tcp",
                restart_on_exit=True,
                restart_backoff_sec=2,
                ffmpeg_bin="ffmpeg",
                log_ffmpeg=True,
                global_args=[],
            ),
            streams=[],
        )
        s = StreamConfig(
            name="s1",
            path="live/s1",
            enabled=True,
            loop=True,
            realtime=True,
            rtsp_transport="tcp",
            restart_on_exit=True,
            restart_backoff_sec=2,
            source=SourceConfig(type="file", file="D:/videos/a.mp4", files=None, mode=None),
            output=OutputConfig(video_codec="copy", audio_codec="copy", rtsp_url_override=None),
            ffmpeg=FfmpegConfig(bin=None, input_args=[], output_args=[]),
        )
        argv = build_ffmpeg_argv(cfg, s, current_input_file="D:/videos/a.mp4")
        self.assertIn("-stream_loop", argv)
        self.assertIn("-1", argv)
        self.assertIn("rtsp://127.0.0.1:8554/live/s1", argv)

