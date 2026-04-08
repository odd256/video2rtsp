from __future__ import annotations

import random
import subprocess
from dataclasses import dataclass
from typing import Literal

from video2rtsp.config import AppConfig, StreamConfig
from video2rtsp.ffmpeg_cmd import build_ffmpeg_argv


@dataclass
class PlaylistCursor:
    files: list[str]
    mode: Literal["sequential", "random"]
    loop: bool

    def __post_init__(self) -> None:
        if len(self.files) == 0:
            raise ValueError("files must not be empty")
        self._order: list[int] = []
        self._pos: int = 0
        self._reset_order()

    def current(self) -> str:
        return self.files[self._order[self._pos]]

    def advance(self) -> None:
        next_pos = self._pos + 1
        if next_pos < len(self._order):
            self._pos = next_pos
            return
        if self.loop:
            self._reset_order()
            self._pos = 0
            return
        raise StopIteration()

    def _reset_order(self) -> None:
        if self.mode == "sequential":
            self._order = list(range(len(self.files)))
        else:
            self._order = list(range(len(self.files)))
            random.shuffle(self._order)


@dataclass
class StreamRuntime:
    cfg: AppConfig
    stream: StreamConfig
    popen_factory: callable
    proc: subprocess.Popen | None = None
    playlist: PlaylistCursor | None = None

    def start(self, current_input_file: str) -> None:
        argv = build_ffmpeg_argv(self.cfg, self.stream, current_input_file=current_input_file)
        self.proc = self.popen_factory(argv)

    def stop(self) -> None:
        if not self.proc:
            return
        self.proc.terminate()
        self.proc = None

    def poll(self) -> int | None:
        if not self.proc:
            return None
        return self.proc.poll()

