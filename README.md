# Sprite Cutout Creator

A browser-based tool for creating RGBA sprite cutouts from gameplay video. Draw lasso selections around sprites to export them as transparent PNGs, organized by class.

## Windows Setup (Step by Step)

### 1. Install Python

Download Python 3.8+ from [python.org](https://www.python.org/downloads/). During installation, **check "Add Python to PATH"**.

Verify it works by opening Command Prompt (`Win+R`, type `cmd`, press Enter):

```
python --version
```

You should see something like `Python 3.11.x`. If you get "not recognized", restart your terminal or reinstall Python with the PATH option checked.

### 2. Download the Project

Option A - Git:
```
git clone https://github.com/weihaog1/Quick-Seg.git
cd Quick-Seg
```

Option B - No Git: Go to https://github.com/weihaog1/Quick-Seg, click the green **Code** button, click **Download ZIP**, extract it, then open Command Prompt and `cd` into the extracted folder:
```
cd C:\Users\YourName\Downloads\Quick-Seg-main
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

This installs Flask, OpenCV, and NumPy. If `pip` is not recognized, try `python -m pip install -r requirements.txt`.

### 4. Run the App

```
python app.py
```

Your browser will open automatically to the setup page at `http://localhost:5000`.

If port 5000 is taken, use a different port:
```
python app.py --port 8080
```

### 5. Configure and Start

On the setup page:

1. **Upload a video** - Drag and drop a `.mp4`/`.avi`/`.mkv`/`.mov`/`.webm` file onto the upload zone, or click to browse. Alternatively, select a video already on your machine from the server list.
2. **Set the output directory** - Type a path (e.g., `C:\Users\YourName\Desktop\sprites`) or click **Browse** to pick a folder.
3. Click **Start Annotating**.

### 6. Annotate

- **Draw** a lasso around a sprite by clicking and dragging
- **Select a class** from the sidebar or press `1`-`8` for the deck classes
- **Press `S`** to save the cutout
- **Arrow keys** to navigate frames
- **Switch Video** link in the header to go back to setup

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--video` | _(none)_ | Path to video file. If both `--video` and `--output` are given, skips the setup page. |
| `--output` | _(none)_ | Output directory for cutout PNGs. |
| `--port` | `5000` | Port to run the server on. |
| `--host` | `0.0.0.0` | Bind address. Use `127.0.0.1` for localhost-only. |
| `--videos-dir` | `.` | Directory to browse for server-side videos on the setup page. |
| `--uploads-dir` | `./uploads` | Directory where uploaded videos are saved. |
| `--no-browser` | _(flag)_ | Don't auto-open the browser on start. |

## Examples

```bash
# Interactive setup (default)
python app.py

# Direct mode (skip setup page)
python app.py --video gameplay.mp4 --output ./output

# Browse videos from a specific folder
python app.py --videos-dir C:\Users\YourName\Videos

# Specify everything up front
python app.py --video gameplay.mp4 --output ./sprites --port 8080
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `S` | Save the current cutout |
| `1`-`8` | Select class by number |
| `Escape` | Clear drawing / close modal |
| `Left/Right` | Previous / next frame |
| `Alt` + `Scroll` | Zoom in / out |
| `Space` + drag | Pan the view |
| `R` | Reset zoom and pan |
| `Ctrl+Z` | Undo last save |
| `?` | Show all shortcuts |

## Output Format

Cutouts are saved as RGBA PNGs organized by class:

```
output/
  class_name/
    class_name_0_CUSTOM_000.png
    class_name_0_CUSTOM_001.png
    ...
```

Each PNG has a transparent background with only the lasso-selected region visible.

## Troubleshooting

- **"python is not recognized"** - Reinstall Python and check "Add Python to PATH", or use the full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`
- **"pip is not recognized"** - Use `python -m pip install -r requirements.txt`
- **Port already in use** - Use `--port 8080` or another free port
- **Browser doesn't open** - Manually go to `http://localhost:5000` (or whatever port you chose)
- **Video won't load** - Make sure the file is a supported format (.mp4, .avi, .mkv, .mov, .webm) and not corrupted
