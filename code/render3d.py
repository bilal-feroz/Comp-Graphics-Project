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

from OpenGL.GL import (GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST,
                       GL_LINE_LOOP, GL_POLYGON, GL_LIGHTING, GL_LIGHT0,
                       GL_COLOR_MATERIAL, GL_NORMALIZE, GL_FRONT_AND_BACK,
                       GL_AMBIENT_AND_DIFFUSE, GL_POSITION, GL_DIFFUSE,
                       GL_MODELVIEW, GL_PROJECTION, glBegin, glClear,
                       glColor3f, glEnable, glEnd, glLineWidth,
                       glLoadIdentity, glMatrixMode, glVertex3f, glViewport,
                       glNormal3f, glLightfv, glMaterialfv, glColorMaterial)

from OpenGL.GLU import gluLookAt, gluPerspective
import math
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
    trophy.add(Node("star", figures.star(), (1.0, 1.0, 0.6), dim=3, tx=2.0, ty=0.5))
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
  
    yaw_r = math.radians(camera.yaw)
    pitch_r = math.radians(camera.pitch)

    cx = camera.distance * math.cos(pitch_r) * math.sin(yaw_r)
    cy = 1.0 + camera.distance * math.sin(pitch_r)
    cz = camera.distance * math.cos(pitch_r) * math.cos(yaw_r)

    gluLookAt(
        cx, cy, cz,
        0.0, 1.0, 0.0,
        0.0, 1.0, 0.0
    )
    glEnable(GL_DEPTH_TEST)

    
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

   
    glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 8.0, 10.0, 1.0))

   
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))

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

    glColor3f(*(SELECTED_COLOUR if highlighted else node.color))

    for face in faces:
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]

       
        a = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        b = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])

        normal = (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

        glBegin(GL_POLYGON)
        glNormal3f(*normal)

        for index in face:
            glVertex3f(*vertices[index])

        glEnd()



def on_drag(camera, dx, dy):
    """Orbit the camera when the mouse is dragged."""
    yaw = camera.yaw + dx * 0.5
    pitch = camera.pitch + dy * 0.5

   
    pitch = max(-80.0, min(80.0, pitch))

    camera.set(yaw=yaw, pitch=pitch)


def on_wheel(camera, steps):
    """Zoom the camera in and out."""
    distance = camera.distance - steps * 1.5

   
    distance = max(8.0, min(40.0, distance))

    camera.set(distance=distance)

