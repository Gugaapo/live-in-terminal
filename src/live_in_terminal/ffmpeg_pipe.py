"""Spawn ffmpeg to decode a stream into raw RGB24 frames."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Iterator


@dataclass
class FrameSource:
    """Readable RGB24 frame stream from ffmpeg."""

    process: subprocess.Popen[bytes]
    width: int
    height: int

    @property
    def frame_bytes(self) -> int:
        return self.width * self.height * 3

    def frames(self) -> Iterator[bytes]:
        assert self.process.stdout is not None
        size = self.frame_bytes
        while True:
            buf = self.process.stdout.read(size)
            if not buf or len(buf) < size:
                break
            yield buf

    def close(self) -> None:
        if self.process.stdout:
            try:
                self.process.stdout.close()
            except OSError:
                pass
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)

    def __enter__(self) -> FrameSource:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def open_rgb_pipe(
    stream_url: str,
    width: int,
    height: int,
    fps: float,
    ffmpeg_path: str = "ffmpeg",
) -> FrameSource:
    """
    Start ffmpeg reading stream_url and writing raw rgb24 frames to stdout.

    width/height are the ASCII cell grid (one pixel per character).
    """
    if width < 1 or height < 1:
        raise ValueError("width and height must be >= 1")

    # Twitch HLS often needs a browser-like UA; streamlink URLs may already embed tokens.
    headers = "User-Agent: Mozilla/5.0\r\n"

    cmd = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-headers",
        headers,
        "-re",
        "-i",
        stream_url,
        "-an",
        "-vf",
        f"fps={fps},scale={width}:{height}:flags=fast_bilinear",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "pipe:1",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=width * height * 3 * 2,
    )
    return FrameSource(process=proc, width=width, height=height)
