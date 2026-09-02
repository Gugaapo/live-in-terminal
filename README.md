# live-in-terminal

Watch a **live Twitch stream** as colored pixel art in your terminal — the same half-block / background-color technique used by [pokemon-terminal-art](https://github.com/shinya/pokemon-terminal-art).

Works on **Linux** (`watch.sh`) and **Windows** (`watch.ps1`) via a shared Python core.

## Showcase

[Mount](https://www.twitch.tv/mount) on the GeoGuessr World Championship — pixel art + live chat, recorded with `--record`:

[![Mount GeoGuessr World Championship showcase](./showcase_mount-geoguessr.mp4)](./showcase_mount-geoguessr.mp4)

## How it works

1. **streamlink** (preferred) or **yt-dlp** resolves `https://twitch.tv/<channel>` to an HLS URL  
2. **ffmpeg** decodes frames to raw RGB  
3. Python renders each frame with **256-color ANSI** (default), optional **24-bit truecolor**, or legacy ASCII  
4. **Compact** mode uses Unicode half-blocks (`▀`) — two pixel rows per terminal row, like pokemon-terminal-art's compact style  
5. **Blocks** mode uses colored background spaces (two per pixel), like pokemon-terminal-art's normal style  

Latency is typically a few seconds (HLS). Aim for ~8–15 FPS depending on terminal size and CPU.

## Requirements

| Dependency | Role |
|------------|------|
| Python 3.10+ | Player |
| [ffmpeg](https://ffmpeg.org/) | Decode video / optional MP4 recording |
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

Use [Windows Terminal](https://aka.ms/terminal) for reliable ANSI / 256-color output.

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
./watch.sh oMeiaUm
./watch.sh https://www.twitch.tv/oMeiaUm --fps 12 --quality 480p
./watch.sh oMeiaUm --mode blocks --color
./watch.sh oMeiaUm --mode ascii --no-color
./watch.sh oMeiaUm --quality 720p --fps 15 --decode 240x72
./watch.sh mount --record showcase.mp4
```

**Windows (PowerShell):**

```powershell
.\watch.ps1 oMeiaUm
.\watch.ps1 oMeiaUm --fps 10 --mode compact
.\watch.ps1 https://www.twitch.tv/oMeiaUm --quality 720p
.\watch.ps1 oMeiaUm --quality 720p --fps 15 --decode 240x72
.\watch.ps1 mount --record showcase.mp4
```

**Direct module:**

```bash
python -m live_in_terminal oMeiaUm --fps 12
# after pip install -e .:
live-in-terminal oMeiaUm
lit oMeiaUm
```

### Options

| Flag | Description |
|------|-------------|
| `--fps N` | Target FPS (default `12`, capped 1–30) |
| `--width N` | Terminal width in characters (default: terminal width) |
| `--mode` | `compact` (half-block ▀, default), `blocks` (colored spaces), or `ascii` (legacy) |
| `--decode WxH` | ffmpeg decode grid before resample (default `160x48`; try `240x72` or `320x90` for fullscreen) |
| `--quality` | `best`, `worst`, `1080p`, `720p`, `480p`, `360p`, `160p` |
| `--chars` | Charset for `--mode ascii`: `classic`, `blocks`, or custom ramp |
| `--no-color` | Grayscale block density (no ANSI colors) |
| `--color` | 24-bit truecolor instead of 256-color palette |
| `--no-chat` | Hide Twitch chat under the video |
| `--chat-lines N` | Chat rows under the video (default `5`) |
| `--record [PATH]` | Record pixel-art output (with chat) to an MP4 via ffmpeg (default: `<channel>_<timestamp>.mp4`) |
| `--record-scale N` | Pixels per art pixel in the recording (default `8`) |

Exit with **Ctrl+C**. If the channel is offline, you get a clear error.

## Render modes

| Mode | Technique | Looks like |
|------|-----------|------------|
| **compact** (default) | `▀` half-blocks, fg/bg ANSI colors | [pokemon-terminal-art compact](https://github.com/shinya/pokemon-terminal-art) |
| **blocks** | Two colored spaces per pixel | [pokemon-terminal-art normal](https://github.com/shinya/pokemon-terminal-art) |
| **ascii** | Character density ramp | Original live-in-terminal style |

## Chat

Live chat is on by default: the last **5** messages appear under the status line (anonymous Twitch IRC — no login). Use `--no-chat` to disable, or `--chat-lines 8` for more rows.

## Recording

Use `--record` to save what you see (pixel art + status + chat) to an MP4 without OBS:

```bash
./watch.sh mount --record
./watch.sh mount --record my_clip.mp4 --record-scale 12
```

Press **Ctrl+C** to stop; the file is finalized automatically. Recording dimensions are locked at session start.

## Notes

- Video only in v1 (no audio).  
- Legacy Windows `conhost` may show poor colors; prefer Windows Terminal.  
- Lower `--quality` / `--fps` / `--width` if the terminal cannot keep up.  
- Resizing the window is supported: frames are decoded at a fixed grid (`--decode`) and resampled to the live terminal size (no stream restart). While `--record` is active, layout stays locked so the MP4 stays stable.  
- For sharper fullscreen, raise `--decode` (e.g. `240x72`) and `--quality 720p`; higher values cost more CPU.  
