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
