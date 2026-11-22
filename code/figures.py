"""
figures.py - every figure in its own MODEL coordinates, centred on the origin.
2D part: Member 2.   3D part: Member 4.

  2D figure = list of (x, y) vertices, counter-clockwise.
  3D figure = (vertices, faces)
              vertices: [(x, y, z), ...]
              faces:    [(i0, i1, i2, ...), ...], each listed counter-clockwise
                        when seen from OUTSIDE the solid.

A figure is never moved in this file: its Node's transform places it.

STARTER VERSION by Member 1 (lead) so the placeholder renderers have shapes
to draw. Members 2 and 4 replace the TODOs.
"""
import math

# ======================================================================= 2D (Member 2)


def rect(w, h):
    """Axis-aligned rectangle, w wide and h tall."""
    hw, hh = w / 2.0, h / 2.0
    return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]


def regular_polygon(n, r):
    """n corners evenly spaced on a circle of radius r, counter-clockwise."""
    return [(r * math.cos(2.0 * math.pi * i / n), r * math.sin(2.0 * math.pi * i / n))
            for i in range(n)]


def circle(r):
    """TODO(M2): build this outline with the midpoint circle algorithm (raster.py)."""
    return regular_polygon(32, r)


# TODO(M2): brick, paddle with rounded ends, ball, UFO body, UFO dome, UFO light,
#           heart (lives), joystick base / stick / knob, button, cabinet frame,
#           seven-segment digit (7 segments)

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


def star():
    """A small 3D star made from an octahedron."""
    vertices = [
        (0.0, 0.2, 0.0),
        (0.0, -0.2, 0.0),
        (-0.2, 0.0, 0.0),
        (0.2, 0.0, 0.0),
        (0.0, 0.0, 0.2),
        (0.0, 0.0, -0.2)
    ]

    faces = [
        (0, 2, 4),
        (0, 4, 3),
        (0, 3, 5),
        (0, 5, 2),
        (1, 4, 2),
        (1, 3, 4),
        (1, 5, 3),
        (1, 2, 5)
    ]

    return vertices, faces

def bevelled_brick(w, h, d):
    """A brick with clipped corners."""
    x = w / 2.0
    y = h / 2.0
    z = d / 2.0
    c = min(w, h) * 0.15

    vertices = [
        (-x + c, -y, -z), (x - c, -y, -z),
        (x, -y + c, -z), (x, y - c, -z),
        (x - c, y, -z), (-x + c, y, -z),
        (-x, y - c, -z), (-x, -y + c, -z),

        (-x + c, -y, z), (x - c, -y, z),
        (x, -y + c, z), (x, y - c, z),
        (x - c, y, z), (-x + c, y, z),
        (-x, y - c, z), (-x, -y + c, z)
    ]

    faces = [
        (8, 9, 10, 11, 12, 13, 14, 15),
        (7, 6, 5, 4, 3, 2, 1, 0),
        (0, 1, 9, 8),
        (1, 2, 10, 9),
        (2, 3, 11, 10),
        (3, 4, 12, 11),
        (4, 5, 13, 12),
        (5, 6, 14, 13),
        (6, 7, 15, 14),
        (7, 0, 8, 15)
    ]

    return vertices, faces


def trophy():
    """A simple 3D trophy made from a turned profile."""
    profile = [
        (0.0, -1.0),
        (0.5, -1.0),
        (0.5, -0.7),
        (0.8, -0.4),
        (0.9, 0.3),
        (0.7, 0.7),
        (0.4, 0.9),
        (0.0, 0.9)
    ]

    steps = 16
    vertices = []

    for i in range(steps):
        angle = 2.0 * math.pi * i / steps
        for radius, y in profile:
            vertices.append((
                radius * math.cos(angle),
                y,
                radius * math.sin(angle)
            ))

    faces = []

    for i in range(steps):
        next_i = (i + 1) % steps

        for j in range(len(profile) - 1):
            a = i * len(profile) + j
            b = next_i * len(profile) + j
            c = next_i * len(profile) + j + 1
            d = i * len(profile) + j + 1

            faces.append((a, d, c, b))

    return vertices, faces
