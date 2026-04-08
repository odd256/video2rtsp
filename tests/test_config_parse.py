import unittest


class TestConfigParse(unittest.TestCase):
    def test_defaults_applied(self):
        from video2rtsp.config import load_config_from_str

        toml_text = """
[server]
host = "127.0.0.1"
port = 8554

[defaults]
loop = true
realtime = true
rtsp_transport = "tcp"
restart_on_exit = true
restart_backoff_sec = 2
ffmpeg_bin = "ffmpeg"
log_ffmpeg = true
global_args = []

[[streams]]
name = "s1"
path = "live/s1"

[streams.source]
type = "file"
file = "D:/videos/a.mp4"
"""
        cfg = load_config_from_str(toml_text)
        s1 = cfg.streams[0]
        self.assertEqual(cfg.server.port, 8554)
        self.assertTrue(s1.loop)
        self.assertEqual(s1.rtsp_transport, "tcp")

