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


class Game:
    """The whole game state. update(dt) moves it forward by dt seconds."""

    def __init__(self):
        # Values the GUI's "Game tuning" sliders change.
        self.ball_speed = 6.0         # world units per second
        self.ufo_orbit_speed = 120.0  # degrees per second
        self.paddle_width = 1.0       # scale factor of the paddle
        self.reset()

    def reset(self):
        """Start a new game (R key / Reset button)."""
        self.time = 0.0
        self.ball_x, self.ball_y = 0.0, -5.0
        self.ball_vx, self.ball_vy = 3.6, 4.8
        self.ball_spin = 0.0          # degrees
        self.paddle_x = 0.0
        self.paddle_input = 0         # -1 left, 0 still, +1 right (set by gui.py)
        self.attract = False          # M key: the paddle plays by itself
        self.bricks = [[{"alive": True, "scale": 1.0, "alpha": 1.0}
                        for _ in range(BRICK_COLS)] for _ in range(BRICK_ROWS)]
        self.score, self.lives, self.level = 0, 3, 1
        self.ufo_light_angle = 0.0    # degrees, the light ring around the UFO

    def toggle_attract(self):
        """M key. TODO(M3): in attract mode the paddle follows the ball."""
        self.attract = not self.attract

    def update(self, dt):
        """Advance the game by dt seconds (dt already includes the speed slider)."""
        self.time += dt
        self._move_paddle(dt)
        self._move_ball(dt)
        self.ufo_light_angle = (self.ufo_light_angle + self.ufo_orbit_speed * dt) % 360.0
        # TODO(M3): paddle and brick collisions, score, lives, game over,
        #           UFO on a curved path, power-up capsule, joystick, attract mode

    def _move_paddle(self, dt):
        self.paddle_x += self.paddle_input * PADDLE_SPEED * dt
        half = PADDLE_HALF_WIDTH * self.paddle_width
        self.paddle_x = max(WORLD_LEFT + half, min(WORLD_RIGHT - half, self.paddle_x))

    def _move_ball(self, dt):
        # Keep the direction of travel but use the speed from the slider.
        speed = math.hypot(self.ball_vx, self.ball_vy)
        if speed > 0:
            self.ball_vx *= self.ball_speed / speed
            self.ball_vy *= self.ball_speed / speed
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt
        self.ball_spin = (self.ball_spin + 360.0 * dt) % 360.0

        # Bounce off the side walls and the ceiling.
        if self.ball_x > WORLD_RIGHT - BALL_RADIUS:
            self.ball_x, self.ball_vx = WORLD_RIGHT - BALL_RADIUS, -abs(self.ball_vx)
        if self.ball_x < WORLD_LEFT + BALL_RADIUS:
            self.ball_x, self.ball_vx = WORLD_LEFT + BALL_RADIUS, abs(self.ball_vx)
        if self.ball_y > WORLD_TOP - BALL_RADIUS:
            self.ball_y, self.ball_vy = WORLD_TOP - BALL_RADIUS, -abs(self.ball_vy)

        # TODO(M3): lose a life here. For now the ball is served again.
        if self.ball_y < WORLD_BOTTOM - 1.0:
            self.ball_x, self.ball_y = self.paddle_x, PADDLE_Y + 1.0
            self.ball_vy = abs(self.ball_vy)
