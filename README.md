# live-in-terminal

Watch a **live Twitch stream** as ASCII art in your terminal (color when supported).

Works on **Linux** (`watch.sh`) and **Windows** (`watch.ps1`) via a shared Python core.

## How it works

1. **streamlink** (preferred) or **yt-dlp** resolves `https://twitch.tv/<channel>` to an HLS URL  
2. **ffmpeg** decodes frames to raw RGB  
3. Python maps pixels to characters (optional truecolor ANSI) and redraws the terminal  

Latency is typically a few seconds (HLS). Aim for ~8–15 FPS depending on terminal size and CPU.

## Requirements

| Dependency | Role |
|------------|------|
| Python 3.10+ | Player |
| [ffmpeg](https://ffmpeg.org/) | Decode video |
| [streamlink](https://streamlink.github.io/) **or** [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Resolve Twitch live URL |

No Twitch API key is required for public live streams.

### Install helpers

**Linux (Debian/Ubuntu example):**

```bash
sudo apt update
sudo apt install -y python3 ffmpeg
pipx install streamlink   # or: pip install --user streamlink
```

**Windows:**

```powershell
winget install Gyan.FFmpeg
pip install streamlink
# or: pip install yt-dlp
```

Use [Windows Terminal](https://aka.ms/terminal) for reliable ANSI / truecolor.

## Setup

From the repo root (recommended: virtualenv):

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install -e .
python -m pip install streamlink   # or: yt-dlp
```

Or skip `pip install -e .` and use the launchers (they set `PYTHONPATH=src` when the package is not installed). Activate the venv first so `streamlink` is available to the player.
## Usage

**Linux / macOS / WSL:**

```bash
chmod +x watch.sh
./watch.sh shroud
./watch.sh https://www.twitch.tv/shroud --fps 12 --quality 480p
./watch.sh shroud --no-color --chars blocks
```

**Windows (PowerShell):**

```powershell
.\watch.ps1 shroud
.\watch.ps1 shroud --fps 10 --no-color
.\watch.ps1 https://www.twitch.tv/shroud --quality 720p
```

**Direct module:**

```bash
python -m live_in_terminal shroud --fps 12
# after pip install -e .:
live-in-terminal shroud
lit shroud
```

### Options

| Flag | Description |
|------|-------------|
| `--fps N` | Target FPS (default `12`, capped 1–30) |
| `--width N` | ASCII width in characters (default: terminal width) |
| `--quality` | `best`, `worst`, `1080p`, `720p`, `480p`, `360p`, `160p` |
| `--chars` | `classic`, `blocks`, or a custom dark→bright ramp |
| `--no-color` | Grayscale characters only |
| `--color` | Force truecolor ANSI |
| `--no-chat` | Hide Twitch chat under the video |
| `--chat-lines N` | Chat rows under the video (default `5`) |

Exit with **Ctrl+C**. If the channel is offline, you get a clear error.

## Chat

Live chat is on by default: the last **5** messages appear under the status line (anonymous Twitch IRC — no login). Use `--no-chat` to disable, or `--chat-lines 8` for more rows.

## Notes

- Video only in v1 (no audio).  
- Legacy Windows `conhost` may show poor colors; prefer Windows Terminal.  
- Lower `--quality` / `--fps` / `--width` if the terminal cannot keep up.  
