"""
raster.py - the course raster algorithms.                                 [Member 2]

Each function only RETURNS integer pixels (or spans); it draws nothing.
render2d.py draws the result with GL_POINTS on a low-resolution
"arcade pixel" grid (for example 320 x 240, scaled up).

SKELETON by Member 1 (lead): the names and return formats below are the
contract the tests and render2d.py use. Member 2 writes the bodies.
"""


def bresenham_line(x0, y0, x1, y1):
    """Integer points of the line from (x0, y0) to (x1, y1), all 8 octants.
    Example: (0, 0) -> (5, 2) gives (0,0) (1,0) (2,1) (3,1) (4,2) (5,2)."""
    raise NotImplementedError("TODO(M2): Bresenham line")


def midpoint_circle(xc, yc, r):
    """Integer points on the circle of radius r around (xc, yc)."""
    raise NotImplementedError("TODO(M2): midpoint circle")


def scanline_fill(polygon):
    """Horizontal spans [(y, x_start, x_end), ...] that fill the polygon."""
    raise NotImplementedError("TODO(M2): scan-line polygon fill")
