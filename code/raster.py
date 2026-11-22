"""
raster.py - the course raster algorithms.                                 [Member 2]

Each function only RETURNS integer pixels (or spans); it draws nothing.
render2d.py draws the result with GL_POINTS on a low-resolution
"arcade pixel" grid (for example 320 x 240, scaled up).

Implemented by Member 2 for the Breakout 2D Arcade World project.
"""
import math


def bresenham_line(x0, y0, x1, y1):
    """Integer points of the line from (x0, y0) to (x1, y1), all 8 octants.
    Example: (0, 0) -> (5, 2) gives (0,0) (1,0) (2,1) (3,1) (4,2) (5,2).
    """
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    if dy <= dx:
        # Shallow line: step along x (|slope| <= 1)
        d = 2 * dy - dx
        x, y = x0, y0
        for _ in range(dx + 1):
            points.append((x, y))
            if d >= 0:
                y += sy
                d -= 2 * dx
            d += 2 * dy
            x += sx
    else:
        # Steep line: step along y (|slope| > 1)
        d = 2 * dx - dy
        x, y = x0, y0
        for _ in range(dy + 1):
            points.append((x, y))
            if d >= 0:
                x += sx
                d -= 2 * dy
            d += 2 * dx
            y += sy
    return points


def midpoint_circle(xc, yc, r):
    """Integer points on the circle of radius r around (xc, yc) using
    8-way symmetry. Points are sorted counter-clockwise.
    """
    xc, yc, r = int(round(xc)), int(round(yc)), int(round(r))
    if r < 0:
        return []
    if r == 0:
        return [(xc, yc)]

    x = 0
    y = r
    d = 1 - r

    # Use a set to prevent duplicate boundary points where octants touch
    points_set = set()

    def add_symmetric(px, py):
        for sx in (-px, px):
            for sy in (-py, py):
                points_set.add((xc + sx, yc + sy))
                points_set.add((xc + sy, yc + sx))

    while x <= y:
        add_symmetric(x, y)
        if d < 0:
            d += 2 * x + 3
        else:
            d += 2 * (x - y) + 5
            y -= 1
        x += 1

    # Return points ordered counter-clockwise around (xc, yc)
    return sorted(list(points_set), key=lambda p: math.atan2(p[1] - yc, p[0] - xc))


def scanline_fill(polygon):
    """Horizontal spans [(y, x_start, x_end), ...] that fill the polygon.
    Uses edge table and parity rule for robust scanline conversion.
    """
    if not polygon or len(polygon) < 3:
        return []

    y_coords = [p[1] for p in polygon]
    min_y = int(math.floor(min(y_coords)))
    max_y = int(math.ceil(max(y_coords)))

    n = len(polygon)
    spans = []

    for y in range(min_y, max_y + 1):
        intersections = []
        scan_y = float(y)

        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]

            x1, y1 = p1[0], p1[1]
            x2, y2 = p2[0], p2[1]

            # Skip horizontal edges
            if y1 == y2:
                continue

            # Check if scanline intersects this edge (half-open interval)
            if (y1 <= scan_y < y2) or (y2 <= scan_y < y1):
                # Linear interpolation
                t = (scan_y - y1) / (y2 - y1)
                x_inter = x1 + t * (x2 - x1)
                intersections.append(x_inter)

        intersections.sort()

        # Pair up intersections
        for j in range(0, len(intersections) - 1, 2):
            x_start = int(math.floor(intersections[j]))
            x_end = int(math.ceil(intersections[j + 1]))
            if x_end >= x_start:
                spans.append((y, x_start, x_end))

    return spans
