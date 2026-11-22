"""
render2d.py - draws the 2D scene.                                         [Member 2]

Implemented by Member 2 for the Breakout 2D Arcade World:
    - build_scene(): Complete hierarchical 2D scene graph
    - sync(root, game, dt): Copies game physics state to scene graph nodes
    - draw(root, width, height, selected): 4:3 letterboxing, filled polygons, selection highlight
    - pick(root, px, py, width, height): Mouse pixel -> world coordinates -> inverse world transform -> point-in-polygon
"""
import math

from OpenGL.GL import (GL_COLOR_BUFFER_BIT, GL_DEPTH_TEST, GL_LIGHTING, GL_LINE_LOOP,
                       GL_MODELVIEW, GL_POINTS, GL_POLYGON, GL_PROJECTION, glBegin,
                       glClear, glColor3f, glDisable, glEnd, glLineWidth, glLoadIdentity,
                       glMatrixMode, glOrtho, glPointSize, glVertex2f, glViewport)

import anim2d
import figures
import game as rules
import matrices
from scene import Node
from scene import draw as draw_tree

BRICK_COLOURS = [(0.95, 0.26, 0.21), (1.0, 0.6, 0.0), (1.0, 0.92, 0.23),
                 (0.30, 0.69, 0.31), (0.13, 0.59, 0.95)]
SELECTED_COLOUR = (1.0, 1.0, 0.0)


def build_scene():
    """Build the full 2D scene graph for Breakout."""
    root = Node("world")

    # Retro Arcade Cabinet Bezel / Frame
    root.add(Node("cabinet_frame", figures.cabinet_frame(20.0, 15.0), (0.35, 0.38, 0.45)))

    # Playing field side boundary walls
    root.add(Node("left_wall", figures.rect(0.2, 14.6), (0.45, 0.50, 0.60), tx=rules.WORLD_LEFT + 0.1, ty=0.0))
    root.add(Node("right_wall", figures.rect(0.2, 14.6), (0.45, 0.50, 0.60), tx=rules.WORLD_RIGHT - 0.1, ty=0.0))
    root.add(Node("top_wall", figures.rect(19.8, 0.2), (0.45, 0.50, 0.60), tx=0.0, ty=rules.WORLD_TOP - 0.1))

    # Player Paddle (rounded ends) & Ball
    root.add(Node("paddle", figures.rounded_paddle(2 * rules.PADDLE_HALF_WIDTH, 0.4),
                  (0.2, 0.85, 1.0), ty=rules.PADDLE_Y))
    root.add(Node("ball", figures.ball(rules.BALL_RADIUS), (1.0, 1.0, 1.0)))

    # Bricks grid
    bricks = root.add(Node("bricks"))
    for row in range(rules.BRICK_ROWS):
        for col in range(rules.BRICK_COLS):
            x, y = rules.brick_center(row, col)
            bricks.add(Node("brick_%d_%d" % (row, col),
                            figures.brick(rules.BRICK_W, rules.BRICK_H),
                            BRICK_COLOURS[row % len(BRICK_COLOURS)], tx=x, ty=y))

    # UFO Hierarchy: ufo -> dome & light_ring -> 4 lights
    ufo = root.add(Node("ufo", figures.ufo_body(2.0, 0.8), (0.5, 0.95, 0.5), ty=6.4))
    ufo.add(Node("ufo_dome", figures.ufo_dome(1.0, 0.5), (0.7, 1.0, 0.8), ty=0.15))
    ring = ufo.add(Node("ufo_light_ring"))
    for i in range(4):
        a = math.radians(90 * i)
        ring.add(Node("ufo_light_%d" % i, figures.ufo_light(0.12),
                      (1.0, 0.92, 0.2), tx=1.0 * math.cos(a), ty=0.35 * math.sin(a)))

    # Lives Display (3 Hearts)
    lives_group = root.add(Node("lives_display", tx=-8.2, ty=6.8))
    for i in range(3):
        lives_group.add(Node("heart_%d" % i, figures.heart(0.35), (0.95, 0.2, 0.3), tx=i * 0.8))

    # Arcade Controls Decoration (Bottom Bezel)
    controls = root.add(Node("controls_panel", tx=0.0, ty=-7.1))
    joy = controls.add(Node("joystick_base", figures.joystick_base(1.0, 0.3), (0.25, 0.25, 0.3), tx=-5.0))
    joy.add(Node("joystick_stick", figures.joystick_stick(0.12, 0.5), (0.6, 0.6, 0.6), ty=0.35))
    joy.add(Node("joystick_knob", figures.joystick_knob(0.2), (0.9, 0.15, 0.15), ty=0.6))
    controls.add(Node("button_1", figures.button(0.22), (0.9, 0.2, 0.2), tx=4.5))
    controls.add(Node("button_2", figures.button(0.22), (0.2, 0.8, 0.3), tx=5.2))
    controls.add(Node("button_3", figures.button(0.22), (0.2, 0.5, 0.9), tx=5.9))

    # Member 3: default joystick, capsule and hearts for any of them this scene
    # does not define itself (same names = yours are used instead).
    anim2d.ensure_nodes(root)
    return root


def sync(root, game, dt):
    """Copy the game state (plain numbers) onto the nodes before drawing.
    The 2D animation lives in anim2d.py (Member 3): ball, paddle, brick break /
    build, UFO path and lights, capsule, joystick, hearts, score pulse."""
    anim2d.sync(root, game, dt)


def compute_letterbox(width, height):
    """Calculate 4:3 letterbox viewport coordinates (vp_x, vp_y, vp_w, vp_h)."""
    target_aspect = (rules.WORLD_RIGHT - rules.WORLD_LEFT) / (rules.WORLD_TOP - rules.WORLD_BOTTOM)
    win_aspect = float(width) / max(1.0, float(height))

    if win_aspect > target_aspect:
        vp_w = int(height * target_aspect)
        vp_h = height
        vp_x = (width - vp_w) // 2
        vp_y = 0
    else:
        vp_w = width
        vp_h = int(width / target_aspect)
        vp_x = 0
        vp_y = (height - vp_h) // 2

    return vp_x, vp_y, max(1, vp_w), max(1, vp_h)


def screen_to_world(px, py, width, height):
    """Convert screen pixel coordinates (px, py, origin at top-left)
    to 2D world coordinates, respecting 4:3 letterboxing.
    """
    vp_x, vp_y, vp_w, vp_h = compute_letterbox(width, height)
    # Convert Tk top-left to OpenGL bottom-left
    gl_x = px
    gl_y = height - py

    # Normalize within viewport [0, 1]
    u = (gl_x - vp_x) / float(vp_w)
    v = (gl_y - vp_y) / float(vp_h)

    # Map to world coordinates
    wx = rules.WORLD_LEFT + u * (rules.WORLD_RIGHT - rules.WORLD_LEFT)
    wy = rules.WORLD_BOTTOM + v * (rules.WORLD_TOP - rules.WORLD_BOTTOM)
    return wx, wy


def draw(root, width, height, selected=None):
    """Draw one frame of the 2D view with letterboxing and filled polygons."""
    vp_x, vp_y, vp_w, vp_h = compute_letterbox(width, height)
    glViewport(vp_x, vp_y, vp_w, vp_h)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(rules.WORLD_LEFT, rules.WORLD_RIGHT, rules.WORLD_BOTTOM, rules.WORLD_TOP, -1.0, 1.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    glClear(GL_COLOR_BUFFER_BIT)

    # Draw the scene graph
    draw_tree(root, lambda node: _render_node(node, _inside(node, selected)))


def _inside(node, selected):
    """True if node is the selected node or one of its descendants."""
    while node is not None:
        if node is selected:
            return True
        node = node.parent
    return False


def _render_node(node, highlighted):
    """Draws a node's figure: filled interior + crisp outline."""
    if not node.figure:
        return

    # 1. Filled interior
    color = node.color or (0.8, 0.8, 0.8)
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_POLYGON)
    for x, y in node.figure:
        glVertex2f(x, y)
    glEnd()

    # 2. Outline (yellow if selected)
    if highlighted:
        glLineWidth(3.0)
        glColor3f(*SELECTED_COLOUR)
    else:
        glLineWidth(1.2)
        glColor3f(max(0.0, color[0] * 0.7), max(0.0, color[1] * 0.7), max(0.0, color[2] * 0.7))

    glBegin(GL_LINE_LOOP)
    for x, y in node.figure:
        glVertex2f(x, y)
    glEnd()


def point_in_polygon(px, py, polygon):
    """Ray casting algorithm: returns True if point (px, py) is inside polygon."""
    inside = False
    n = len(polygon)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def pick(root, px, py, width, height):
    """Mouse pixel -> world point -> inverse(world()) -> point-in-figure test.
    Returns the selected Node, or None.
    """
    vp_x, vp_y, vp_w, vp_h = compute_letterbox(width, height)
    gl_x = px
    gl_y = height - py

    # Check if click is inside letterbox viewport
    if not (vp_x <= gl_x <= vp_x + vp_w and vp_y <= gl_y <= vp_y + vp_h):
        return None

    wx, wy = screen_to_world(px, py, width, height)

    # Check visible nodes with figures. Test children first (reverse order of all_nodes)
    # so specific shapes (like UFO dome or light) are selected before their parent.
    candidates = [node for node in root.all_nodes() if node.visible and node.figure]
    for node in reversed(candidates):
        try:
            inv_world = matrices.inverse2(node.world())
            # Map world point to node's model coordinates
            (mx, my), = matrices.apply2(inv_world, [(wx, wy)])
            if point_in_polygon(mx, my, node.figure):
                return node
        except ValueError:
            continue

    return None
