"""
hud2d.py - arcade-pixel overlay for the 2D view: score and starfield.    [Member 1, integration]

Draws on top of the 2D scene with Member 2's raster algorithms, on a low-resolution
320 x 240 "arcade pixel" grid where every grid pixel is one square GL_POINT:

  * the score as seven-segment digits: the segment shapes come from
    figures.seven_segment_polygons (Member 2), each segment is filled with
    raster.scanline_fill and outlined with raster.bresenham_line;
  * a starfield of 100 points in three point sizes (glPointSize).

It only READS the game (score, score_pulse) and changes nothing.
App.draw calls it right after render2d.draw, so the letterboxed world
projection set up by render2d is still active.
"""
import random

from OpenGL.GL import GL_POINTS, glBegin, glColor3f, glEnd, glPointSize, glVertex2f

import figures
import game as rules
import raster
import render2d

GRID_W, GRID_H = 320, 240                                         # the arcade pixel grid
PIXEL = (rules.WORLD_RIGHT - rules.WORLD_LEFT) / GRID_W            # 0.0625 world units
DIGIT_W, DIGIT_H, DIGIT_THICK, DIGIT_GAP = 10, 18, 3, 3            # in arcade pixels
SCORE_X, SCORE_Y = GRID_W - 8 - 5 * (DIGIT_W + DIGIT_GAP) + DIGIT_GAP, GRID_H - 7 - DIGIT_H

_digit_cache = {}


def to_world(gx, gy):
    """Centre of arcade pixel (gx, gy) in world coordinates."""
    return rules.WORLD_LEFT + (gx + 0.5) * PIXEL, rules.WORLD_BOTTOM + (gy + 0.5) * PIXEL


def digit_pixels(digit):
    """(fill, outline): the arcade pixels of one seven-segment digit whose
    lower-left corner is grid pixel (0, 0)."""
    if digit not in _digit_cache:
        fill, outline = set(), set()
        for segment in figures.seven_segment_polygons(digit, DIGIT_W, DIGIT_H, DIGIT_THICK):
            poly = [(x + DIGIT_W / 2.0, y + DIGIT_H / 2.0) for x, y in segment]
            for y, x_start, x_end in raster.scanline_fill(poly):          # scan-line fill
                fill.update((x, y) for x in range(x_start, x_end))
            for i in range(len(poly)):                                   # Bresenham outline
                (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
                outline.update(raster.bresenham_line(ax, ay, bx, by))
        _digit_cache[digit] = (fill - outline, outline)
    return _digit_cache[digit]


def _make_stars():
    """100 stars from a fixed seed, kept out of the brick wall; three sizes."""
    rng = random.Random(7)
    layers = {1: [], 2: [], 3: []}
    while sum(len(v) for v in layers.values()) < 100:
        x = rng.uniform(rules.WORLD_LEFT + 0.4, rules.WORLD_RIGHT - 0.4)
        y = rng.uniform(rules.WORLD_BOTTOM + 0.9, rules.WORLD_TOP - 0.4)
        if 1.2 < y < 5.5:                                                # behind the bricks: skip
            continue
        size = rng.choice((1, 1, 1, 2, 2, 3))
        layers[size].append((x, y))
    return layers


STARS = _make_stars()
STAR_COLOURS = {1: (0.45, 0.5, 0.68), 2: (0.7, 0.76, 0.95), 3: (1.0, 1.0, 1.0)}


def draw(game, width, height):
    """Draw the starfield and the score. Call right after render2d.draw."""
    viewport_w = render2d.compute_letterbox(width, height)[2]
    for size, stars in STARS.items():                                    # point size: 1, 2, 3
        glPointSize(float(size))
        glColor3f(*STAR_COLOURS[size])
        glBegin(GL_POINTS)
        for x, y in stars:
            glVertex2f(x, y)
        glEnd()

    glPointSize(max(1.0, viewport_w / float(GRID_W)))                   # one point = one arcade pixel
    glow = min(1.0, getattr(game, "score_pulse", 0.0))
    text = "%05d" % max(0, min(99999, int(game.score)))
    for part, colour in ((0, (0.55 + 0.3 * glow, 0.42 + 0.3 * glow, 0.05)), (1, (1.0, 0.86 + 0.14 * glow, 0.25 + 0.5 * glow))):
        glColor3f(*colour)
        glBegin(GL_POINTS)
        for i, ch in enumerate(text):
            pixels = digit_pixels(int(ch))[part]
            ox = SCORE_X + i * (DIGIT_W + DIGIT_GAP)
            for gx, gy in pixels:
                glVertex2f(*to_world(ox + gx, SCORE_Y + gy))
        glEnd()
