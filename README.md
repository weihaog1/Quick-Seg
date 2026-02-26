# Quick-Seg - Sprite Cutout Creator

A browser-based tool for creating transparent sprite cutouts from gameplay video. Load a video, draw selections around sprites, and export them as RGBA PNGs organized by class.

Created as part of our [CS 175 (Project in AI)](https://royf.org/crs/CS175/W26) course at UC Irvine, Winter 2026. We needed a way to quickly segment sprite cutouts from Clash Royale gameplay footage to build training data for our object detection model, and couldn't find an existing tool that did this well -- so we built one.

## Setup

### Prerequisites

- Python 3.8 or newer

**Windows:** Download from [python.org](https://www.python.org/downloads/). During installation, check **"Add Python to PATH"**. Verify with `python --version` in Command Prompt.

**Mac/Linux:** Python is usually pre-installed. Check with `python3 --version`.

### Install

```
git clone https://github.com/weihaog1/Quick-Seg.git
cd Quick-Seg
pip install -r requirements.txt
```

Or download the ZIP from the GitHub page, extract it, and run `pip install -r requirements.txt` inside the folder.

If `pip` is not recognized, try `python -m pip install -r requirements.txt`.

### Run

```
python app.py
```

Your browser opens to the setup page. From there:

1. **Choose a video** - drag and drop a file onto the upload zone, or pick one from the server list
2. **Set the output folder** - type a path or click **Browse** to navigate your filesystem
3. Click **Start Annotating**

## How to Use

### Drawing Selections

- **Click and drag** on the frame to draw a lasso around a sprite
- Each new lasso **adds to** the existing selection (multiple regions accumulate)
- Press **X** to switch to **subtract mode** - draw over the green area to cut holes out of it
- Press **X** again to go back to **add mode**
- The header shows the current mode (green dot = add, red dot = subtract)
- Subtract regions erase instantly from the green overlay when you release the mouse
- You can add back over a previously subtracted area

### Saving Cutouts

1. Draw your selection (green overlay shows what will be exported)
2. Pick a class from the sidebar, or press **1-8** to quick-select
3. Press **S** to save

The cutout is exported as a transparent PNG into the output folder, organized by class name.

### Navigation

- **Left/Right arrow** keys move between frames
- **Skip input** in the sidebar lets you set a custom frame step (type any number)
- **Save + skip** toggle: when enabled, saving a cutout automatically advances by the skip amount

### Zoom and Pan

- **Alt + scroll** (Option + scroll on Mac) zooms toward your mouse cursor
- **Zoom slider** in the header for precise control
- **Space + drag** to pan the view
- **R** to reset zoom and center the frame

### Switching Videos

Click the **Switch Video** link in the header to go back to the setup page without restarting the server.

### Pen / Stylus Support

Works with Windows pen input and tablet styluses out of the box (uses Pointer Events API).

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `S` | Save cutout |
| `X` | Toggle add / subtract mode |
| `Escape` | Clear all selections (or close modal) |
| `Left` / `Right` | Previous / next frame |
| `1` - `8` | Select class by number |
| `Alt` + `Scroll` | Zoom in / out |
| `Space` + drag | Pan the view |
| `R` | Reset zoom and pan |
| `Ctrl+Z` | Undo last save |
| `?` | Show shortcuts modal |

## Output Format

```
output/
  arrows/
    arrows_0_CUSTOM_000.png
    arrows_0_CUSTOM_001.png
  royal-hogs/
    royal-hogs_0_CUSTOM_000.png
  ...
```

Each PNG has a transparent background. Only the lasso-selected pixels are visible. On first save, all 8 class folders are created automatically:

1. arrows
2. barbarian-barrel
3. electro-spirit
4. flying-machine
5. goblin-cage
6. royal-hogs
7. royal-recruits
8. zappies

You can also create custom classes by typing a new name in the sidebar search box.

## CLI Options

```
python app.py [options]
```

| Option | Default | What it does |
|--------|---------|--------------|
| `--video PATH` | _(none)_ | Video file path. If both `--video` and `--output` are given, skips the setup page. |
| `--output PATH` | _(none)_ | Output directory for saved PNGs. |
| `--port N` | `5000` | Server port. |
| `--host ADDR` | `0.0.0.0` | Bind address. Use `127.0.0.1` for localhost only. |
| `--videos-dir PATH` | `.` | Folder to list server-side videos from on the setup page. |
| `--uploads-dir PATH` | `./uploads` | Where uploaded videos are saved. |
| `--no-browser` | _(flag)_ | Don't auto-open the browser. |

### Examples

```bash
# Default: opens setup page in browser
python app.py

# Skip setup, go straight to annotating
python app.py --video gameplay.mp4 --output ./output

# Point at a folder of videos so they show up in the setup page list
python app.py --videos-dir ~/Videos

# Use a different port
python app.py --port 8080

# Run on a remote machine (access from another device on the network)
python app.py --host 0.0.0.0 --no-browser
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python is not recognized` | Reinstall Python with "Add to PATH" checked, or use the full path to python.exe |
| `pip is not recognized` | Use `python -m pip install -r requirements.txt` |
| Port already in use | Use `--port 8080` or another free port |
| Browser doesn't open | Go to `http://localhost:5000` manually |
| Video won't load | Check the file is .mp4, .avi, .mkv, .mov, or .webm and not corrupted |
| Pen/stylus not working | Make sure you're drawing directly on the canvas area, not the sidebar |
