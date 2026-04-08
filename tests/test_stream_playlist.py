import unittest


class TestPlaylistCursor(unittest.TestCase):
    def test_sequential_loop_wraps(self):
        from video2rtsp.stream import PlaylistCursor

        c = PlaylistCursor(files=["a.mp4", "b.mp4"], mode="sequential", loop=True)
        self.assertEqual(c.current(), "a.mp4")
        c.advance()
        self.assertEqual(c.current(), "b.mp4")
        c.advance()
        self.assertEqual(c.current(), "a.mp4")

