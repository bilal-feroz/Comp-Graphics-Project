"""
scene.py - the scene graph.                                               [Member 1]

Every object in the game is a Node. A Node has
  * a figure: its vertices in MODEL coordinates, centred on the origin
    (2D: [(x, y), ...]   3D: (vertices, faces)   None: a group node),
  * a LOCAL transform: where it sits relative to its parent,
  * children that move with it.

The one rule to remember (draw it as a tree in the presentation):

        world(node) = world(parent) . local(node)

so moving, turning or scaling a parent automatically does the same to every
child. That is how the UFO's lights orbit the UFO while the UFO flies, and how
the joystick knob stays on the end of the stick.
"""
import math

import matrices as mx

# The transform fields a Node accepts as keyword arguments,
# e.g.  Node("paddle", figure, colour, ty=-6.5)
TRANSFORM_FIELDS = ("tx", "ty", "tz", "angle", "rx", "ry", "rz", "sx", "sy", "sz")


class Node:
    """One object (or group of objects) in the scene graph."""

    def __init__(self, name, figure=None, color=(1.0, 1.0, 1.0), dim=2, **transform):
        if dim not in (2, 3):
            raise ValueError("dim must be 2 or 3")
        self.name = name
        self.figure = figure          # vertex list, (vertices, faces), or None for a group
        self.color = tuple(color)     # (r, g, b), each 0..1
        self.dim = dim                # 2 -> 3x3 matrices, 3 -> 4x4 matrices
        self.visible = True           # a hidden node hides its whole subtree
        self.parent = None
        self.children = []

        # Local transform. Angles are in DEGREES (easy to type in the GUI).
        self.tx = self.ty = self.tz = 0.0      # translation
        self.angle = 0.0                       # 2D rotation about z
        self.rx = self.ry = self.rz = 0.0      # 3D rotations about x, y, z
        self.sx = self.sy = self.sz = 1.0      # scale
        for field, value in transform.items():
            if field not in TRANSFORM_FIELDS:
                raise TypeError("unknown transform field %r" % field)
            setattr(self, field, float(value))

    def __repr__(self):
        return "Node(%r)" % self.name

    def local(self):
        """This node's own transform matrix:  T . R . S

        Read right to left: scale the figure about its own centre, rotate it
        about its own centre, THEN move it into place. Doing T before R would
        swing the object around the parent's origin instead of turning it.
        """
        if self.dim == 2:
            return mx.compose(mx.translate2(self.tx, self.ty),
                              mx.rotate2(math.radians(self.angle)),
                              mx.scale2(self.sx, self.sy))
        return mx.compose(mx.translate3(self.tx, self.ty, self.tz),
                          mx.rot_z(math.radians(self.rz)),
                          mx.rot_y(math.radians(self.ry)),
                          mx.rot_x(math.radians(self.rx)),
                          mx.scale3(self.sx, self.sy, self.sz))
