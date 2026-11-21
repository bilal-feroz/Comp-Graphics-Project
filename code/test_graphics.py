"""
test_graphics.py - unit tests for the whole project.

Run from the code/ folder:      python -m unittest -v

Member 1 owns this file. Every member adds at least 2 tests in their own
section and runs the whole file before opening a pull request.
"""
import math
import unittest

import matrices as mx
from scene import Node


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

    def test_trs_order_scales_then_rotates_then_translates(self):
        M = mx.compose(mx.translate2(5, 0), mx.rotate2(math.radians(90)), mx.scale2(2, 2))
        # (1, 0) --scale 2--> (2, 0) --rotate 90--> (0, 2) --move (5, 0)--> (5, 2)
        (x, y), = mx.apply2(M, [(1, 0)])
        self.assertTrue(close((x, y), (5, 2)))

    def test_inverse2_undoes_the_transform(self):
        M = mx.compose(mx.translate2(3, -2), mx.rotate2(math.radians(30)), mx.scale2(2, 0.5))
        self.assertMatrixClose(mx.mul(mx.inverse2(M), M), mx.identity3())

    def test_inverse2_refuses_a_zero_scale(self):
        with self.assertRaises(ValueError):
            mx.inverse2(mx.scale2(0, 1))

    def test_to_gl_translate3_puts_translation_at_12_13_14(self):
        flat = mx.to_gl(mx.translate3(1, 2, 3))
        self.assertEqual(len(flat), 16)
        self.assertEqual(flat[12:15], [1.0, 2.0, 3.0])

    def test_to_gl_embeds_a_2d_matrix(self):
        flat = mx.to_gl(mx.translate2(4, 5))
        self.assertEqual(flat[12:16], [4.0, 5.0, 0.0, 1.0])
        self.assertEqual(flat[10], 1.0)        # z is left unchanged

    def test_rot_y_90_degrees_maps_z_axis_to_x_axis(self):
        (point,) = mx.apply3(mx.rot_y(math.radians(90)), [(0, 0, 1)])
        self.assertTrue(close(point, (1, 0, 0)))


# ======================================================================= Member 1: scene graph

class TestSceneGraph(unittest.TestCase):

    @staticmethod
    def origin_in_world(node):
        """Where the node's model origin (0, 0) ends up in the world."""
        return mx.apply2(node.world(), [(0, 0)])[0]

    def test_child_follows_parent(self):
        ufo = Node("ufo", tx=2, ty=3)
        light = ufo.add(Node("light", tx=1))
        before = self.origin_in_world(light)              # (3, 3)
        ufo.tx += 4                                       # move only the parent
        ufo.ty -= 1
        after = self.origin_in_world(light)
        self.assertTrue(close((after[0] - before[0], after[1] - before[1]), (4, -1)))

    def test_child_orbits_when_parent_rotates(self):
        ring = Node("ring", angle=90)
        light = ring.add(Node("light", tx=1))
        self.assertTrue(close(self.origin_in_world(light), (0, 1)))

    def test_world_of_root_is_its_local(self):
        root = Node("world", tx=1, angle=30, sx=2)
        self.assertEqual(root.world(), root.local())

    def test_child_follows_parent_in_3d(self):
        trophy = Node("trophy", dim=3, tx=1, ty=2, tz=3)
        star = trophy.add(Node("star", dim=3, tx=2))
        (point,) = mx.apply3(star.world(), [(0, 0, 0)])
        self.assertTrue(close(point, (3, 2, 3)))

    def test_find_and_all_nodes_walk_the_tree_parent_first(self):
        root = Node("world")
        a = root.add(Node("a"))
        a.add(Node("a1"))
        root.add(Node("b"))
        self.assertEqual([n.name for n in root.all_nodes()], ["world", "a", "a1", "b"])
        self.assertIs(root.find("a1"), a.children[0])
        self.assertIsNone(root.find("missing"))

    def test_add_rejects_mixing_2d_and_3d(self):
        with self.assertRaises(ValueError):
            Node("world").add(Node("cube", dim=3))


# ======================================================================= Member 1: GUI input validation

class TestGuiValidation(unittest.TestCase):

    def setUp(self):
        import gui                       # imported here: only these tests need Tk
        self.gui = gui

    def test_entry_accepts_partial_numbers_and_refuses_letters(self):
        for text in ("", "-", "1.", "-0.5", "12"):
            self.assertTrue(self.gui.is_partial_number(text), text)
        for text in ("abc", "1e5", "1-", "--1", "1.2.3"):
            self.assertFalse(self.gui.is_partial_number(text), text)

    def test_parse_number_clamps_to_the_slider_range(self):
        self.assertEqual(self.gui.parse_number("5", 0.1, 3.0), 3.0)
        self.assertEqual(self.gui.parse_number("-2", 0.1, 3.0), 0.1)
        self.assertEqual(self.gui.parse_number("1.5", 0.1, 3.0), 1.5)

    def test_parse_number_rejects_text_that_is_not_a_number(self):
        for text in ("", "-", "nan", "inf"):
            with self.assertRaises(ValueError):
                self.gui.parse_number(text, 0, 1)

    def test_wrap_degrees_keeps_the_rotation_slider_in_range(self):
        self.assertEqual(self.gui.wrap_degrees(270), -90)
        self.assertEqual(self.gui.wrap_degrees(-180), 180)
        self.assertEqual(self.gui.wrap_degrees(720), 0)


# ======================================================================= Member 2: raster + 2D
# TODO(M2): replace the skip markers with the real tests.

class TestRaster(unittest.TestCase):

    @unittest.skip("TODO(M2): Bresenham (0,0)->(5,2) gives (0,0) (1,0) (2,1) (3,1) (4,2) (5,2)")
    def test_bresenham_0_0_to_5_2(self):
        pass

    @unittest.skip("TODO(M2): every midpoint-circle point lies within 1 pixel of radius r")
    def test_midpoint_circle_points_on_radius(self):
        pass

    @unittest.skip("TODO(M2): screen-to-world maps the window centre to (0, 0)")
    def test_screen_centre_is_world_origin(self):
        pass


# ======================================================================= Member 3: game
# TODO(M3): replace the skip markers with the real tests.

class TestGame(unittest.TestCase):

    @unittest.skip("TODO(M3): a ball moving right at the right wall ends with negative vx")
    def test_ball_bounces_off_right_wall(self):
        pass

    @unittest.skip("TODO(M3): hitting a brick removes it and adds 10 to the score")
    def test_brick_hit_scores_10(self):
        pass

    @unittest.skip("TODO(M3): the UFO heading equals atan2(vy, vx) of its velocity")
    def test_ufo_faces_its_direction(self):
        pass


# ======================================================================= Member 4: 3D
# TODO(M4): replace the skip markers with the real tests.

class TestFigures3D(unittest.TestCase):

    @unittest.skip("TODO(M4): every face index is in range and every face has 3+ vertices")
    def test_face_tables_are_valid(self):
        pass

    @unittest.skip("TODO(M4): every brick normal has length 1 and points away from the centre")
    def test_brick_normals_point_outwards(self):
        pass

    @unittest.skip("TODO(M4): the orbiting star stays at distance r from the trophy axis")
    def test_star_orbit_radius(self):
        pass


if __name__ == "__main__":
    unittest.main()
