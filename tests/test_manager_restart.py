import unittest


class TestManagerRestart(unittest.TestCase):
    def test_restart_on_exit_respects_backoff(self):
        from video2rtsp.config import (
            AppConfig,
            DefaultsConfig,
            FfmpegConfig,
            OutputConfig,
            ServerConfig,
            SourceConfig,
            StreamConfig,
        )
        from video2rtsp.manager import StreamManager

        sleeps: list[int] = []

        def sleep(sec: int) -> None:
            sleeps.append(sec)

        class P:
            def poll(self):
                return 1

            def terminate(self):
                return None

            def kill(self):
                return None

        popen_calls: list[list[str]] = []

        def popen_factory(argv: list[str]):
            popen_calls.append(argv)
            return P()

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
            streams=[
                StreamConfig(
                    name="s1",
                    path="live/s1",
                    enabled=True,
                    loop=True,
                    realtime=True,
                    rtsp_transport="tcp",
                    restart_on_exit=True,
                    restart_backoff_sec=3,
                    source=SourceConfig(type="file", file="D:/videos/a.mp4", files=None, mode=None),
                    output=OutputConfig(video_codec="copy", audio_codec="copy", rtsp_url_override=None),
                    ffmpeg=FfmpegConfig(bin=None, input_args=[], output_args=[]),
                )
            ],
        )

        mgr = StreamManager(popen_factory=popen_factory, sleep=sleep)
        mgr.start_all(cfg)
        self.assertEqual(len(popen_calls), 1)

        mgr.tick()

        self.assertEqual(sleeps, [3])
        self.assertEqual(len(popen_calls), 2)

