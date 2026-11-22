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

class TestRaster(unittest.TestCase):

    def test_bresenham_0_0_to_5_2(self):
        import raster
        pts = raster.bresenham_line(0, 0, 5, 2)
        expected = [(0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)]
        self.assertEqual(pts, expected)

    def test_midpoint_circle_points_on_radius(self):
        import raster
        for r in (3, 5, 10, 15):
            pts = raster.midpoint_circle(0, 0, r)
            self.assertGreater(len(pts), 0)
            for x, y in pts:
                dist = math.hypot(x, y)
                self.assertLessEqual(abs(dist - r), 1.0,
                                     "Point (%d, %d) dist %f not within 1 of r=%d" % (x, y, dist, r))

    def test_screen_centre_is_world_origin(self):
        import render2d
        # Window 800 x 600 has center (400, 300)
        wx, wy = render2d.screen_to_world(400, 300, 800, 600)
        self.assertTrue(close((wx, wy), (0.0, 0.0)))
        # Letterbox test: wide window 1200 x 600 has center (600, 300) -> world (0, 0)
        wx2, wy2 = render2d.screen_to_world(600, 300, 1200, 600)
        self.assertTrue(close((wx2, wy2), (0.0, 0.0)))

    def test_pick_finds_paddle(self):
        import render2d
        root = render2d.build_scene()
        # Paddle is at (0, -6.5). Window 800 x 600 (4:3 aspect ratio).
        # In world: Y=-6.5 is near the bottom.
        # Screen Y = 600 * (7.5 - (-6.5)) / 15.0 = 600 * 14.0 / 15.0 = 560
        node = render2d.pick(root, 400, 560, 800, 600)
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "paddle")


# ======================================================================= Member 3: game
# Game rules, 2D animation and save / load. No window is opened: game.py and
# anim2d.py are plain numbers, which is exactly why they are easy to test.

class TestGame(unittest.TestCase):

    def setUp(self):
        import game as rules             # imported here like the GUI tests above
        self.rules = rules
        self.game = rules.Game(seed=1)
        self.game._build_bricks(animated=False)     # skip the pop-in animation

    def put_ball(self, x, y, vx, vy):
        """Ball in play at (x, y) with velocity (vx, vy)."""
        g = self.game
        g.state = self.rules.PLAY
        g.ball_x, g.ball_y, g.ball_vx, g.ball_vy = x, y, vx, vy
        g.ball_speed = math.hypot(vx, vy)

    def test_ball_bounces_off_right_wall(self):
        self.put_ball(9.5, 0.0, 4.0, -3.0)
        self.game.update(0.1)
        self.assertLess(self.game.ball_vx, 0.0)                       # now moving left
        self.assertLessEqual(self.game.ball_x, self.rules.WORLD_RIGHT - self.rules.BALL_RADIUS)
        self.assertTrue(close(self.game.ball_vy, -3.0))               # vy unchanged

    def test_brick_hit_scores_10(self):
        x, y = self.rules.brick_center(4, 5)                          # bottom row, (1.0, 1.6)
        self.put_ball(x, y - 0.8, 0.0, 6.0)                           # just below, going up
        self.game.update(0.1)
        self.assertFalse(self.game.bricks[4][5]["alive"])
        self.assertEqual(self.game.score, 10)
        self.assertEqual(self.game.bricks_left, 49)
        self.assertLess(self.game.ball_vy, 0.0)                       # bounced back down

    def test_ufo_faces_its_direction(self):
        """The heading is atan2(vy, vx) of the real velocity (checked against a
        finite difference of the path), and the saucer never tilts past 18 deg.
        (t = 4 s and 12 s are left out: the UFO turns round off screen there.)"""
        for t in (0.0, 1.3, 2.9, 7.7, 9.1, 13.5):
            self.game.time = t
            self.game._move_ufo(0.0)
            h = 1e-5
            x1, y1, _, _ = self.rules.ufo_path(t - h)
            x2, y2, _, _ = self.rules.ufo_path(t + h)
            expected = math.degrees(math.atan2(y2 - y1, x2 - x1))
            self.assertAlmostEqual(self.game.ufo_heading, expected, places=4)
            self.assertLessEqual(abs(self.game.ufo_angle), 18.0)

    def test_paddle_centre_sends_ball_up_and_edge_at_60_degrees(self):
        r = self.rules
        top = r.PADDLE_Y + r.PADDLE_HALF_HEIGHT + r.BALL_RADIUS
        self.put_ball(0.0, top + 0.05, 0.0, -6.0)                     # centre of the paddle
        self.game.update(0.05)
        self.assertGreater(self.game.ball_vy, 0.0)
        self.assertTrue(close(self.game.ball_vx, 0.0))
        self.put_ball(r.PADDLE_HALF_WIDTH, top + 0.05, 0.0, -6.0)     # right edge
        self.game.update(0.05)
        self.assertTrue(close(self.game.ball_vx, 6.0 * math.sin(math.radians(60)), 6))

    def test_fast_ball_does_not_tunnel_through_a_brick(self):
        """One frame of 0.3 s at 15 units/s is 4.5 units, far more than a brick
        is high. The sub-steps still catch the hit."""
        x, y = self.rules.brick_center(4, 5)
        self.put_ball(x, y - 3.0, 0.0, 15.0)
        self.game.update(0.3)
        self.assertFalse(self.game.bricks[4][5]["alive"])
        self.assertLess(self.game.ball_y, y)                          # it did not pass through

    def test_losing_the_ball_costs_a_life_and_serves_again(self):
        self.put_ball(-8.0, -7.3, 0.0, -6.0)                          # below the paddle
        self.game.update(0.1)
        self.assertEqual(self.game.lives, 2)
        self.assertEqual(self.game.state, self.rules.SERVE)
        self.assertEqual(self.game.heart_pop_index, 2)                # that heart pops
        self.assertTrue(close(self.game.ball_x, self.game.paddle_x))  # back on the paddle

    def test_game_over_after_the_last_life(self):
        self.game.lives = 1
        self.put_ball(-8.0, -7.3, 0.0, -6.0)
        self.game.update(0.1)
        self.assertEqual(self.game.state, self.rules.GAME_OVER)
        self.assertFalse(self.game.ball_visible)
        self.assertEqual(self.game.banner, "GAME OVER")
        self.game.update(5.0)                                         # no restart without attract
        self.assertEqual(self.game.state, self.rules.GAME_OVER)

    def test_last_brick_starts_a_faster_level(self):
        g = self.game
        for line in g.bricks:
            for brick in line:
                brick["alive"], brick["phase"], brick["visible"] = False, "gone", False
        g.bricks[4][5].update(alive=True, phase="idle", visible=True)
        g.bricks_left = 1
        speed_level_1 = g.current_ball_speed()
        x, y = self.rules.brick_center(4, 5)
        self.put_ball(x, y - 0.8, 0.0, 6.0)
        g.update(0.1)
        self.assertEqual(g.level, 2)
        self.assertEqual(g.state, self.rules.SERVE)
        for _ in range(60):
            g.update(1 / 60.0)                                        # the new wall appears
        self.assertEqual(g.bricks_left, 50)
        self.assertTrue(close(g.current_ball_speed(), speed_level_1 * 1.1))

    def test_wide_power_up_grows_smoothly_and_keeps_the_slider_value(self):
        g = self.game
        g.serve_timer = 1e9                                           # keep the ball on the paddle
        g.paddle_width = 1.2                                          # the GUI slider
        g.capsule_kind = "wide"
        g._catch_capsule()
        g.update(0.1)
        self.assertTrue(1.2 < g.paddle_width < 1.2 * 1.6)             # growing, not jumping
        for _ in range(30):
            g.update(0.1)
        self.assertTrue(close(g.paddle_width, 1.2 * 1.6, 2))
        self.assertEqual(g.paddle_base, 1.2)                          # slider untouched
        for _ in range(100):
            g.update(0.1)                                             # 10 s later it is over
        self.assertTrue(close(g.paddle_width, 1.2, 2))

    def test_attract_mode_keeps_the_ball_alive(self):
        g = self.rules.Game(seed=7)
        g.toggle_attract()
        for _ in range(60 * 120):                                     # two minutes at 60 FPS
            g.update(1 / 60.0)
        self.assertGreaterEqual(g.lives, 3)
        self.assertGreater(g.score, 200)

    def test_update_ignores_zero_negative_and_nan_dt(self):
        before = self.game.time
        for dt in (0.0, -1.0, float("nan")):
            self.game.update(dt)
        self.assertEqual(self.game.time, before)

    def test_circle_rect_contact_normals(self):
        contact = self.rules.circle_rect_contact
        nx, ny, depth = contact(0.0, 0.55, 0.3, 0.0, 0.0, 1.0, 0.3)   # on top
        self.assertTrue(close((nx, ny, depth), (0.0, 1.0, 0.05)))
        nx, ny, _ = contact(1.1, 0.4, 0.3, 0.0, 0.0, 1.0, 0.3)        # top-right corner
        self.assertTrue(close((nx, ny), (math.sqrt(0.5), math.sqrt(0.5))))
        self.assertIsNone(contact(0.0, 1.0, 0.3, 0.0, 0.0, 1.0, 0.3))  # too far away

    def test_attract_prediction_folds_between_the_walls(self):
        # A ball that would reach x = 11 bounces off the wall at 9.7 and ends at 8.4.
        self.assertTrue(close(self.rules.fold_between(11.0, -9.7, 9.7), 8.4))
        self.assertTrue(close(self.rules.fold_between(3.0, -9.7, 9.7), 3.0))


class TestAnimation2D(unittest.TestCase):

    def setUp(self):
        import anim2d
        import game as rules
        import render2d
        self.anim2d, self.rules = anim2d, rules
        self.game = rules.Game(seed=1)
        self.game._build_bricks(animated=False)
        self.root = render2d.build_scene()
        anim2d.sync(self.root, self.game)

    def test_joystick_knob_follows_the_tilted_stick(self):
        """world(knob) = T(panel) . T(base) . T(pivot) . R(tilt) . T(0, 0.25) . T(0, 0.25)
        (Member 2's joystick: base at (-5, -7.1), pivot 0.1 up, stick 0.25, knob 0.25.)"""
        self.game.joystick_tilt = -25.0
        self.anim2d.sync(self.root, self.game)
        knob = self.root.find("joystick_knob")
        (x, y), = mx.apply2(knob.world(), [(0, 0)])
        a = math.radians(-25.0)
        expected = (-5.0 - 0.5 * math.sin(a), -7.1 + 0.1 + 0.5 * math.cos(a))
        self.assertTrue(close((x, y), expected))

    def test_ufo_lights_ride_on_the_moving_ufo(self):
        for _ in range(30):
            self.game.update(0.1)
            self.anim2d.sync(self.root, self.game)
            ufo = mx.apply2(self.root.find("ufo").world(), [(0, 0)])[0]
            light = mx.apply2(self.root.find("ufo_light_2").world(), [(0, 0)])[0]
            self.assertTrue(close(math.dist(ufo, light), 1.0))        # always on the ring

    def test_broken_brick_shrinks_spins_falls_then_disappears(self):
        node = self.root.find("brick_0_0")
        base_x, base_y = self.rules.brick_center(0, 0)
        self.game._break_brick(0, 0)
        self.game._animate_bricks(0.2)
        self.anim2d.sync(self.root, self.game)
        self.assertTrue(node.visible)
        self.assertTrue(0.0 < node.sx < 1.0)
        self.assertNotEqual(node.angle, 0.0)
        self.assertLess(node.ty, base_y)
        self.game._animate_bricks(0.3)
        self.anim2d.sync(self.root, self.game)
        self.assertFalse(node.visible)

    def test_gui_size_on_an_idle_brick_is_kept(self):
        node = self.root.find("brick_2_3")
        node.sx = node.sy = 2.0                                       # the Size slider
        self.game.update(0.1)
        self.anim2d.sync(self.root, self.game)
        self.assertEqual(node.sx, 2.0)


class TestPersist(unittest.TestCase):

    def setUp(self):
        import tempfile
        import persist
        self.persist = persist
        self.folder = tempfile.TemporaryDirectory()
        self.path = self.folder.name + "/settings.json"

    def tearDown(self):
        self.folder.cleanup()

    def test_settings_round_trip(self):
        data = {"format": self.persist.FORMAT, "version": 1, "speed": 1.5, "view": "3D",
                "nodes_2d": {"ufo": {"color": [0.1, 0.2, 0.3], "size": 1.4}}}
        self.persist.save_settings(self.path, data)
        self.assertEqual(self.persist.load_settings(self.path), data)

    def test_missing_damaged_or_foreign_files_give_a_clear_error(self):
        with self.assertRaises(ValueError):
            self.persist.load_settings(self.path)                     # not saved yet
        for text in ("{broken", "[1, 2, 3]", '{"format": "something else", "version": 1}'):
            with open(self.path, "w") as file:
                file.write(text)
            with self.assertRaises(ValueError):
                self.persist.load_settings(self.path)

    def test_apply_settings_clamps_and_skips_bad_values(self):
        import types
        import game as rules
        import render2d
        calls = []
        app = types.SimpleNamespace(game=rules.Game(), scene2d=render2d.build_scene(),
                                    scene3d=Node("world", dim=3), gui=None,
                                    set_speed=lambda v: calls.append(("speed", v)),
                                    set_view=lambda v: calls.append(("view", v)))
        data = {"format": self.persist.FORMAT, "version": 1, "speed": 99, "view": "4D",
                "game": {"ball_speed": "fast", "paddle_width": 0.0, "ufo_orbit_speed": True},
                "nodes_2d": {"ufo": {"size": 50, "color": [2, -1, 0.5], "rotation": 270},
                             "bricks": {"rotation": 270},
                             "brick_0_0": {"visible": False},
                             "no_such_node": {"size": 2}}}
        self.persist.apply_settings(app, data)
        self.assertEqual(calls, [("speed", 3.0)])                     # clamped; "4D" ignored
        self.assertEqual(app.game.ball_speed, 6.0)                    # "fast" is not a number
        self.assertEqual(app.game.ufo_orbit_speed, 120.0)             # True is not a number
        self.assertEqual(app.game.paddle_base, 0.5)                   # clamped to the slider
        ufo = app.scene2d.find("ufo")
        self.assertEqual((ufo.sx, ufo.color), (3.0, (1.0, 0.0, 0.5)))   # clamped
        self.assertEqual(ufo.angle, 0.0)            # the animation owns the UFO's rotation
        self.assertEqual(app.scene2d.find("bricks").angle, -90.0)     # 270 wrapped
        self.assertTrue(app.scene2d.find("brick_0_0").visible)        # the game decides that


# ======================================================================= Member 4: 3D
# TODO(M4): replace the skip markers with the real tests.

class TestFigures3D(unittest.TestCase):
    """Member 4's 3D figures and orbit (tests added during integration; the code under test is unchanged)."""

    def setUp(self):
        import figures
        self.figures = figures

    def test_face_tables_are_valid(self):
        """Every face index is in range and every face has at least 3 vertices."""
        shapes = {"bevelled brick": self.figures.bevelled_brick(1.8, 0.6, 0.6), "trophy": self.figures.trophy(),
                  "star": self.figures.star(), "box": self.figures.box(3.0, 0.4, 0.6)}
        for name, (vertices, faces) in shapes.items():
            for face in faces:
                self.assertGreaterEqual(len(face), 3, name)
                self.assertTrue(all(0 <= i < len(vertices) for i in face), name)

    def test_brick_normals_point_outwards(self):
        """Every brick face normal (Newell's method, normalised) has length 1 and points away from the centre."""
        vertices, faces = self.figures.bevelled_brick(1.8, 0.6, 0.6)
        for face in faces:
            points = [vertices[i] for i in face]
            n = [0.0, 0.0, 0.0]
            for (x1, y1, z1), (x2, y2, z2) in zip(points, points[1:] + points[:1]):
                n[0] += (y1 - y2) * (z1 + z2)
                n[1] += (z1 - z2) * (x1 + x2)
                n[2] += (x1 - x2) * (y1 + y2)
            length = math.sqrt(sum(c * c for c in n))
            unit = [c / length for c in n]
            self.assertAlmostEqual(math.sqrt(sum(c * c for c in unit)), 1.0)
            centre = [sum(p[k] for p in points) / len(points) for k in range(3)]
            self.assertGreater(sum(u * c for u, c in zip(unit, centre)), 0.0)   # the brick's centre is the origin

    def test_star_orbit_radius(self):
        """The orbiting star stays at distance r = 2 from the trophy's axis."""
        import game as rules
        import render3d
        root, game = render3d.build_scene(), rules.Game(seed=1)
        star = root.find("star")
        for _ in range(60):
            render3d.sync(root, game, 0.07)
            self.assertAlmostEqual(math.hypot(star.tx, star.tz), 2.0)


# ======================================================================= Member 1: arcade-pixel overlay

class TestArcadePixels(unittest.TestCase):

    def test_score_digits_are_drawn_with_the_raster_algorithms(self):
        """A seven-segment 8 lights more arcade pixels than a 1, and every pixel stays in the digit's box."""
        import hud2d
        fill8, outline8 = hud2d.digit_pixels(8)
        fill1, outline1 = hud2d.digit_pixels(1)
        self.assertGreater(len(fill8 | outline8), len(fill1 | outline1))
        for x, y in fill8 | outline8:
            self.assertTrue(0 <= x <= hud2d.DIGIT_W and 0 <= y <= hud2d.DIGIT_H)


if __name__ == "__main__":
    unittest.main()
