"""CLI entry for live-in-terminal."""

from __future__ import annotations

import argparse
import sys

from live_in_terminal import __version__
from live_in_terminal.player import (
    DECODE_HEIGHT,
    DECODE_WIDTH,
    PlayerOptions,
    parse_decode_size,
    play,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="live-in-terminal",
        description="Watch a live Twitch stream as ASCII art in your terminal.",
    )
    p.add_argument(
        "channel",
        help="Twitch channel name or URL (e.g. shroud or https://www.twitch.tv/shroud)",
    )
    p.add_argument(
        "--fps",
        type=float,
        default=12.0,
        help="Target frames per second (default: 12)",
    )
    p.add_argument(
        "--width",
        type=int,
        default=None,
        help="ASCII width in characters (default: full terminal width)",
    )
    p.add_argument(
        "--quality",
        default="best",
        help="Stream quality: best, worst, 1080p, 720p, 480p, 360p, 160p (default: best)",
    )
    p.add_argument(
        "--chars",
        default="classic",
        help="Charset: classic, blocks, or a custom dark-to-bright ramp string",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        help="Disable truecolor ANSI (grayscale characters only)",
    )
    p.add_argument(
        "--color",
        action="store_true",
        help="Force truecolor ANSI even if auto-detect is unsure",
    )
    p.add_argument(
        "--decode",
        default=f"{DECODE_WIDTH}x{DECODE_HEIGHT}",
        metavar="WxH",
        help=(
            f"ffmpeg decode grid before terminal resample "
            f"(default: {DECODE_WIDTH}x{DECODE_HEIGHT}; try 240x72 for fullscreen)"
        ),
    )
    p.add_argument(
        "--no-chat",
        action="store_true",
        help="Hide Twitch chat under the video",
    )
    p.add_argument(
        "--chat-lines",
        type=int,
        default=5,
        help="Number of chat messages shown below the video (default: 5)",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.no_color and args.color:
        parser.error("use only one of --color / --no-color")
    if args.chat_lines < 1:
        parser.error("--chat-lines must be >= 1")

    try:
        decode_w, decode_h = parse_decode_size(args.decode)
    except ValueError as exc:
        parser.error(f"--decode: {exc}")

    color: bool | None
    if args.no_color:
        color = False
    elif args.color:
        color = True
    else:
        color = None

    options = PlayerOptions(
        channel_or_url=args.channel,
        fps=args.fps,
        width=args.width,
        quality=args.quality,
        chars=args.chars,
        color=color,
        chat=not args.no_chat,
        chat_lines=args.chat_lines,
        decode_width=decode_w,
        decode_height=decode_h,
    )
    return play(options)


if __name__ == "__main__":
    sys.exit(main())
