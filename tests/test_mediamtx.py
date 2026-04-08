import unittest


class TestMediaMTX(unittest.TestCase):
    def test_wait_port_ready_uses_probe(self):
        from video2rtsp.mediamtx import wait_port_ready

        calls: list[int] = []

        def probe() -> bool:
            calls.append(1)
            return len(calls) >= 3

        ok = wait_port_ready(timeout_sec=1, probe=probe, sleep=lambda s: None)
        self.assertTrue(ok)
        self.assertGreaterEqual(len(calls), 3)

