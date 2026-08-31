"""Convert RGB24 frames to ASCII (optionally with truecolor ANSI)."""

from __future__ import annotations

DEFAULT_CHARS = " .:-=+*#%@"
BLOCKS_CHARS = " ░▒▓█"
BRAILLE_HINT = "braille"  # reserved label; ramp still used for density


def supports_truecolor() -> bool:
    import os
    import sys

    if not sys.stdout.isatty():
        return False
    colorterm = (os.environ.get("COLORTERM") or "").lower()
    if colorterm in {"truecolor", "24bit"}:
        return True
    # Windows Terminal and modern ConPTY generally handle truecolor.
    if os.name == "nt":
        return bool(
            os.environ.get("WT_SESSION")
            or os.environ.get("TERM_PROGRAM")
            or (os.environ.get("TERM") or "").lower() in {"xterm-256color", "xterm-truecolor"}
        )
    term = (os.environ.get("TERM") or "").lower()
    return "truecolor" in term or "256color" in term or term in {"xterm-kitty", "alacritty"}


def _luminance(r: int, g: int, b: int) -> float:
    # Rec. 601 luma
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def resize_rgb(rgb: bytes, src_w: int, src_h: int, dst_w: int, dst_h: int) -> bytes:
    """Nearest-neighbor resize of an RGB24 buffer."""
    if src_w < 1 or src_h < 1 or dst_w < 1 or dst_h < 1:
        raise ValueError("dimensions must be >= 1")
    if src_w == dst_w and src_h == dst_h:
        return rgb
    expected = src_w * src_h * 3
    if len(rgb) < expected:
        raise ValueError("rgb buffer shorter than src dimensions")

    out = bytearray(dst_w * dst_h * 3)
    for y in range(dst_h):
        sy = (y * src_h) // dst_h
        src_row = sy * src_w * 3
        dst_row = y * dst_w * 3
        for x in range(dst_w):
            sx = (x * src_w) // dst_w
            si = src_row + sx * 3
            di = dst_row + x * 3
            out[di] = rgb[si]
            out[di + 1] = rgb[si + 1]
            out[di + 2] = rgb[si + 2]
    return bytes(out)


def frame_to_ascii(
    rgb: bytes,
    width: int,
    height: int,
    chars: str = DEFAULT_CHARS,
    color: bool = True,
) -> str:
    """Map one RGB24 frame to a multi-line ASCII string."""
    if len(chars) < 2:
        chars = DEFAULT_CHARS
    n = len(chars) - 1
    lines: list[str] = []
    idx = 0
    reset = "\x1b[0m" if color else ""

    for _y in range(height):
        parts: list[str] = []
        for _x in range(width):
            r = rgb[idx]
            g = rgb[idx + 1]
            b = rgb[idx + 2]
            idx += 3
            lum = _luminance(r, g, b)
            ch = chars[min(n, int(lum * n + 0.5))]
            if color:
                parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
            else:
                parts.append(ch)
        line = "".join(parts)
        if color:
            line += reset
        lines.append(line)

    return "\n".join(lines)


def resolve_charset(name: str | None) -> str:
    if not name or name.lower() in {"classic", "default"}:
        return DEFAULT_CHARS
    if name.lower() in {"blocks", "block"}:
        return BLOCKS_CHARS
    # Treat as custom character ramp (dark → bright).
    return name
