"""
figures.py - every figure in its own MODEL coordinates, centred on the origin.
2D part: Member 2.   3D part: Member 4.

  2D figure = list of (x, y) vertices, counter-clockwise.
  3D figure = (vertices, faces)
              vertices: [(x, y, z), ...]
              faces:    [(i0, i1, i2, ...), ...], each listed counter-clockwise
                        when seen from OUTSIDE the solid.

A figure is never moved in this file: its Node's transform places it.
"""
import math
import raster

# ======================================================================= 2D (Member 2)


def rect(w, h):
    """Axis-aligned rectangle, w wide and h tall, centred on (0, 0)."""
    hw, hh = w / 2.0, h / 2.0
    return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]


def regular_polygon(n, r):
    """n corners evenly spaced on a circle of radius r, counter-clockwise."""
    return [(r * math.cos(2.0 * math.pi * i / n), r * math.sin(2.0 * math.pi * i / n))
            for i in range(n)]


def circle(r, steps=32):
    """Outline of a circle of radius r, counter-clockwise."""
    return regular_polygon(steps, r)


def brick(w=1.8, h=0.6):
    """Brick rectangle in model coordinates."""
    return rect(w, h)


def rounded_paddle(w=3.0, h=0.4, steps=10):
    """Paddle with rounded circular ends, centred on the origin."""
    r = h / 2.0
    hw = max(r, w / 2.0)
    inner_w = hw - r
    pts = []
    # Right cap: angle from -pi/2 to pi/2
    for i in range(steps + 1):
        a = -math.pi / 2.0 + math.pi * i / steps
        pts.append((inner_w + r * math.cos(a), r * math.sin(a)))
    # Left cap: angle from pi/2 to 3*pi/2
    for i in range(steps + 1):
        a = math.pi / 2.0 + math.pi * i / steps
        pts.append((-inner_w + r * math.cos(a), r * math.sin(a)))
    return pts


def ball(r=0.3):
    """Ball outline in model coordinates."""
    return circle(r, steps=24)


def ufo_body(w=2.0, h=0.8, steps=24):
    """Saucer/flattened ellipse body for the UFO."""
    hw, hh = w / 2.0, h / 2.0
    return [(hw * math.cos(2.0 * math.pi * i / steps),
             hh * math.sin(2.0 * math.pi * i / steps))
            for i in range(steps)]


def ufo_dome(w=1.0, h=0.6, steps=12):
    """Upper glass dome for the UFO."""
    hw, hh = w / 2.0, h
    pts = []
    for i in range(steps + 1):
        a = math.pi * i / steps
        pts.append((hw * math.cos(a), hh * math.sin(a)))
    pts.append((-hw, 0.0))
    return pts


def ufo_light(r=0.15):
    """Small circular navigation light."""
    return regular_polygon(8, r)


def heart(size=0.4, steps=24):
    """Heart shape for player lives, centred on (0, 0)."""
    pts = []
    # Parametric heart curve scaled to size
    for i in range(steps):
        t = 2.0 * math.pi * i / steps
        # Standard cardioid/heart equation
        x = 16.0 * (math.sin(t) ** 3)
        y = 13.0 * math.cos(t) - 5.0 * math.cos(2 * t) - 2.0 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(((x / 16.0) * size, (y / 16.0) * size))
    return pts


def joystick_base(w=1.2, h=0.5):
    """Trapezoid base for arcade joystick."""
    hw = w / 2.0
    top_hw = hw * 0.7
    hh = h / 2.0
    return [(-hw, -hh), (hw, -hh), (top_hw, hh), (-top_hw, hh)]


def joystick_stick(w=0.15, h=0.8):
    """Shaft for joystick."""
    return rect(w, h)


def joystick_knob(r=0.25):
    """Ball knob for joystick top."""
    return circle(r, steps=16)


def button(r=0.3):
    """Arcade control button."""
    return regular_polygon(16, r)


def cabinet_frame(w=20.0, h=15.0):
    """Outer border frame for the arcade cabinet."""
    return rect(w, h)


# 7-Segment lookup: segments A (top), B (top-right), C (bot-right),
# D (bot), E (bot-left), F (top-left), G (mid)
_SEG_MAP = {
    0: (1, 1, 1, 1, 1, 1, 0),
    1: (0, 1, 1, 0, 0, 0, 0),
    2: (1, 1, 0, 1, 1, 0, 1),
    3: (1, 1, 1, 1, 0, 0, 1),
    4: (0, 1, 1, 0, 0, 1, 1),
    5: (1, 0, 1, 1, 0, 1, 1),
    6: (1, 0, 1, 1, 1, 1, 1),
    7: (1, 1, 1, 0, 0, 0, 0),
    8: (1, 1, 1, 1, 1, 1, 1),
    9: (1, 1, 1, 1, 0, 1, 1),
}


def seven_segment_polygons(digit=0, w=0.5, h=0.9, thick=0.08):
    """Returns a list of polygons (rectangles) for the active segments
    of a digit, centred at (0, 0).
    """
    hw = w / 2.0
    hh = h / 2.0
    th = thick / 2.0

    # 7 segment boxes: (cx, cy, sw, sh)
    defs = [
        (0.0, hh - th, w - 2 * thick, thick),      # A: top horizontal
        (hw - th, hh / 2.0, thick, hh - thick),   # B: top-right vertical
        (hw - th, -hh / 2.0, thick, hh - thick),  # C: bottom-right vertical
        (0.0, -hh + th, w - 2 * thick, thick),     # D: bottom horizontal
        (-hw + th, -hh / 2.0, thick, hh - thick), # E: bottom-left vertical
        (-hw + th, hh / 2.0, thick, hh - thick),  # F: top-left vertical
        (0.0, 0.0, w - 2 * thick, thick),         # G: middle horizontal
    ]

    segments = []
    active = _SEG_MAP.get(int(digit) % 10, (1, 1, 1, 1, 1, 1, 0))
    for on, (cx, cy, sw, sh) in zip(active, defs):
        if on:
            box = rect(sw, sh)
            segments.append([(x + cx, y + cy) for x, y in box])
    return segments


# ======================================================================= 3D (Member 4)


def box(w, h, d):
    """Box w x h x d: 8 vertices and 6 quad faces (counter-clockwise from outside)."""
    x, y, z = w / 2.0, h / 2.0, d / 2.0
    vertices = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),   # back  (z < 0)
                (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]       # front (z > 0)
    faces = [(4, 5, 6, 7),   # front  +z
             (1, 0, 3, 2),   # back   -z
             (1, 2, 6, 5),   # right  +x
             (0, 4, 7, 3),   # left   -x
             (3, 7, 6, 2),   # top    +y
             (0, 1, 5, 4)]   # bottom -y
    return vertices, faces


# TODO(M4): bevelled_brick()  12 vertices, 10 faces (team model 1)
#           trophy()          profile of ~10 points turned around y in 16 steps (team model 2)
#           star()            octahedron, 6 vertices, 8 faces
#           face_normal(...)  cross product of two edges, normalised
