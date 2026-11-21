"""
render3d.py - draws the 3D view.                                          [Member 4]

PLACEHOLDER by Member 1 (lead): wireframe boxes and a fixed camera, so the
2D/3D switch and the object selector can be tested. Member 4 replaces the
TODOs but keeps these names, because main.py and gui.py call them:

    build_scene()                                  -> root Node (dim=3)
    sync(root, game, dt)                           copy the game state onto the nodes
    draw(root, width, height, camera, selected)    draw one frame
    on_drag(camera, dx, dy)                        mouse dragged by (dx, dy) pixels
    on_wheel(camera, steps)                        wheel: +1 = up / away, -1 = down

`camera` is gui.CameraControls. Read camera.yaw, camera.pitch (degrees) and
camera.distance (world units); change it with camera.set(yaw=..., pitch=...,
distance=...) so the sliders follow the mouse.

TODO(M4): bevelled bricks, trophy and star from vertex/face tables, gluSphere
ball, GL_LIGHTING + normals + glMaterial, orbit camera from the sliders
(gluLookAt), mouse orbit and zoom, trophy turntable and orbiting star.
"""
from OpenGL.GL import (GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_LINE_LOOP,
                       GL_MODELVIEW, GL_PROJECTION, glBegin, glClear, glColor3f, glEnable,
                       glEnd, glLineWidth, glLoadIdentity, glMatrixMode, glVertex3f,
                       glViewport)
from OpenGL.GLU import gluLookAt, gluPerspective

import figures
import game as rules
from scene import Node
from scene import draw as draw_tree

SELECTED_COLOUR = (1.0, 1.0, 0.0)


def build_scene():
    """The 3D scene graph. Same x and y as the 2D field, z points to the camera.
    Shared objects use the same names as in 2D, so the selection survives V."""
    root = Node("world", dim=3)
    root.add(Node("paddle", figures.box(2 * rules.PADDLE_HALF_WIDTH, 0.4, 0.6),
                  (0.2, 0.85, 1.0), dim=3, ty=rules.PADDLE_Y))
    root.add(Node("ball", figures.box(0.6, 0.6, 0.6), (1.0, 1.0, 1.0), dim=3))
    bricks = root.add(Node("bricks", dim=3))
    for row in range(rules.BRICK_ROWS):
        for col in range(rules.BRICK_COLS):
            x, y = rules.brick_center(row, col)
            bricks.add(Node("brick_%d_%d" % (row, col),
                            figures.box(rules.BRICK_W, rules.BRICK_H, 0.6),
                            (0.9, 0.45, 0.3), dim=3, tx=x, ty=y))
    trophy = root.add(Node("trophy", figures.box(1.2, 2.0, 1.2), (1.0, 0.84, 0.0),
                           dim=3, ty=9.0, tz=-4.0))
    trophy.add(Node("star", figures.box(0.4, 0.4, 0.4), (1.0, 1.0, 0.6), dim=3, tx=2.0, ty=0.5))
    return root


def sync(root, game, dt):
    """Copy the game state onto the 3D nodes (same numbers as the 2D view)."""
    ball = root.find("ball")
    ball.tx, ball.ty, ball.rz = game.ball_x, game.ball_y, game.ball_spin
    paddle = root.find("paddle")
    paddle.tx, paddle.sx = game.paddle_x, game.paddle_width
    for node in root.find("bricks").children:
        row, col = (int(n) for n in node.name.split("_")[1:])
        node.visible = game.bricks[row][col]["alive"]
    root.find("trophy").ry += 45.0 * dt    # TODO(M4): turntable + orbiting star


def draw(root, width, height, camera, selected=None):
    """Draw one frame of the 3D view."""
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, width / float(max(height, 1)), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # TODO(M4): orbit camera built from camera.yaw, camera.pitch, camera.distance.
    gluLookAt(0.0, -6.0, 24.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0)
    glEnable(GL_DEPTH_TEST)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw_tree(root, lambda node: _wireframe(node, _inside(node, selected)))


def _inside(node, selected):
    while node is not None:
        if node is selected:
            return True
        node = node.parent
    return False


def _wireframe(node, highlighted):
    vertices, faces = node.figure
    glLineWidth(2.5 if highlighted else 1.0)
    glColor3f(*(SELECTED_COLOUR if highlighted else node.color))
    for face in faces:
        glBegin(GL_LINE_LOOP)
        for index in face:
            glVertex3f(*vertices[index])
        glEnd()


def on_drag(camera, dx, dy):
    """TODO(M4): orbit, e.g. camera.set(yaw=camera.yaw + dx * 0.5, pitch=camera.pitch + dy * 0.5)."""


def on_wheel(camera, steps):
    """TODO(M4): zoom, e.g. camera.set(distance=camera.distance - steps)."""
