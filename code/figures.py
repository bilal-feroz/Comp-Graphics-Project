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
