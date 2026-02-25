"""Flask web app for creating RGBA sprite cutouts from gameplay video."""
import argparse, os, re, sys, webbrowser
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Timer
import cv2, numpy as np
from flask import Flask, Response, jsonify, render_template, request
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2 GB

VIDEO_PATH, OUTPUT_DIR, _cap = "", "", None
_configured = False
_videos_dir, _uploads_dir = ".", "./uploads"
_frame_cache, _undo_stack = OrderedDict(), []
_session = {"saves_count": 0, "undo_count": 0, "last_class": None, "start": None}
CACHE_MAX, SAFE_NAME = 10, re.compile(r"^[A-Za-z0-9_\- ]+$")
_cap_lock = Lock()
VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
DECK_CLASSES = [
    "arrows", "barbarian-barrel", "electro-spirit", "flying-machine",
    "goblin-cage", "royal-hogs", "royal-recruits", "zappies",
]


def _require_config():
    """Return an error response if the app is not configured, else None."""
    if not _configured:
        return jsonify({"error": "Not configured. Complete setup first."}), 409
    return None


def _reset_state():
    """Release video capture and clear all caches."""
    global _cap, _dirs_seeded
    _dirs_seeded = False
    if _cap is not None and _cap.isOpened():
        _cap.release()
    _cap = None
    _frame_cache.clear()
    _undo_stack.clear()
    _session.update({"saves_count": 0, "undo_count": 0, "last_class": None,
                     "start": datetime.now(timezone.utc).isoformat()})


def get_cap():
    global _cap
    if _cap is None or not _cap.isOpened(): _cap = cv2.VideoCapture(VIDEO_PATH)
    return _cap


def _read_frame(n):
    if n in _frame_cache:
        _frame_cache.move_to_end(n); return _frame_cache[n]
    with _cap_lock:
        c = get_cap(); c.set(cv2.CAP_PROP_POS_FRAMES, n)
        ret, frame = c.read()
    if not ret: return None
    _frame_cache[n] = frame
    if len(_frame_cache) > CACHE_MAX: _frame_cache.popitem(last=False)
    return frame


def _err(msg, code=400):
    return jsonify({"error": msg}), code


def _check_points(points):
    if not isinstance(points, list) or len(points) < 3:
        return None, _err("Need at least 3 points")
    for p in points:
        if not isinstance(p, list) or len(p) != 2:
            return None, _err("Each point must be [x, y]")
    return np.array(points, dtype=np.int32), None


def _check_regions(regions):
    """Validate a list of {points, subtract} region objects."""
    if not isinstance(regions, list) or len(regions) == 0:
        return None, _err("Need at least one region")
    parsed = []
    for r in regions:
        pts, err = _check_points(r.get("points", []))
        if err:
            return None, err
        parsed.append({"pts": pts, "subtract": bool(r.get("subtract", False))})
    return parsed, None


_dirs_seeded = False

def _seed_class_dirs():
    """Create all 8 deck class folders in the output directory."""
    global _dirs_seeded
    if _dirs_seeded:
        return
    out = Path(OUTPUT_DIR)
    for name in DECK_CLASSES:
        (out / name).mkdir(parents=True, exist_ok=True)
    _dirs_seeded = True


def _class_counts():
    out = Path(OUTPUT_DIR)
    seen = set()
    result = []
    # Always include deck classes first, in order
    for name in DECK_CLASSES:
        d = out / name
        total = len(list(d.glob("*.png"))) if d.exists() else 0
        custom = len(list(d.glob("*_CUSTOM_*.png"))) if d.exists() else 0
        result.append({"name": name, "total": total, "custom": custom})
        seen.add(name)
    # Then any extra directories the user created
    if out.exists():
        for d in sorted(out.iterdir()):
            if not d.is_dir() or d.name in seen: continue
            total = len(list(d.glob("*.png")))
            custom = len(list(d.glob("*_CUSTOM_*.png")))
            result.append({"name": d.name, "total": total, "custom": custom})
    return result


def _apply_mask(frame, pts):
    x, y, w, h = cv2.boundingRect(pts)
    if w == 0 or h == 0: return None, None
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [pts], 255)
    rgba = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = mask[y:y+h, x:x+w]
    return rgba, (w, h)


def _apply_composite_mask(frame, regions):
    """Build RGBA cutout from multiple add/subtract regions."""
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    # Apply add regions first, then subtract
    for r in regions:
        if not r["subtract"]:
            cv2.fillPoly(mask, [r["pts"]], 255)
    for r in regions:
        if r["subtract"]:
            cv2.fillPoly(mask, [r["pts"]], 0)
    coords = np.where(mask > 0)
    if len(coords[0]) == 0:
        return None, None
    y1, y2 = int(coords[0].min()), int(coords[0].max()) + 1
    x1, x2 = int(coords[1].min()), int(coords[1].max()) + 1
    rgba = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = mask[y1:y2, x1:x2]
    return rgba, (x2 - x1, y2 - y1)


def _next_id(class_dir, name):
    d = Path(class_dir)
    if not d.exists(): return 0
    ids = []
    for f in d.glob(f"{name}_0_CUSTOM_*.png"):
        try: ids.append(int(f.stem.split("_")[-1]))
        except ValueError: pass
    return max(ids, default=-1) + 1


def _get_frame_or_err(n):
    total = int(get_cap().get(cv2.CAP_PROP_FRAME_COUNT))
    if n < 0 or n >= total: return None, _err(f"Frame {n} out of range")
    frame = _read_frame(n)
    if frame is None: return None, _err("Could not read frame", 500)
    return frame, None


def _list_videos():
    """List video files from videos-dir and uploads-dir."""
    seen = set()
    result = []
    for directory in [_videos_dir, _uploads_dir]:
        d = Path(directory)
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in VIDEO_EXTS:
                continue
            abs_path = str(f.resolve())
            if abs_path in seen:
                continue
            seen.add(abs_path)
            try:
                size = f.stat().st_size
            except OSError:
                size = 0
            result.append({"name": f.name, "path": abs_path, "size": size})
    return result


def _browse_dir(path_str):
    """List subdirectories of a given path for the folder browser."""
    try:
        p = Path(path_str).resolve()
    except (ValueError, OSError):
        return None, "Invalid path"
    if not p.exists():
        return None, f"Path does not exist: {path_str}"
    if not p.is_dir():
        return None, f"Not a directory: {path_str}"
    dirs = []
    try:
        for entry in sorted(p.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                dirs.append(entry.name)
    except PermissionError:
        return None, f"Permission denied: {path_str}"
    return {"path": str(p), "dirs": dirs}, None


# ============================================================
# Setup / Config Endpoints
# ============================================================

@app.route("/")
def index():
    if _configured:
        return render_template("index.html")
    return render_template("setup.html")


@app.route("/api/config")
def get_config():
    return jsonify({
        "configured": _configured,
        "video": VIDEO_PATH if _configured else None,
        "output": OUTPUT_DIR if _configured else None,
    })


@app.route("/api/browse")
def browse_dirs():
    path = request.args.get("path", os.getcwd())
    data, err_msg = _browse_dir(path)
    if err_msg:
        return _err(err_msg)
    return jsonify(data)


@app.route("/api/configure", methods=["POST"])
def configure():
    global VIDEO_PATH, OUTPUT_DIR, _configured
    data = request.json or {}
    video = data.get("video", "").strip()
    output = data.get("output", "").strip()

    if not video:
        return _err("Video path is required")
    if not output:
        return _err("Output directory is required")

    vpath = Path(video)
    if not vpath.exists() or not vpath.is_file():
        return _err(f"Video not found: {video}")

    tc = cv2.VideoCapture(str(vpath))
    if not tc.isOpened():
        return _err(f"Cannot open video: {video}")
    tc.release()

    _reset_state()
    VIDEO_PATH = str(vpath.resolve())
    OUTPUT_DIR = output
    _configured = True
    print(f"Configured - Video: {VIDEO_PATH}\nOutput: {OUTPUT_DIR}")

    return jsonify({"status": "ok", "video": VIDEO_PATH, "output": OUTPUT_DIR})


@app.route("/api/videos")
def list_videos():
    return jsonify(_list_videos())


@app.route("/api/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return _err("No video file in request")

    f = request.files["video"]
    if not f.filename:
        return _err("No filename")

    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in VIDEO_EXTS:
        return _err(f"Unsupported file type: {ext}")

    upload_dir = Path(_uploads_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / filename

    # Avoid overwriting - append number if exists
    counter = 1
    while dest.exists():
        stem = os.path.splitext(filename)[0]
        dest = upload_dir / f"{stem}_{counter}{ext}"
        counter += 1

    f.save(str(dest))
    abs_path = str(dest.resolve())
    return jsonify({"status": "ok", "path": abs_path, "filename": dest.name})


@app.route("/api/reset", methods=["POST"])
def reset_config():
    global _configured
    _reset_state()
    _configured = False
    return jsonify({"status": "ok"})


# ============================================================
# Annotation Endpoints (require configuration)
# ============================================================

@app.route("/api/video/info")
def video_info():
    err = _require_config()
    if err: return err
    c = get_cap()
    return jsonify({"total_frames": int(c.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(c.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(c.get(cv2.CAP_PROP_FRAME_HEIGHT)), "fps": c.get(cv2.CAP_PROP_FPS)})


@app.route("/api/frame/<int:n>")
def get_frame(n):
    err = _require_config()
    if err: return err
    frame, err = _get_frame_or_err(n)
    if err: return err
    w_param = request.args.get("w", type=int)
    quality = 90
    if w_param and w_param > 0:
        ho, wo = frame.shape[:2]
        frame = cv2.resize(frame, (w_param, int(ho * w_param / wo)), interpolation=cv2.INTER_AREA)
        quality = 60
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return Response(buf.tobytes(), mimetype="image/jpeg")


@app.route("/api/classes")
def get_classes():
    err = _require_config()
    if err: return err
    return jsonify(_class_counts())


@app.route("/api/export", methods=["POST"])
def export_cutout():
    err = _require_config()
    if err: return err
    data = request.json or {}
    frame_num, class_name = data.get("frame"), data.get("class_name", "")
    if frame_num is None: return _err("Missing frame number")
    if not class_name or not SAFE_NAME.match(class_name): return _err("Invalid class name")
    regions, err = _check_regions(data.get("regions", []))
    if err: return err
    frame, err = _get_frame_or_err(frame_num)
    if err: return err
    rgba, size = _apply_composite_mask(frame, regions)
    if rgba is None: return _err("Selection has zero area")
    _seed_class_dirs()
    class_dir = Path(OUTPUT_DIR) / class_name
    class_dir.mkdir(parents=True, exist_ok=True)
    cid = _next_id(class_dir, class_name)
    filename = f"{class_name}_0_CUSTOM_{cid:03d}.png"
    filepath = class_dir / filename
    cv2.imwrite(str(filepath), rgba)
    _undo_stack.append(str(filepath))
    _session["saves_count"] += 1
    _session["last_class"] = class_name
    return jsonify({"filename": filename, "size": list(size)})


@app.route("/api/preview", methods=["POST"])
def preview_cutout():
    err = _require_config()
    if err: return err
    data = request.json or {}
    frame_num = data.get("frame")
    if frame_num is None: return _err("Missing frame number")
    regions, err = _check_regions(data.get("regions", []))
    if err: return err
    frame, err = _get_frame_or_err(frame_num)
    if err: return err
    rgba, _ = _apply_composite_mask(frame, regions)
    if rgba is None: return _err("Selection has zero area")
    _, buf = cv2.imencode(".png", rgba)
    return Response(buf.tobytes(), mimetype="image/png")


@app.route("/api/undo", methods=["POST"])
def undo():
    err = _require_config()
    if err: return err
    if not _undo_stack: return jsonify({"error": "nothing to undo"}), 400
    fp = Path(_undo_stack.pop())
    filename = fp.name
    if fp.exists():
        fp.unlink()
        if fp.parent.exists() and not any(fp.parent.iterdir()): fp.parent.rmdir()
    _session["undo_count"] += 1
    return jsonify({"deleted": filename, "counts": _class_counts()})


@app.route("/api/session")
def session_info():
    err = _require_config()
    if err: return err
    return jsonify({"saves_count": _session["saves_count"],
        "undo_count": _session["undo_count"], "last_class": _session["last_class"],
        "session_start_time_iso": _session["start"]})


if __name__ == "__main__":
    pa = argparse.ArgumentParser(description="Sprite cutout creator web app")
    pa.add_argument("--video", default=None, help="Path to video file (optional; skip setup if given with --output)")
    pa.add_argument("--output", default=None, help="Output directory (optional; skip setup if given with --video)")
    pa.add_argument("--port", type=int, default=5000)
    pa.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    pa.add_argument("--videos-dir", default=".", help="Directory to browse for server-side videos")
    pa.add_argument("--uploads-dir", default="./uploads", help="Directory for uploaded videos")
    pa.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")
    args = pa.parse_args()

    _videos_dir = args.videos_dir
    _uploads_dir = args.uploads_dir

    # Direct mode: both --video and --output given
    if args.video and args.output:
        VIDEO_PATH = args.video
        OUTPUT_DIR = args.output
        vpath = Path(VIDEO_PATH)
        if not vpath.exists() or not vpath.is_file():
            sys.exit(f"Error: video not found: {VIDEO_PATH}")
        tc = cv2.VideoCapture(VIDEO_PATH)
        if not tc.isOpened(): sys.exit(f"Error: cannot open video: {VIDEO_PATH}")
        tc.release()
        _configured = True
        _session["start"] = datetime.now(timezone.utc).isoformat()
        print(f"Video: {VIDEO_PATH}\nOutput: {OUTPUT_DIR}")
    else:
        print("Setup mode: open the browser to configure video and output.")

    if not args.no_browser:
        url = f"http://localhost:{args.port}"
        Timer(1.0, webbrowser.open, [url]).start()

    app.run(host=args.host, port=args.port, debug=False)
