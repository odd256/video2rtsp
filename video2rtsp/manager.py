from __future__ import annotations

import subprocess
from collections.abc import Callable

from video2rtsp.config import AppConfig
from video2rtsp.stream import PlaylistCursor, StreamRuntime


PopenFactory = Callable[[list[str]], subprocess.Popen]
SleepFn = Callable[[int], None]


class StreamManager:
    def __init__(self, popen_factory: PopenFactory, sleep: SleepFn):
        self._popen_factory = popen_factory
        self._sleep = sleep
        self._runtimes: list[StreamRuntime] = []

    def start_all(self, cfg: AppConfig) -> None:
        self._runtimes = []
        for s in cfg.streams:
            if not s.enabled:
                continue
            runtime = StreamRuntime(cfg=cfg, stream=s, popen_factory=self._popen_factory)
            if s.source.type == "playlist":
                cursor = PlaylistCursor(
                    files=list(s.source.files or []),
                    mode=s.source.mode or "sequential",
                    loop=s.loop,
                )
                runtime.playlist = cursor
                runtime.start(current_input_file=cursor.current())
            else:
                runtime.start(current_input_file=str(s.source.file or ""))
            self._runtimes.append(runtime)

    def tick(self) -> None:
        for rt in self._runtimes:
            if not rt.proc:
                continue
            exit_code = rt.proc.poll()
            if exit_code is None:
                continue

            if rt.stream.source.type == "playlist":
                if not rt.playlist:
                    rt.proc = None
                    continue
                try:
                    rt.playlist.advance()
                except StopIteration:
                    rt.proc = None
                    continue
                rt.start(current_input_file=rt.playlist.current())
                continue

            if exit_code == 0 and not rt.stream.loop:
                rt.proc = None
                continue

            if rt.stream.restart_on_exit:
                self._sleep(rt.stream.restart_backoff_sec)
                rt.start(current_input_file=str(rt.stream.source.file or ""))
            else:
                rt.proc = None

