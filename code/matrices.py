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


def inverse2(M):
    """Inverse of a 2D affine matrix  [[a, b, tx], [c, d, ty], [0, 0, 1]].

    Used by click-to-select: it takes a world point back into the figure's
    own model coordinates, where a point-in-polygon test is easy.
    The 2x2 part [[a, b], [c, d]] is inverted with the 1/det formula, then the
    translation is undone:  t' = -(A^-1 . t).
    """
    a, b, tx = M[0]
    c, d, ty = M[1]
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError("matrix cannot be inverted (a scale of 0 squashes the figure flat)")
    ia, ib = d / det, -b / det
    ic, id_ = -c / det, a / det
    return [[ia, ib, -(ia * tx + ib * ty)],
            [ic, id_, -(ic * tx + id_ * ty)],
            [0.0, 0.0, 1.0]]

# ======================================================================= 3D (4x4)


def identity4():
    """The 4x4 identity matrix."""
    return [[1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def translate3(tx, ty, tz):
    """Move by (tx, ty, tz). The translation sits in the 4th column."""
    return [[1.0, 0.0, 0.0, float(tx)],
            [0.0, 1.0, 0.0, float(ty)],
            [0.0, 0.0, 1.0, float(tz)],
            [0.0, 0.0, 0.0, 1.0]]


def scale3(sx, sy, sz):
    """Scale about the origin along x, y and z."""
    return [[float(sx), 0.0, 0.0, 0.0],
            [0.0, float(sy), 0.0, 0.0],
            [0.0, 0.0, float(sz), 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def rot_x(theta):
    """Rotate about the x axis (y turns towards z), theta in radians."""
    c, s = math.cos(theta), math.sin(theta)
    return [[1.0, 0.0, 0.0, 0.0],
            [0.0, c, -s, 0.0],
            [0.0, s, c, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def rot_y(theta):
    """Rotate about the y axis (z turns towards x), theta in radians."""
    c, s = math.cos(theta), math.sin(theta)
    return [[c, 0.0, s, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-s, 0.0, c, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def rot_z(theta):
    """Rotate about the z axis (x turns towards y), theta in radians.
    This is rotate2 with an untouched z row and column."""
    c, s = math.cos(theta), math.sin(theta)
    return [[c, -s, 0.0, 0.0],
            [s, c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]]


def apply3(M, vertices):
    """Transform a list of 3D points: each (x, y, z) becomes M . (x, y, z, 1)."""
    result = []
    for x, y, z in vertices:
        result.append((M[0][0] * x + M[0][1] * y + M[0][2] * z + M[0][3],
                       M[1][0] * x + M[1][1] * y + M[1][2] * z + M[1][3],
                       M[2][0] * x + M[2][1] * y + M[2][2] * z + M[2][3]))
    return result

# ======================================================================= to OpenGL


def embed3(M):
    """Turn a 2D 3x3 matrix into the equivalent 4x4 one.

    The 2x2 rotation/scale part stays top-left, the 2D translation moves to the
    4th column, and z is left alone (z' = z).
    """
    return [[M[0][0], M[0][1], 0.0, M[0][2]],
            [M[1][0], M[1][1], 0.0, M[1][2]],
            [0.0, 0.0, 1.0, 0.0],
            [M[2][0], M[2][1], 0.0, M[2][2]]]


def to_gl(M):
    """Flatten a matrix into the 16 floats glMultMatrixf expects.

    OpenGL wants COLUMN-MAJOR order: all of column 0, then column 1, ...
    Our matrices are stored row by row, so we read them column by column.
    A 2D 3x3 matrix is embedded into 4x4 first.
    Example: to_gl(translate3(1, 2, 3)) has 1, 2, 3 at indices 12, 13, 14.
    """
    if len(M) == 3:
        M = embed3(M)
    return [float(M[row][col]) for col in range(4) for row in range(4)]
