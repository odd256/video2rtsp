import unittest


class TestCli(unittest.TestCase):
    def test_parse_config_path(self):
        from video2rtsp.cli import parse_args

        args = parse_args(["run", "-c", "video2rtsp.toml"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.config, "video2rtsp.toml")

