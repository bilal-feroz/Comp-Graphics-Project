"""
game.py - game state and rules. NO OpenGL calls in this file.             [Member 3]

Everything here is plain numbers in WORLD units:
    x from -10 to 10, y from -7.5 to 7.5, origin at the centre of the field.
render2d.py and render3d.py only READ this state (in their sync functions),
so the same game is shown in both views.

STARTER VERSION by Member 1 (lead) so the main loop, Pause, the speed slider
and the arrow keys can be tested end to end. Member 3 owns this file and
replaces the TODOs; please keep the attribute names the GUI uses:
    ball_speed, ufo_orbit_speed, paddle_width   (Game tuning sliders)
    paddle_input, toggle_attract()              (arrow keys, M key)
"""
import math

WORLD_LEFT, WORLD_RIGHT = -10.0, 10.0
WORLD_BOTTOM, WORLD_TOP = -7.5, 7.5

BALL_RADIUS = 0.3
PADDLE_Y = -6.5
PADDLE_HALF_WIDTH = 1.5       # at paddle_width = 1
PADDLE_SPEED = 12.0           # world units per second

BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_W, BRICK_H = 1.8, 0.6
BRICK_TOP_Y = 5.0             # centre of the top row


def brick_center(row, col):
    """World position of brick (row, col). Row 0 is the top row."""
    x = WORLD_LEFT + 1.0 + col * (BRICK_W + 0.2)
    y = BRICK_TOP_Y - row * (BRICK_H + 0.25)
    return x, y
