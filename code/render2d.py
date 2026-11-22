"""
render2d.py - draws the 2D scene.                                         [Member 2]

PLACEHOLDER by Member 1 (lead) so the engine, the main loop and the GUI can
be tested before the real renderer exists: every figure is drawn as a plain
outline. Member 2 replaces the TODOs but keeps these four names, because
main.py and gui.py call them:

    build_scene()                          -> root Node of the 2D scene graph
    sync(root, game, dt)                   copy the game state onto the nodes
    draw(root, width, height, selected)    draw one frame
    pick(root, px, py, width, height)      -> Node under the mouse pixel, or None

TODO(M2): filled figures and a colour per object, starfield (glPointSize),
walls and frame (glLineWidth), seven-segment score with Bresenham lines,
raster algorithms on an "arcade pixel" grid, letterbox on resize,
pick() with the inverse world matrix, yellow outline on the selection.
"""
import math

from OpenGL.GL import (GL_COLOR_BUFFER_BIT, GL_DEPTH_TEST, GL_LIGHTING, GL_LINE_LOOP,
                       GL_MODELVIEW, GL_PROJECTION, glBegin, glClear, glColor3f,
                       glDisable, glEnd, glLineWidth, glLoadIdentity, glMatrixMode,
                       glOrtho, glVertex2f, glViewport)

import anim2d
import figures
import game as rules
from scene import Node
from scene import draw as draw_tree

BRICK_COLOURS = [(0.95, 0.26, 0.21), (1.0, 0.6, 0.0), (1.0, 0.92, 0.23),
                 (0.30, 0.69, 0.31), (0.13, 0.59, 0.95)]
SELECTED_COLOUR = (1.0, 1.0, 0.0)


def build_scene():
    """The 2D scene graph. Every figure is in model coordinates; the keyword
    arguments (tx, ty, ...) are its local transform."""
    root = Node("world")
    root.add(Node("cabinet_frame", figures.rect(20.0, 15.0), (0.55, 0.55, 0.65)))
    root.add(Node("paddle", figures.rect(2 * rules.PADDLE_HALF_WIDTH, 0.4),
                  (0.2, 0.85, 1.0), ty=rules.PADDLE_Y))
    root.add(Node("ball", figures.circle(rules.BALL_RADIUS), (1.0, 1.0, 1.0)))

    bricks = root.add(Node("bricks"))                 # group node
    for row in range(rules.BRICK_ROWS):
        for col in range(rules.BRICK_COLS):
            x, y = rules.brick_center(row, col)
            bricks.add(Node("brick_%d_%d" % (row, col),
                            figures.rect(rules.BRICK_W, rules.BRICK_H),
                            BRICK_COLOURS[row % len(BRICK_COLOURS)], tx=x, ty=y))

    # Hierarchy demo: ufo -> light ring -> 4 lights. Turning the ring orbits
    # all four lights; moving the UFO carries the ring and the lights along.
    ufo_body = [(x, 0.4 * y) for x, y in figures.regular_polygon(12, 1.0)]
    ufo = root.add(Node("ufo", ufo_body, (0.6, 1.0, 0.6), ty=6.4))
    ring = ufo.add(Node("ufo_light_ring"))
    for i in range(4):
        a = math.radians(90 * i)
        ring.add(Node("ufo_light_%d" % i, figures.regular_polygon(6, 0.15),
                      (1.0, 0.9, 0.2), tx=1.0 * math.cos(a), ty=1.0 * math.sin(a)))
    # Member 3: default joystick, capsule and hearts for any of them this scene
    # does not define itself (same names = yours are used instead).
    anim2d.ensure_nodes(root)
    return root


def sync(root, game, dt):
    """Copy the game state (plain numbers) onto the nodes before drawing.
    The 2D animation lives in anim2d.py (Member 3): ball, paddle, brick break /
    build, UFO path and lights, capsule, joystick, hearts, score pulse."""
    anim2d.sync(root, game, dt)


def draw(root, width, height, selected=None):
    """Draw one frame of the 2D view."""
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # TODO(M2): letterbox so the 4:3 world is never stretched.
    glOrtho(rules.WORLD_LEFT, rules.WORLD_RIGHT, rules.WORLD_BOTTOM, rules.WORLD_TOP, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_tree(root, lambda node: _outline(node, _inside(node, selected)))


def _inside(node, selected):
    """True if node is the selected node or one of its descendants."""
    while node is not None:
        if node is selected:
            return True
        node = node.parent
    return False


def _outline(node, highlighted):
    glLineWidth(3.0 if highlighted else 1.5)
    glColor3f(*(SELECTED_COLOUR if highlighted else node.color))
    glBegin(GL_LINE_LOOP)
    for x, y in node.figure:
        glVertex2f(x, y)
    glEnd()


def pick(root, px, py, width, height):
    """TODO(M2): mouse pixel -> world point -> inverse(world()) -> point-in-figure test."""
    return None
