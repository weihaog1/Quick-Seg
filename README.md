# Sprite Cutout Creator

A browser-based tool for creating RGBA sprite cutouts from gameplay video. Draw lasso selections around sprites to export them as transparent PNGs, organized by class.

## Install

```bash
pip install -r requirements.txt
```

Requires Python 3.8+.

## Quick Start

```bash
# Interactive setup (opens browser with video upload/selection UI)
python app.py

# Direct mode (skip setup, go straight to annotation)
python app.py --video path/to/video.mp4 --output ./output
```

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--video` | _(none)_ | Path to video file. If both `--video` and `--output` are given, skips the setup page. |
| `--output` | _(none)_ | Output directory for cutout PNGs. |
| `--port` | `5000` | Port to run the server on. |
| `--host` | `0.0.0.0` | Bind address. Use `127.0.0.1` for localhost-only. |
| `--videos-dir` | `.` | Directory to browse for server-side videos on the setup page. |
| `--uploads-dir` | `./uploads` | Directory where uploaded videos are saved. |
| `--no-browser` | _(flag)_ | Don't auto-open the browser on start. Useful for remote/headless servers. |

## Examples

```bash
# Browse videos from a specific directory
python app.py --videos-dir /path/to/gameplay/videos

# Run on a remote server (accessible from other machines)
python app.py --host 0.0.0.0 --no-browser

# Specify everything up front
python app.py --video gameplay.mp4 --output ./sprites --port 8080
```

## Setup Page

When launched without `--video` and `--output`, the app opens a setup page where you can:

- **Upload a video** by dragging and dropping or clicking the upload zone
- **Select a server-side video** from the videos directory
- **Set the output directory** for exported cutouts
- Click **Start Annotating** to begin

## Annotation UI

### Drawing
- **Click and drag** on the frame to draw a lasso around a sprite
- **Right-click** to clear the current drawing
- Release the mouse to see a live preview of the cutout

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `S` | Save the current cutout |
| `Escape` | Clear drawing / close modal |
| `Left/Right` | Previous / next frame |
| `1`-`9` | Set frame skip amount |
| `Scroll` | Zoom in / out |
| `Space` + drag | Pan the view |
| `R` | Reset zoom and pan |
| `Ctrl+Z` | Undo last save |
| `?` | Show all shortcuts |

### Output Format

Cutouts are saved as RGBA PNGs organized by class:

```
output/
  class_name/
    class_name_0_CUSTOM_000.png
    class_name_0_CUSTOM_001.png
    ...
```

Each PNG has transparent background with only the lasso-selected region visible.

## Switching Videos

Click the **Switch Video** link in the header to return to the setup page and select a different video without restarting the server.
