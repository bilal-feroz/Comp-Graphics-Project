"""
game.py - Breakout rules and the numbers behind every animation.        [Member 3]

NO OpenGL calls in this file. Everything is plain numbers in WORLD units:
    x from -10 to 10, y from -7.5 to 7.5, origin at the centre of the field.
That gives two big advantages:
  * the same game is shown by both views: anim2d.py (2D) and render3d.sync (3D)
    only READ these numbers and copy them onto their scene-graph nodes,
  * every rule can be unit-tested without opening a window.

One call to update(dt) moves the whole game forward by dt seconds
(dt already includes the speed slider; when paused, update is not called):

    power-up timers -> paddle -> joystick -> UFO on its curved path
    -> ball (in small sub-steps, with collisions) -> capsule
    -> brick, heart and score animations

The game is a small state machine:

    SERVE --(1.2 s, or the Up key)--> PLAY
    PLAY  --(ball lost, lives left)--> SERVE
    PLAY  --(last brick broken)------> SERVE  (next level, faster ball)
    PLAY  --(ball lost, no lives)----> GAME_OVER
    GAME_OVER --(R key, or 3 s in attract mode)--> new game

Attribute names that other files use (please keep them):
    gui.py      ball_speed, ufo_orbit_speed, paddle_width   (Game tuning sliders)
                paddle_input, toggle_attract(), launch()    (arrow keys, M, Up)
                score, lives, level, high_score, attract    (status bar)
    main.py     update(dt), reset(), pop_events()
    anim2d.py / render3d.py   ball_*, paddle_*, bricks, ufo_*, capsule_*,
                joystick_tilt, score_pulse, heart_pop_*

Written by Member 3 with help from Claude (Anthropic AI assistant);
see the AI-use appendix of the report.
"""
import math
import random

# ======================================================================= the field
WORLD_LEFT, WORLD_RIGHT = -10.0, 10.0
WORLD_BOTTOM, WORLD_TOP = -7.5, 7.5

# ======================================================================= ball and paddle
BALL_RADIUS = 0.3
PADDLE_Y = -6.5               # centre of the paddle
PADDLE_HALF_WIDTH = 1.5       # at paddle_width = 1
PADDLE_HALF_HEIGHT = 0.2      # the paddle figure is 0.4 tall
PADDLE_SPEED = 12.0           # world units per second (player and attract mode)
MAX_BOUNCE_DEG = 60.0         # the paddle's edge sends the ball out 60 deg from vertical
MIN_VERTICAL = 0.3            # |vy| never drops below 30 % of the speed (no endless sideways ball)
MAX_BALL_SPEED = 20.0
SERVE_ANGLE_DEG = 25.0        # a serve leaves up to 25 deg left or right of vertical

# ======================================================================= bricks
BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_W, BRICK_H = 1.8, 0.6
BRICK_GAP_X, BRICK_GAP_Y = 0.2, 0.25
BRICK_TOP_Y = 5.0             # centre of the top row
BRICK_POINTS = 10
BREAK_TIME = 0.45             # seconds a broken brick shrinks, spins and falls
BUILD_TIME = 0.35             # seconds one brick needs to pop in at a new level
BUILD_STAGGER = 0.02          # brick n starts popping in n x 0.02 s after the first

# ======================================================================= UFO (curved path)
UFO_POINTS = 50
UFO_RANGE_X = 12.0            # x(t) = 12 sin(w t): turns round just off the screen
UFO_PERIOD = 16.0             # seconds to fly across and back
UFO_CENTRE_Y = 6.45           # y(x) = 6.45 + 0.4 sin(k x): a wave across the sky
UFO_WAVE_Y = 0.4
UFO_WAVELENGTH = 8.0          # k = 2 pi / 8
UFO_HALF_W, UFO_HALF_H = 1.0, 0.4    # the saucer body (an ellipse 2.0 x 0.8)
UFO_VISIBLE_X = 9.0           # it only drops capsules while it is over the field
UFO_HIT_COOLDOWN = 0.4        # seconds before the UFO can be hit again

# ======================================================================= power-up capsule
CAPSULE_HALF_W, CAPSULE_HALF_H = 0.45, 0.2
CAPSULE_FALL_SPEED = 3.0      # world units per second
CAPSULE_SPIN_SPEED = 180.0    # degrees per second
CAPSULE_INTERVAL = 18.0       # the UFO drops one by itself this often (seconds of play)
CAPSULE_POINTS = 25
POWERUP_KINDS = ("wide", "slow", "life")
POWERUP_WEIGHTS = (0.45, 0.35, 0.20)
WIDE_FACTOR, WIDE_TIME = 1.6, 10.0     # paddle 1.6 x wider for 10 s
SLOW_FACTOR, SLOW_TIME = 0.65, 8.0     # ball at 65 % speed for 8 s

# ======================================================================= rules and timing
START_LIVES, MAX_LIVES = 3, 5
SERVE_DELAY = 1.2             # ball waits on the paddle before it is served
LEVEL_SERVE_DELAY = 2.2       # longer at a new level, while the bricks pop in
LEVEL_SPEEDUP = 0.10          # each level makes the ball 10 % faster
GAME_OVER_RESTART = 3.0       # attract mode starts a new game after 3 s
JOYSTICK_MAX_TILT = 25.0      # degrees
HEART_POP_TIME = 0.6          # seconds the lost heart grows and fades

SERVE, PLAY, GAME_OVER = "serve", "play", "game_over"


# ======================================================================= helper functions
# Plain functions (no Game object needed), so the unit tests can check the maths.

def clamp(value, low, high):
    """Keep value inside [low, high]."""
    return max(low, min(high, value))


def brick_center(row, col):
    """World position of brick (row, col). Row 0 is the top row."""
    x = WORLD_LEFT + 1.0 + col * (BRICK_W + BRICK_GAP_X)
    y = BRICK_TOP_Y - row * (BRICK_H + BRICK_GAP_Y)
    return x, y


def circle_rect_contact(cx, cy, r, rx, ry, half_w, half_h):
    """Does a circle (centre cx, cy, radius r) touch an axis-aligned rectangle
    (centre rx, ry, half sizes half_w, half_h)?

    Returns None, or (nx, ny, depth): the unit normal pointing from the
    rectangle towards the circle, and how far they overlap.

    Method: clamp the circle centre into the rectangle to get the CLOSEST point
    of the rectangle. If that point is nearer than r, they touch, and the line
    from the closest point to the centre is the normal. A hit on a flat side
    gives (0, 1), (1, 0), ...; a hit on a corner gives a diagonal normal, so the
    ball bounces off corners in a natural direction.
    """
    dx, dy = cx - rx, cy - ry
    ox = dx - clamp(dx, -half_w, half_w)       # centre minus closest point
    oy = dy - clamp(dy, -half_h, half_h)
    dist2 = ox * ox + oy * oy
    if dist2 > r * r:
        return None
    if dist2 > 1e-12:
        dist = math.sqrt(dist2)
        return ox / dist, oy / dist, r - dist
    # The centre is inside the rectangle: push out through the nearest side.
    push_x, push_y = half_w - abs(dx) + r, half_h - abs(dy) + r
    if push_x < push_y:
        return (1.0 if dx >= 0 else -1.0), 0.0, push_x
    return 0.0, (1.0 if dy >= 0 else -1.0), push_y


def rects_overlap(ax, ay, a_half_w, a_half_h, bx, by, b_half_w, b_half_h):
    """True when two axis-aligned rectangles overlap (capsule vs paddle)."""
    return abs(ax - bx) <= a_half_w + b_half_w and abs(ay - by) <= a_half_h + b_half_h


def fold_between(x, low, high):
    """Where a point moving freely to x really is when it bounces between two
    walls at low and high (used by attract mode to predict the ball).
    Like folding a long strip of paper back and forth between the walls."""
    width = high - low
    if width <= 0:
        return low
    u = (x - low) % (2.0 * width)
    return low + (u if u <= width else 2.0 * width - u)


def ufo_path(t):
    """The UFO's curved path at time t: it flies across the sky on a wave,
    turns round just off the screen and flies back.

        x(t) = A sin(w t)              vx = A w cos(w t)              w = 2 pi / period
        y(x) = y0 + B sin(k x)         vy = dy/dt = B k cos(k x) . vx k = 2 pi / wavelength

    Because y depends on x, the slope of the path dy/dx = B k cos(k x) is never
    more than B k = 0.31, so the saucer tilts at most about 17 degrees.
    Returns (x, y, vx, vy). The velocity is the exact derivative, so the
    heading does not depend on the frame rate."""
    w = 2.0 * math.pi / UFO_PERIOD
    k = 2.0 * math.pi / UFO_WAVELENGTH
    x = UFO_RANGE_X * math.sin(w * t)
    vx = UFO_RANGE_X * w * math.cos(w * t)
    y = UFO_CENTRE_Y + UFO_WAVE_Y * math.sin(k * x)
    vy = UFO_WAVE_Y * k * math.cos(k * x) * vx
    return x, y, vx, vy


def heading_degrees(vx, vy):
    """Direction of motion in degrees: atan2(vy, vx). 0 = moving right, 90 = up."""
    return math.degrees(math.atan2(vy, vx))


def upright_tilt(heading):
    """Turn a heading into a tilt that keeps the saucer the right way up.
    The saucer is symmetric left-right, so moving left (heading near 180)
    only needs a small tilt, not a half turn that would put the dome underneath.
    The body's long axis still lies exactly along the direction of motion."""
    if heading > 90.0:
        return heading - 180.0
    if heading < -90.0:
        return heading + 180.0
    return heading


def ease_out_back(p):
    """0 -> 1 with a small overshoot at the end (the brick 'pops' into place)."""
    p = clamp(p, 0.0, 1.0) - 1.0
    k = 1.70158
    return 1.0 + p * p * ((k + 1.0) * p + k)


# ======================================================================= the game

class Game:
    """The whole game state. update(dt) moves it forward by dt seconds."""

    def __init__(self, seed=2026):
        self.seed = seed              # same seed -> same serves and capsules (tests, demos)
        # Values the GUI's "Game tuning" sliders change.
        self.ball_speed = 6.0         # world units per second, before level / slow bonus
        self.ufo_orbit_speed = 120.0  # degrees per second, the light ring around the UFO
        self._paddle_base = 1.0       # the slider's paddle width
        self.paddle_boost = 1.0       # the wide power-up animates this from 1 to 1.6
        self.high_score = 0
        self.attract = False
        self.events = []
        self.reset()

    # ------------------------------------------------------------------ paddle width
    # The slider writes paddle_width. The wide power-up must not overwrite the
    # slider, so the real width is   slider value x boost.

    @property
    def paddle_width(self):
        """Paddle width factor as drawn and used for collisions (slider x power-up)."""
        return self._paddle_base * self.paddle_boost

    @paddle_width.setter
    def paddle_width(self, value):
        value = float(value)
        if not value > 0.0:               # also refuses NaN
            raise ValueError("the paddle width must be positive")
        self._paddle_base = value

    @property
    def paddle_base(self):
        """The slider's value, without the power-up (saved in settings.json)."""
        return self._paddle_base

    def paddle_half_width(self):
        return PADDLE_HALF_WIDTH * self.paddle_width

    # ------------------------------------------------------------------ new game

    def reset(self):
        """R key / Reset button: a completely new game (attract mode off)."""
        self.attract = False
        self._new_game()

    def _new_game(self):
        self.rng = random.Random(self.seed)
        self.time = 0.0
        self.state = SERVE
        self.state_time = 0.0
        self.score, self.lives, self.level = 0, START_LIVES, 1
        # paddle and joystick
        self.paddle_x = 0.0
        self.paddle_input = 0             # -1 left, 0 still, +1 right (set by gui.py)
        self.paddle_velocity = 0.0
        self.paddle_boost = 1.0
        self.paddle_dip = 0.0             # 1 just after the ball hits it, then fades
        self.joystick_tilt = 0.0          # degrees, follows the paddle's movement
        # power-ups
        self.wide_time = 0.0
        self.slow_time = 0.0
        self.capsule_active = False
        self.capsule_x = self.capsule_y = 0.0
        self.capsule_kind = POWERUP_KINDS[0]
        self.capsule_spin = 0.0
        self.capsule_timer = CAPSULE_INTERVAL
        # ball
        self.ball_vx, self.ball_vy = 0.0, 0.0
        self.ball_spin = 0.0              # degrees, the ball rolls along its path
        self.ball_visible = True
        self.serve_timer = SERVE_DELAY
        self._place_ball_on_paddle()
        # bricks
        self._rebuild_timer = None        # counts down to the next level's bricks
        self._build_bricks(animated=True)
        # UFO
        self.ufo_light_angle = 0.0
        self.ufo_wobble = 0.0             # 1 just after a hit, then fades
        self._ufo_cooldown = 0.0
        self._move_ufo(0.0)
        # score and lives animations
        self.score_pulse = 0.0            # 1 when points are scored, then fades
        self.heart_pop_index = None       # which heart is popping (the one just lost)
        self.heart_pop_time = 0.0
        self.events = []
        self._event("New game - break all the bricks!")

    def _build_bricks(self, animated):
        """A full wall of bricks. With animated=True they pop in one after another."""
        self.bricks = []
        for row in range(BRICK_ROWS):
            line = []
            for col in range(BRICK_COLS):
                line.append({"alive": True, "visible": True,
                             "scale": 0.0 if animated else 1.0, "alpha": 1.0,
                             "angle": 0.0, "drop": 0.0,
                             "phase": "build" if animated else "idle", "t": 0.0,
                             "delay": BUILD_STAGGER * (row * BRICK_COLS + col),
                             "spin": 1.0 if (row + col) % 2 == 0 else -1.0})
            self.bricks.append(line)
        self.bricks_left = BRICK_ROWS * BRICK_COLS

    # ------------------------------------------------------------------ input

    def toggle_attract(self):
        """M key: attract (demo) mode, the paddle plays by itself."""
        self.attract = not self.attract
        self._event("Attract mode on - the paddle plays by itself"
                    if self.attract else "Attract mode off - your turn")

    def launch(self):
        """Up key: serve now instead of waiting."""
        if self.state == SERVE and self._rebuild_timer is None:
            self._launch()

    def pop_events(self):
        """Messages for the status bar since the last call (main.py shows them)."""
        events, self.events = self.events, []
        return events

    def _event(self, text):
        self.events.append(text)

    @property
    def banner(self):
        """Big text a renderer may draw in the middle of the field."""
        if self.state == GAME_OVER:
            return "GAME OVER"
        if self.state == SERVE:
            return "LEVEL %d" % self.level if self.level > 1 else "GET READY"
        return ""

    def current_ball_speed(self):
        """Slider speed x level bonus x slow power-up."""
        speed = self.ball_speed * (1.0 + LEVEL_SPEEDUP * (self.level - 1))
        if self.slow_time > 0.0:
            speed *= SLOW_FACTOR
        return clamp(speed, 0.5, MAX_BALL_SPEED)

    # ------------------------------------------------------------------ one frame

    def update(self, dt):
        """Advance the game by dt seconds (dt already includes the speed slider)."""
        if not dt > 0.0:                  # 0, negative or NaN: nothing happens
            return
        dt = min(dt, 0.5)                 # a frozen window must not teleport the ball
        self.time += dt
        self.state_time += dt
        self._update_power_ups(dt)
        self._move_paddle(dt)
        self._move_joystick(dt)
        self._move_ufo(dt)
        if self.state == SERVE:
            self._update_serve(dt)
        elif self.state == PLAY:
            self._move_ball(dt)
        else:
            self._update_game_over()
        self._move_capsule(dt)
        self._animate_bricks(dt)
        self._animate_hud(dt)

    # ------------------------------------------------------------------ paddle + joystick

    def _move_paddle(self, dt):
        direction = self._attract_direction(dt) if self.attract else self.paddle_input
        direction = clamp(float(direction), -1.0, 1.0)
        old_x = self.paddle_x
        half = self.paddle_half_width()
        self.paddle_x = clamp(self.paddle_x + direction * PADDLE_SPEED * dt,
                              WORLD_LEFT + half, WORLD_RIGHT - half)
        self.paddle_velocity = (self.paddle_x - old_x) / dt

    def _move_joystick(self, dt):
        """The cabinet's joystick leans the way the paddle moves (right = clockwise,
        a negative angle). It eases towards the target instead of jumping."""
        target = -JOYSTICK_MAX_TILT * clamp(self.paddle_velocity / PADDLE_SPEED, -1.0, 1.0)
        self.joystick_tilt += (target - self.joystick_tilt) * min(1.0, 15.0 * dt)

    # ------------------------------------------------------------------ UFO

    def _move_ufo(self, dt):
        """Follow the curved path and face the direction of motion."""
        self.ufo_x, self.ufo_y, self.ufo_vx, self.ufo_vy = ufo_path(self.time)
        self.ufo_heading = heading_degrees(self.ufo_vx, self.ufo_vy)
        self.ufo_wobble *= math.exp(-3.0 * dt)
        shake = 20.0 * self.ufo_wobble * math.sin(25.0 * self.time)
        self.ufo_angle = upright_tilt(self.ufo_heading) + shake
        self.ufo_light_angle = (self.ufo_light_angle + self.ufo_orbit_speed * dt) % 360.0
        self._ufo_cooldown = max(0.0, self._ufo_cooldown - dt)

    # ------------------------------------------------------------------ serve / game over

    def _place_ball_on_paddle(self):
        self.ball_x = self.paddle_x
        self.ball_y = PADDLE_Y + PADDLE_HALF_HEIGHT + BALL_RADIUS + 0.01

    def _update_serve(self, dt):
        if self._rebuild_timer is not None:          # next level: bricks come back first
            self._rebuild_timer -= dt
            if self._rebuild_timer <= 0.0:
                self._rebuild_timer = None
                self._build_bricks(animated=True)
        self._place_ball_on_paddle()
        self.serve_timer -= dt
        if self.serve_timer <= 0.0 and self._rebuild_timer is None:
            self._launch()

    def _launch(self):
        angle = math.radians(self.rng.uniform(-SERVE_ANGLE_DEG, SERVE_ANGLE_DEG))
        speed = self.current_ball_speed()
        self.ball_vx, self.ball_vy = speed * math.sin(angle), speed * math.cos(angle)
        self._set_state(PLAY)

    def _update_game_over(self):
        if self.attract and self.state_time >= GAME_OVER_RESTART:
            self._new_game()                          # keeps attract mode on
            self._event("Attract mode: new game")

    def _set_state(self, state):
        self.state = state
        self.state_time = 0.0

    # ------------------------------------------------------------------ ball

    def _move_ball(self, dt):
        """Move the ball in small sub-steps so it can never jump through a brick.

        At 15 units/s and 3x speed one frame can be 4.5 units long, more than a
        brick is high. So the frame is cut into steps of at most half a ball
        radius, and collisions are checked after every step."""
        speed = self.current_ball_speed()
        length = math.hypot(self.ball_vx, self.ball_vy)
        if length < 1e-9:
            self.ball_vx, self.ball_vy, length = 0.0, speed, speed
        self.ball_vx *= speed / length            # keep the direction, use the
        self.ball_vy *= speed / length            # speed of the slider and power-ups
        steps = max(1, int(math.ceil(speed * dt / (0.5 * BALL_RADIUS))))
        h = dt / steps
        for _ in range(steps):
            self.ball_x += self.ball_vx * h
            self.ball_y += self.ball_vy * h
            self._collide_walls()
            self._collide_paddle()
            self._collide_ufo()
            self._collide_bricks()
            if self.state != PLAY:                # the last brick was broken
                return
            if self.ball_y < WORLD_BOTTOM - BALL_RADIUS:
                self._lose_ball()
                return
        # Rolling: distance / radius gives the turn in radians (clockwise when moving right).
        self.ball_spin = (self.ball_spin - math.degrees(self.ball_vx * dt / BALL_RADIUS)) % 360.0

    def _bounce(self, nx, ny, depth):
        """Push the ball out of what it hit and reflect its velocity:
            v' = v - 2 (v . n) n
        Only when it is moving INTO the surface (v . n < 0), so a ball that is
        already leaving is not turned back. Returns True if it bounced."""
        self.ball_x += nx * depth
        self.ball_y += ny * depth
        dot = self.ball_vx * nx + self.ball_vy * ny
        if dot >= 0.0:
            return False
        self.ball_vx -= 2.0 * dot * nx
        self.ball_vy -= 2.0 * dot * ny
        self._keep_steep()
        return True

    def _keep_steep(self):
        """After a corner hit the ball could fly almost flat and bounce from wall
        to wall for ever. Keep |vy| at least MIN_VERTICAL x speed."""
        speed = math.hypot(self.ball_vx, self.ball_vy)
        if abs(self.ball_vy) < MIN_VERTICAL * speed:
            sign_y = 1.0 if self.ball_vy > 0.0 else -1.0
            sign_x = 1.0 if self.ball_vx >= 0.0 else -1.0
            self.ball_vy = sign_y * MIN_VERTICAL * speed
            self.ball_vx = sign_x * math.sqrt(speed * speed - self.ball_vy ** 2)

    def _collide_walls(self):
        right, left = WORLD_RIGHT - BALL_RADIUS, WORLD_LEFT + BALL_RADIUS
        top = WORLD_TOP - BALL_RADIUS
        if self.ball_x > right:
            self._bounce(-1.0, 0.0, self.ball_x - right)
        elif self.ball_x < left:
            self._bounce(1.0, 0.0, left - self.ball_x)
        if self.ball_y > top:
            self._bounce(0.0, -1.0, self.ball_y - top)

    def _collide_paddle(self):
        """Top of the paddle: the bounce angle depends on WHERE the ball lands.
        Centre -> straight up, edges -> 60 deg to that side. This is what lets
        the player aim. The sides of the paddle bounce like a wall."""
        if self.ball_vy > 0.0:                    # already going up
            return
        half = self.paddle_half_width()
        contact = circle_rect_contact(self.ball_x, self.ball_y, BALL_RADIUS,
                                      self.paddle_x, PADDLE_Y, half, PADDLE_HALF_HEIGHT)
        if contact is None:
            return
        nx, ny, depth = contact
        if ny > 0.5:                              # top face (or the top of a corner)
            offset = clamp((self.ball_x - self.paddle_x) / half, -1.0, 1.0)
            angle = math.radians(offset * MAX_BOUNCE_DEG)
            speed = math.hypot(self.ball_vx, self.ball_vy)
            self.ball_vx, self.ball_vy = speed * math.sin(angle), speed * math.cos(angle)
            self.ball_y = PADDLE_Y + PADDLE_HALF_HEIGHT + BALL_RADIUS
            self.paddle_dip = 1.0
        else:
            self._bounce(nx, ny, depth)

    def _collide_ufo(self):
        """The UFO is a moving target: bounce off it for 50 points, and it drops
        a power-up capsule. The saucer is treated as its 2.0 x 0.8 box."""
        if self._ufo_cooldown > 0.0:
            return
        contact = circle_rect_contact(self.ball_x, self.ball_y, BALL_RADIUS,
                                      self.ufo_x, self.ufo_y, UFO_HALF_W, UFO_HALF_H)
        if contact is None:
            return
        self._bounce(*contact)
        self._ufo_cooldown = UFO_HIT_COOLDOWN
        self.ufo_wobble = 1.0
        self._add_score(UFO_POINTS)
        self._event("UFO hit! +%d" % UFO_POINTS)
        self._drop_capsule()

    def _collide_bricks(self):
        """Only the bricks around the ball are tested (its row and column +- 1),
        found directly from the brick grid. If it touches several, the deepest
        overlap is the real hit; one brick breaks per step."""
        pitch_x, pitch_y = BRICK_W + BRICK_GAP_X, BRICK_H + BRICK_GAP_Y
        col0 = int(round((self.ball_x - (WORLD_LEFT + 1.0)) / pitch_x))
        row0 = int(round((BRICK_TOP_Y - self.ball_y) / pitch_y))
        best = None
        for row in range(max(0, row0 - 1), min(BRICK_ROWS, row0 + 2)):
            for col in range(max(0, col0 - 1), min(BRICK_COLS, col0 + 2)):
                if not self.bricks[row][col]["alive"]:
                    continue
                bx, by = brick_center(row, col)
                contact = circle_rect_contact(self.ball_x, self.ball_y, BALL_RADIUS,
                                              bx, by, BRICK_W / 2.0, BRICK_H / 2.0)
                if contact is not None and (best is None or contact[2] > best[0][2]):
                    best = (contact, row, col)
        if best is None:
            return
        contact, row, col = best
        if self._bounce(*contact):
            self._break_brick(row, col)

    def _break_brick(self, row, col):
        brick = self.bricks[row][col]
        brick["alive"] = False
        brick["phase"], brick["t"] = "break", 0.0
        self.bricks_left -= 1
        self._add_score(BRICK_POINTS)
        if self.bricks_left == 0:
            self._next_level()

    def _lose_ball(self):
        self.lives -= 1
        self.heart_pop_index, self.heart_pop_time = self.lives, 0.0
        self.capsule_active = False               # power-ups end with the ball
        self.wide_time = self.slow_time = 0.0
        if self.lives <= 0:
            self.lives = 0
            self.ball_visible = False
            self._set_state(GAME_OVER)
            self._event("Game over - score %d. Press R for a new game" % self.score)
        else:
            self._set_state(SERVE)
            self.serve_timer = SERVE_DELAY
            self._place_ball_on_paddle()
            self._event("Ball lost - %d %s left" % (self.lives,
                                                    "life" if self.lives == 1 else "lives"))

    def _next_level(self):
        """All bricks broken: faster ball, new wall. The new bricks appear when
        the last one has finished its break animation."""
        self.level += 1
        self.capsule_active = False
        self._set_state(SERVE)
        self.serve_timer = LEVEL_SERVE_DELAY
        self._rebuild_timer = BREAK_TIME + 0.15
        self._place_ball_on_paddle()
        self._event("Level %d! The ball is %d%% faster"
                    % (self.level, round(100 * LEVEL_SPEEDUP * (self.level - 1))))

    def _add_score(self, points):
        self.score += points
        self.score_pulse = 1.0
        if not self.attract and self.score > self.high_score:
            self.high_score = self.score

    # ------------------------------------------------------------------ capsule + power-ups

    def _drop_capsule(self):
        """The UFO drops a capsule from where it is. Returns False when it cannot
        (one is already falling, the ball is not in play, or the UFO is off screen)."""
        if self.capsule_active or self.state != PLAY or abs(self.ufo_x) > UFO_VISIBLE_X:
            return False
        self.capsule_kind = self.rng.choices(POWERUP_KINDS, POWERUP_WEIGHTS)[0]
        self.capsule_active = True
        self.capsule_x = self.ufo_x
        self.capsule_y = self.ufo_y - 0.6
        self.capsule_spin = 0.0
        return True

    def _move_capsule(self, dt):
        if self.state == PLAY:
            self.capsule_timer -= dt
            # When the time is up the UFO drops one as soon as it is over the field.
            if self.capsule_timer <= 0.0 and self._drop_capsule():
                self.capsule_timer = CAPSULE_INTERVAL
        if not self.capsule_active:
            return
        self.capsule_y -= CAPSULE_FALL_SPEED * dt
        self.capsule_spin = (self.capsule_spin + CAPSULE_SPIN_SPEED * dt) % 360.0
        if rects_overlap(self.capsule_x, self.capsule_y, CAPSULE_HALF_W, CAPSULE_HALF_H,
                         self.paddle_x, PADDLE_Y, self.paddle_half_width(), PADDLE_HALF_HEIGHT):
            self._catch_capsule()
        elif self.capsule_y < WORLD_BOTTOM - 1.0:
            self.capsule_active = False

    def _catch_capsule(self):
        self.capsule_active = False
        self._add_score(CAPSULE_POINTS)
        if self.capsule_kind == "wide":
            self.wide_time = WIDE_TIME
            self._event("Power-up: wide paddle for %d s" % WIDE_TIME)
        elif self.capsule_kind == "slow":
            self.slow_time = SLOW_TIME
            self._event("Power-up: slow ball for %d s" % SLOW_TIME)
        else:
            self.lives = min(MAX_LIVES, self.lives + 1)
            self._event("Power-up: extra life (%d lives)" % self.lives)

    def _update_power_ups(self, dt):
        """Count the power-ups down. The paddle does not jump to its new width:
        paddle_boost eases towards 1.6 (or back to 1), so it visibly grows
        and shrinks - a scaling animation."""
        self.wide_time = max(0.0, self.wide_time - dt)
        self.slow_time = max(0.0, self.slow_time - dt)
        target = WIDE_FACTOR if self.wide_time > 0.0 else 1.0
        self.paddle_boost += (target - self.paddle_boost) * min(1.0, 6.0 * dt)

    # ------------------------------------------------------------------ animations

    def _animate_bricks(self, dt):
        """Break: shrink, spin and fall for 0.45 s, then disappear.
        Build (new level): pop in one after another with a small overshoot."""
        for line in self.bricks:
            for brick in line:
                phase = brick["phase"]
                if phase == "idle" or phase == "gone":
                    continue
                brick["t"] += dt
                if phase == "break":
                    p = brick["t"] / BREAK_TIME
                    if p >= 1.0:
                        brick.update(phase="gone", visible=False, scale=0.0, alpha=0.0)
                        continue
                    brick["scale"] = 1.0 - p
                    brick["alpha"] = 1.0 - p
                    brick["angle"] = 180.0 * p * brick["spin"]
                    brick["drop"] = 1.5 * p * p       # falls faster and faster
                else:                                  # "build"
                    p = (brick["t"] - brick["delay"]) / BUILD_TIME
                    brick["scale"] = ease_out_back(p) if p > 0.0 else 0.0
                    if p >= 1.0:
                        brick.update(phase="idle", scale=1.0)

    def _animate_hud(self, dt):
        """Score pulse, popping heart and paddle dip all fade out smoothly."""
        self.score_pulse *= math.exp(-5.0 * dt)
        self.paddle_dip *= math.exp(-8.0 * dt)
        if self.heart_pop_index is not None:
            self.heart_pop_time += dt
            if self.heart_pop_time >= HEART_POP_TIME:
                self.heart_pop_index = None

    # ------------------------------------------------------------------ attract mode (AI)

    def _attract_direction(self, dt):
        """Move the paddle towards the attract target at the normal paddle speed
        (no cheating), without overshooting it."""
        diff = self._attract_target() - self.paddle_x
        if abs(diff) < 0.02:
            return 0.0
        return clamp(diff / (PADDLE_SPEED * dt), -1.0, 1.0)

    def _attract_target(self):
        """Where the paddle should be.

        Ball coming down: predict where it reaches the paddle (straight line,
        folded between the side walls), then stand so the ball lands on the part
        of the paddle that sends it towards the column with the most bricks.
        Ball going up: catch a falling capsule, or wait under the ball."""
        half = self.paddle_half_width()
        if self.state != PLAY:
            return self.capsule_x if self.capsule_active else 0.0
        hit_y = PADDLE_Y + PADDLE_HALF_HEIGHT + BALL_RADIUS
        if self.ball_vy < 0.0:
            t = (self.ball_y - hit_y) / -self.ball_vy
            x = fold_between(self.ball_x + self.ball_vx * t,
                             WORLD_LEFT + BALL_RADIUS, WORLD_RIGHT - BALL_RADIUS)
            return x - self._attract_aim(x, hit_y) * half
        if self.capsule_active:
            return self.capsule_x
        return self.ball_x

    def _attract_aim(self, x, hit_y):
        """Paddle offset (-1 .. 1) that sends the ball from (x, hit_y) towards the
        lowest brick of the column with the most bricks left."""
        best_col, best_count = None, 0
        for col in range(BRICK_COLS):
            count = sum(1 for row in range(BRICK_ROWS) if self.bricks[row][col]["alive"])
            if count > best_count:
                best_col, best_count = col, count
        if best_col is None:
            return 0.0
        low_row = max(row for row in range(BRICK_ROWS) if self.bricks[row][best_col]["alive"])
        tx, ty = brick_center(low_row, best_col)
        angle = math.degrees(math.atan2(tx - x, ty - hit_y))   # from vertical
        return clamp(angle / MAX_BOUNCE_DEG, -0.85, 0.85)
