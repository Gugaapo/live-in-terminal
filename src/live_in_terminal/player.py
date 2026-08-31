"""Playback loop: resolve stream, decode frames, render ASCII + chat."""

from __future__ import annotations

import shutil
import sys
import time
from dataclasses import dataclass

from live_in_terminal.ascii import frame_to_ascii, resolve_charset, supports_truecolor
from live_in_terminal.chat import TwitchChat, format_chat_block
from live_in_terminal.ffmpeg_pipe import FrameSource, open_rgb_pipe
from live_in_terminal.stream import StreamResolveError, require_ffmpeg, resolve_stream_url

HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CURSOR_HOME = "\x1b[H"
CLEAR_SCREEN = "\x1b[2J"
CLEAR_EOS = "\x1b[0J"  # clear from cursor to end of screen
ALT_ENTER = "\x1b[?1049h"
ALT_LEAVE = "\x1b[?1049l"
WRAP_OFF = "\x1b[?7l"  # prevent resize wrap from shredding the frame
WRAP_ON = "\x1b[?7h"

DEFAULT_CHAT_LINES = 5


def _enable_windows_ansi() -> None:
    """Enable VT processing on Windows consoles so ANSI escapes work."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        pass


@dataclass
class PlayerOptions:
    channel_or_url: str
    fps: float = 12.0
    width: int | None = None
    quality: str = "best"
    chars: str = "classic"
    color: bool | None = None  # None = auto
    use_alt_screen: bool = True
    chat: bool = True
    chat_lines: int = DEFAULT_CHAT_LINES


def _layout(
    opt_width: int | None,
    chat: bool,
    chat_lines: int,
) -> tuple[int, int]:
    """
    Returns (cols, video_rows) for the current terminal size.

    Reserves 1 status line and optional chat rows below the video.
    """
    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    cols = max(2, cols)
    if opt_width is not None:
        cols = max(2, min(cols, opt_width))

    below = 1  # status
    if chat:
        below += max(1, chat_lines)

    video_rows = max(2, rows - below)
    return cols, video_rows


def _render_frame(
    out,
    *,
    rgb: bytes,
    width: int,
    height: int,
    charset: str,
    use_color: bool,
    channel: str,
    fps: float,
    chat_client: TwitchChat | None,
    chat_lines: int,
) -> None:
    art = frame_to_ascii(rgb, width, height, chars=charset, color=use_color)
    chat_note = ""
    if chat_client is not None:
        st = chat_client.status
        if st and st != "chat live":
            chat_note = f" | {st}"
    status = f"{channel} | {width}x{height} @ {fps:.0f}fps{chat_note} | Ctrl+C quit"
    if len(status) > width:
        status = status[: max(1, width - 1)] + "…"

    parts = [CURSOR_HOME, art, "\n", status]
    if chat_client is not None:
        block = format_chat_block(
            chat_client.latest(),
            width=width,
            lines=chat_lines,
            color=use_color,
            placeholder="",
        )
        parts.extend(["\n", block])
    # Wipe any leftover cells when the previous frame was larger.
    parts.append(CLEAR_EOS)
    out.write("".join(parts))
    out.flush()


def _drain_stderr(src: FrameSource) -> bytes:
    if not src.process.stderr:
        return b""
    try:
        return src.process.stderr.read() or b""
    except OSError:
        return b""


def play(options: PlayerOptions) -> int:
    """Run the player until EOF, stream end, or KeyboardInterrupt. Returns exit code."""
    try:
        ffmpeg = require_ffmpeg()
        channel, stream_url = resolve_stream_url(options.channel_or_url, options.quality)
    except StreamResolveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    chat_lines = max(1, options.chat_lines)
    charset = resolve_charset(options.chars)
    use_color = supports_truecolor() if options.color is None else options.color
    fps = max(1.0, min(30.0, options.fps))

    out = sys.stdout
    entered_alt = False
    wrap_disabled = False
    frames_seen = 0
    ffmpeg_err = b""
    chat_client: TwitchChat | None = None

    try:
        _enable_windows_ansi()
        if options.use_alt_screen and out.isatty():
            out.write(ALT_ENTER)
            entered_alt = True
        if out.isatty():
            out.write(WRAP_OFF)
            wrap_disabled = True
        out.write(HIDE_CURSOR + CLEAR_SCREEN + CURSOR_HOME)
        out.flush()

        if options.chat:
            chat_client = TwitchChat(channel, max_messages=chat_lines)
            chat_client.start()

        frame_interval = 1.0 / fps
        # Outer loop: restart ffmpeg whenever the terminal grid changes.
        while True:
            width, height = _layout(options.width, options.chat, chat_lines)
            resized = False

            with open_rgb_pipe(
                stream_url, width, height, fps, ffmpeg_path=ffmpeg
            ) as src:
                next_deadline = time.perf_counter()
                for rgb in src.frames():
                    new_w, new_h = _layout(options.width, options.chat, chat_lines)
                    if (new_w, new_h) != (width, height):
                        resized = True
                        out.write(CLEAR_SCREEN + CURSOR_HOME)
                        out.flush()
                        break

                    frames_seen += 1
                    now = time.perf_counter()
                    if now < next_deadline:
                        time.sleep(next_deadline - now)
                    next_deadline = time.perf_counter() + frame_interval

                    _render_frame(
                        out,
                        rgb=rgb,
                        width=width,
                        height=height,
                        charset=charset,
                        use_color=use_color,
                        channel=channel,
                        fps=fps,
                        chat_client=chat_client,
                        chat_lines=chat_lines,
                    )

                    if src.process.poll() is not None:
                        break

                ffmpeg_err = _drain_stderr(src) or ffmpeg_err

            if resized:
                # Brief pause so rapid drag-resizes coalesce a bit.
                time.sleep(0.05)
                continue

            # Stream ended (or ffmpeg exited) without a resize.
            break

        if frames_seen == 0:
            msg = ffmpeg_err.decode("utf-8", errors="replace").strip()
            if msg:
                print(f"error: ffmpeg produced no frames: {msg}", file=sys.stderr)
            else:
                print(
                    "error: ffmpeg produced no frames "
                    "(stream may have ended or URL expired).",
                    file=sys.stderr,
                )
            return 1
        return 0
    except KeyboardInterrupt:
        return 0
    except StreamResolveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if chat_client is not None:
            chat_client.stop()
        if out.isatty():
            if wrap_disabled:
                out.write(WRAP_ON)
            if entered_alt:
                out.write(ALT_LEAVE)
            out.write(SHOW_CURSOR)
            out.flush()
