import unittest


class TestValidate(unittest.TestCase):
    def test_duplicate_path_rejected(self):
        from video2rtsp.config import load_config_from_str
        from video2rtsp.validate import ConfigError, validate_config

        toml_text = """
[server]
host="127.0.0.1"
port=8554

[defaults]
loop=true
realtime=true
rtsp_transport="tcp"
restart_on_exit=true
restart_backoff_sec=1
ffmpeg_bin="ffmpeg"
log_ffmpeg=true
global_args=[]

[[streams]]
name="a"
path="live/x"
[streams.source]
type="file"
file="D:/videos/a.mp4"

[[streams]]
name="b"
path="live/x"
[streams.source]
type="file"
file="D:/videos/b.mp4"
"""
        cfg = load_config_from_str(toml_text)
        with self.assertRaises(ConfigError):
            validate_config(cfg, file_exists=lambda p: True)

