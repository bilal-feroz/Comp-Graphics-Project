"""
persist.py - save / load the scene settings (JSON) and screenshots.     [Member 3]

Optional enhancement from the brief (section 2.6): "Save and load the scene
settings (JSON); export a screenshot."

    Ctrl+S / Save button        settings.json  <- speed, view, game tuning,
                                                  camera, best score, and the
                                                  colour / size / rotation /
                                                  visibility of every object
    Ctrl+O / Load button        settings.json  -> the same values back
    P / Screenshot button       screenshots/arcade_<date>_<time>.png

Both files are written next to this file (code/) and are in .gitignore.

A settings file is checked before anything is used: unknown objects are
skipped, numbers are clamped to the slider ranges, wrong types are ignored,
and a damaged file gives a clear message instead of a crash.

Written by Member 3 with help from Claude (Anthropic AI assistant);
see the AI-use appendix of the report.
"""
import json
import math
import os
import time

import anim2d

HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(HERE, "settings.json")
SCREENSHOT_DIR = os.path.join(HERE, "screenshots")
FORMAT = "arcade-breakout-settings"
VERSION = 1

# The same ranges as the GUI sliders, so a loaded file can never set a value
# the sliders could not show.
LIMITS = {"speed": (0.1, 3.0), "ball_speed": (1.0, 15.0), "ufo_orbit_speed": (0.0, 360.0),
          "paddle_width": (0.5, 2.5), "size": (0.1, 3.0),
          "yaw": (-180.0, 180.0), "pitch": (-80.0, 80.0), "distance": (5.0, 40.0)}
GAME_FIELDS = ("ball_speed", "ufo_orbit_speed", "paddle_width")


# ======================================================================= collect / apply

def collect_settings(app):
    """Everything worth keeping from the running program, as plain JSON values."""
    game = app.game
    data = {"format": FORMAT, "version": VERSION,
            "saved": time.strftime("%Y-%m-%d %H:%M:%S"),
            "speed": app.speed, "view": app.view,
            "game": {"ball_speed": game.ball_speed,
                     "ufo_orbit_speed": game.ufo_orbit_speed,
                     "paddle_width": game.paddle_base},      # slider value, not the power-up
            "high_score": game.high_score,
            "nodes_2d": node_settings(app.scene2d, anim2d.animated_fields(game)),
            "nodes_3d": node_settings(app.scene3d)}
    camera = getattr(getattr(app, "gui", None), "camera", None)
    if camera is not None:
        data["camera"] = {"yaw": camera.yaw, "pitch": camera.pitch, "distance": camera.distance}
    return data


def node_settings(root, animated=None):
    """{name: {color, visible, size, rotation}} for every node of a scene graph.
    `animated` ({name: {"size", "rotation"}}, from anim2d.animated_fields) lists
    the values the animation drives; those are left out. Visibility of bricks,
    hearts, ball and capsule belongs to the game (a broken brick is gone, not hidden)."""
    animated = animated or {}
    nodes = {}
    for node in root.all_nodes():
        driven = animated.get(node.name, ())
        entry = {"color": [round(c, 4) for c in node.color]}
        if not _game_controls_visibility(node.name):
            entry["visible"] = node.visible
        if "size" not in driven:
            entry["size"] = round(node.sx, 4)
        if "rotation" not in driven:
            entry["rotation"] = round(node.angle if node.dim == 2 else node.ry, 3)
        nodes[node.name] = entry
    return nodes


def _game_controls_visibility(name):
    """Bricks, hearts, the ball and the capsule appear and disappear with the game."""
    return name in ("ball", "capsule") or name.startswith(("brick_", "heart_"))


def apply_settings(app, data):
    """Put a settings dictionary (from load_settings) back into the program.
    Returns how many objects were changed. Bad values are skipped or clamped."""
    _check_format(data)
    speed = _number(data, "speed")
    if speed is not None:
        app.set_speed(speed)
    if data.get("view") in ("2D", "3D"):
        app.set_view(data["view"])
    game_values = data.get("game")
    if isinstance(game_values, dict):
        for field in GAME_FIELDS:
            value = _number(game_values, field)
            if value is not None:
                setattr(app.game, field, value)
    best = data.get("high_score")
    if isinstance(best, int) and not isinstance(best, bool) and best >= 0:
        app.game.high_score = max(app.game.high_score, best)
    camera = getattr(getattr(app, "gui", None), "camera", None)
    camera_values = data.get("camera")
    if camera is not None and isinstance(camera_values, dict):
        camera.set(yaw=_number(camera_values, "yaw"), pitch=_number(camera_values, "pitch"),
                   distance=_number(camera_values, "distance"))
    changed = _apply_nodes(app.scene2d, data.get("nodes_2d"), anim2d.animated_fields(app.game))
    changed += _apply_nodes(app.scene3d, data.get("nodes_3d"), {})
    return changed


def _apply_nodes(root, saved, animated):
    if not isinstance(saved, dict):
        return 0
    changed = 0
    for node in root.all_nodes():
        entry = saved.get(node.name)
        if not isinstance(entry, dict):
            continue                                   # not in the file: leave it alone
        colour = entry.get("color")
        if (isinstance(colour, list) and len(colour) == 3
                and all(_is_number(c) for c in colour)):
            node.color = tuple(min(1.0, max(0.0, float(c))) for c in colour)
        if isinstance(entry.get("visible"), bool) and not _game_controls_visibility(node.name):
            node.visible = entry["visible"]
        driven = animated.get(node.name, ())
        size = _number(entry, "size")
        if size is not None and "size" not in driven:
            node.sx = node.sy = size
            if node.dim == 3:
                node.sz = size
        rotation = entry.get("rotation")
        if _is_number(rotation) and "rotation" not in driven:
            if node.dim == 2:
                node.angle = _wrap_degrees(float(rotation))
            else:
                node.ry = _wrap_degrees(float(rotation))
        changed += 1
    return changed


def _is_number(value):
    """A real, finite number (True / False do not count)."""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _number(section, key):
    """section[key] clamped to LIMITS[key], or None if missing or not a number."""
    value = section.get(key)
    if not _is_number(value):
        return None
    low, high = LIMITS[key]
    return min(high, max(low, float(value)))


def _wrap_degrees(angle):
    angle = math.fmod(angle, 360.0)
    if angle > 180.0:
        angle -= 360.0
    elif angle <= -180.0:
        angle += 360.0
    return angle


def _check_format(data):
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise ValueError("this is not a settings file of Arcade Breakout")
    if not isinstance(data.get("version"), int) or data["version"] > VERSION:
        raise ValueError("settings file version %r is not supported" % data.get("version"))


# ======================================================================= files

def save_settings(path, settings):
    """Write the settings dictionary to `path` as JSON.
    It is written to a temporary file first and then renamed, so a crash
    half-way can never leave a broken settings.json behind."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2)
    os.replace(temporary, path)
    return path


def load_settings(path):
    """Read a settings dictionary back from `path` (checked, not yet applied)."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise ValueError("no saved settings yet - press Save (Ctrl+S) first") from None
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("the settings file is damaged (%s)" % error) from None
    _check_format(data)
    return data


def screenshot_path(folder=SCREENSHOT_DIR):
    """A new file name such as screenshots/arcade_20261121_231500.png."""
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "arcade_%s.png" % stamp)
    number = 2
    while os.path.exists(path):                       # two shots in the same second
        path = os.path.join(folder, "arcade_%s_%d.png" % (stamp, number))
        number += 1
    return path


def save_screenshot(path, width, height):
    """Save the current OpenGL frame as a PNG.

    Call it right after drawing a frame and BEFORE the buffers are swapped:
    glReadPixels copies the back buffer (the finished picture) into memory.
    OpenGL's first row is the BOTTOM of the picture and an image file's first
    row is the TOP, so the image is flipped upside down before saving."""
    from OpenGL.GL import (GL_BACK, GL_PACK_ALIGNMENT, GL_RGB, GL_UNSIGNED_BYTE,
                           glPixelStorei, glReadBuffer, glReadPixels)
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("screenshots need Pillow:  pip install Pillow") from None
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    glPixelStorei(GL_PACK_ALIGNMENT, 1)               # rows are packed tightly
    glReadBuffer(GL_BACK)
    pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
    if hasattr(pixels, "tobytes"):                    # PyOpenGL may return a numpy array
        pixels = pixels.tobytes()
    flip = getattr(Image, "Transpose", Image).FLIP_TOP_BOTTOM
    Image.frombytes("RGB", (width, height), bytes(pixels)).transpose(flip).save(path)
    return path
