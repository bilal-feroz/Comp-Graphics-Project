"""
test_graphics.py - unit tests for the whole project.

Run from the code/ folder:      python -m unittest -v

Member 1 owns this file. Every member adds at least 2 tests in their own
section and runs the whole file before opening a pull request.
"""
import math
import unittest

import matrices as mx


def close(a, b, places=9):
    """True when two numbers (or two flat sequences of numbers) are equal
    up to rounding error."""
    if isinstance(a, (int, float)):
        return round(a - b, places) == 0
    return len(a) == len(b) and all(close(x, y, places) for x, y in zip(a, b))


# ======================================================================= Member 1: matrices

class TestMatrices(unittest.TestCase):

    def assertMatrixClose(self, A, B):
        for row_a, row_b in zip(A, B):
            self.assertTrue(close(row_a, row_b), "%s != %s" % (A, B))

    def test_mul_matches_hand_worked_3x3_product(self):
        A = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        B = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        # Worked by hand: row 1 of A . column 1 of B = 1*9 + 2*6 + 3*3 = 30, ...
        expected = [[30, 24, 18], [84, 69, 54], [138, 114, 90]]
        self.assertEqual(mx.mul(A, B), expected)

    def test_rotate2_90_degrees_maps_x_axis_to_y_axis(self):
        (x, y), = mx.apply2(mx.rotate2(math.radians(90)), [(1, 0)])
        self.assertTrue(close((x, y), (0, 1)))
