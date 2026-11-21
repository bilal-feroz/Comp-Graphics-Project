"""
matrices.py - our own 3x3 (2D) and 4x4 (3D) matrix functions.            [Member 1]

Why this file exists: the brief says object transformations must use OUR
matrices. We never call glTranslatef / glRotatef / glScalef on objects;
OpenGL only receives the finished matrix through glMultMatrixf (see to_gl).

Conventions (worth saying out loud in the presentation):
  * A matrix is a list of rows, so M[row][col].
  * Points are COLUMN vectors and are transformed as  p' = M . p
  * Homogeneous coordinates: a 2D point (x, y) is used as (x, y, 1) and a 3D
    point (x, y, z) as (x, y, z, 1). That extra 1 is what lets a translation
    be written as a matrix multiplication.
  * A composite transform is read RIGHT TO LEFT:  T . R . S  means
    "scale first, then rotate, then translate".
  * Angles are in RADIANS here (like math.sin). Node keeps degrees, because
    people type degrees into the GUI, and converts when it builds a matrix.
"""
import math

# ======================================================================= 2D (3x3)


def identity3():
    """The 3x3 identity matrix: leaves every point where it is."""
    return [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]


def translate2(tx, ty):
    """Move by (tx, ty):   x' = x + tx,   y' = y + ty."""
    return [[1.0, 0.0, float(tx)],
            [0.0, 1.0, float(ty)],
            [0.0, 0.0, 1.0]]


def scale2(sx, sy):
    """Scale about the origin:   x' = sx * x,   y' = sy * y."""
    return [[float(sx), 0.0, 0.0],
            [0.0, float(sy), 0.0],
            [0.0, 0.0, 1.0]]


def rotate2(theta):
    """Rotate counter-clockwise by theta radians about the origin:
        x' = x cos(theta) - y sin(theta)
        y' = x sin(theta) + y cos(theta)
    """
    c, s = math.cos(theta), math.sin(theta)
    return [[c, -s, 0.0],
            [s, c, 0.0],
            [0.0, 0.0, 1.0]]


def mul(A, B):
    """Matrix product A . B (works for 3x3 and 4x4).

    Entry (i, j) of the result = row i of A  "dot"  column j of B.
    Order matters: mul(A, B) applies B to the point first, then A.
    """
    rows, inner, cols = len(A), len(B), len(B[0])
    return [[sum(A[i][k] * B[k][j] for k in range(inner)) for j in range(cols)]
            for i in range(rows)]


def apply2(M, vertices):
    """Transform a list of 2D points: each (x, y) becomes M . (x, y, 1)."""
    result = []
    for x, y in vertices:
        result.append((M[0][0] * x + M[0][1] * y + M[0][2],
                       M[1][0] * x + M[1][1] * y + M[1][2]))
    return result


def compose(*matrices):
    """Multiply several matrices left to right:  compose(T, R, S) = T . R . S

    Lets us write a transformation plan exactly as it appears in the report,
    e.g.  light = T(ufo) . R(heading) . R(w t) . T(r, 0).
    The RIGHTMOST matrix is the one applied to the point first.
    """
    result = matrices[0]
    for M in matrices[1:]:
        result = mul(result, M)
    return result
