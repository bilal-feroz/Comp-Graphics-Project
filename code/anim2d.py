"""
anim2d.py - the 2D animation: game numbers -> scene-graph nodes.          [Member 3]

game.py decides WHAT happens (plain numbers, no OpenGL). This file decides how
it MOVES on screen: every frame, sync() copies those numbers into the local
transform (T . R . S) of the 2D nodes. render2d.py (Member 2) decides what the
nodes LOOK like and draws them. No OpenGL calls here either.

Animated objects (T = translation, R = rotation, S = scaling):

    ball               T  path of the ball         R  rolls along its path
    paddle             T  player / attract mode    S  width (slider x wide power-up,
                                                      grows and shrinks smoothly), dips on a hit
    brick_r_c          T  falls when broken        R  spins          S  shrinks / pops in
    ufo                T  wave across the sky      R  faces its direction of motion
       ufo_light_ring  R  orbits the lights        (hierarchy: the lights ride on the UFO)
       ufo_light_i     S  blink one after another
    capsule            T  falls from the UFO       R  spins          S  pulses
    joystick_pivot     R  leans with the paddle    (hierarchy: stick and knob follow)
    heart_i            S  heartbeat, pops when a life is lost
    score              S  pulses when points are scored (if Member 2's scene has it)

Hierarchical motion (world = parent world . local):

    world(knob)    = T(base) . T(pivot) . R(tilt) . T(0, 0.2) . T(0, 0.2)
    world(light_i) = T(ufo) . R(ufo tilt) . S(ufo size) . R(ring angle) . T(r cos 90i, r sin 90i) . S(blink)

NODE NAMES are the contract with render2d.py: sync() looks nodes up by name and
skips any it cannot find. ensure_nodes() adds simple default figures for the
nodes this file animates that the scene does not have yet (joystick, capsule,
hearts); Member 2 can build nicer ones with the same names and they will be
used instead.

GUI edits are kept: a brick's size, rotation or visibility is only written
while the brick is animating, so the Size / Rotation sliders still work on
idle bricks.

Written by Member 3 with help from Claude (Anthropic AI assistant);
see the AI-use appendix of the report.
"""
import math
import weakref

import figures
import game as rules
from scene import Node

CAPSULE_COLOURS = {"wide": (0.25, 0.65, 1.0),     # blue  = wide paddle
                   "slow": (0.30, 0.90, 0.45),    # green = slow ball
                   "life": (1.0, 0.35, 0.55)}     # pink  = extra life
HEART_COLOUR = (1.0, 0.30, 0.40)
UFO_LIGHT_COUNT = 4

# What sync() remembers between frames for each scene (to write a value only
# when it changes). Keyed by the root node; forgotten when the scene is rebuilt.
_memory = weakref.WeakKeyDictionary()


# ======================================================================= default figures
# Simple shapes in MODEL coordinates, centred on the origin, counter-clockwise.
# Member 2 may replace them with nicer ones in figures.py.

def heart(width):
    """Heart outline from the curve  x = 16 sin^3 t,
    y = 13 cos t - 5 cos 2t - 2 cos 3t - cos 4t, scaled to `width` and centred."""
    points = []
    for i in range(32):
        t = 2.0 * math.pi * i / 32
        x = 16.0 * math.sin(t) ** 3
        y = 13.0 * math.cos(t) - 5.0 * math.cos(2 * t) - 2.0 * math.cos(3 * t) - math.cos(4 * t)
        points.append((x, y))
    k = width / 32.0
    centre_y = 0.5 * (max(y for _, y in points) + min(y for _, y in points))
    # The curve runs clockwise, so reverse it to get counter-clockwise.
    return [(k * x, k * (y - centre_y)) for x, y in reversed(points)]


def capsule_shape(half_w, half_h, segments=8):
    """A pill: two half circles of radius half_h joined by straight sides."""
    r, cx = half_h, half_w - half_h
    points = []
    for i in range(segments + 1):                      # right end, bottom -> top
        a = -math.pi / 2 + math.pi * i / segments
        points.append((cx + r * math.cos(a), r * math.sin(a)))
    for i in range(segments + 1):                      # left end, top -> bottom
        a = math.pi / 2 + math.pi * i / segments
        points.append((-cx + r * math.cos(a), r * math.sin(a)))
    return points


# ======================================================================= scene set-up

def ensure_nodes(root):
    """Add default nodes for everything this file animates that the 2D scene
    does not have yet. Called at the end of render2d.build_scene()."""
    if root.find("joystick") is None:
        # base -> pivot (the joint, which turns) -> stick -> knob
        base = root.add(Node("joystick", figures.rect(1.1, 0.2), (0.35, 0.35, 0.45),
                             tx=-8.9, ty=-7.38))
        pivot = base.add(Node("joystick_pivot", ty=0.1))          # group node: the joint
        stick = pivot.add(Node("joystick_stick", figures.rect(0.12, 0.4),
                               (0.80, 0.80, 0.85), ty=0.2))       # centre of the stick
        stick.add(Node("joystick_knob", figures.regular_polygon(12, 0.15),
                       (0.95, 0.20, 0.20), ty=0.2))                # top of the stick
    if root.find("lives") is None:
        lives = root.add(Node("lives"))                            # group node
        for i in range(rules.MAX_LIVES):
            lives.add(Node("heart_%d" % i, heart(0.42), HEART_COLOUR,
                           tx=9.4 - 0.55 * i, ty=-7.12))
    if root.find("capsule") is None:
        root.add(Node("capsule", capsule_shape(rules.CAPSULE_HALF_W, rules.CAPSULE_HALF_H),
                      CAPSULE_COLOURS["wide"]))
    return root


def animated_fields(game):
    """{node name: {"size", "rotation"}} - the GUI-editable values that sync()
    is driving right now. persist.py does not save or load those (the animation
    owns them); everything else, like the UFO's size, is the user's."""
    both = {"size", "rotation"}
    fields = {"ball": {"rotation"}, "paddle": {"size"}, "ufo": {"rotation"},
              "ufo_light_ring": {"rotation"}, "capsule": both,
              "joystick_pivot": {"rotation"}, "score": {"size"}}
    fields.update(("ufo_light_%d" % i, {"size"}) for i in range(UFO_LIGHT_COUNT))
    fields.update(("heart_%d" % i, {"size"}) for i in range(rules.MAX_LIVES))
    for row in range(rules.BRICK_ROWS):
        for col in range(rules.BRICK_COLS):
            if game.bricks[row][col]["phase"] != "idle":
                fields["brick_%d_%d" % (row, col)] = both
    return fields


# ======================================================================= every frame

def sync(root, game, dt=0.0):
    """Copy the game state onto the 2D nodes. Called after game.update(dt)."""
    nodes = {node.name: node for node in root.all_nodes()}
    memory = _memory.setdefault(root, {})
    _sync_ball(nodes, game, memory)
    _sync_paddle(nodes, game)
    _sync_bricks(nodes, game, memory)
    _sync_ufo(nodes, game)
    _sync_capsule(nodes, game, memory)
    _sync_joystick(nodes, game)
    _sync_hearts(nodes, game)
    _sync_score(nodes, game)


def _changed(memory, key, value):
    """True the first time and whenever `value` differs from last frame."""
    if memory.get(key, object()) == value:
        return False
    memory[key] = value
    return True


def _sync_ball(nodes, game, memory):
    ball = nodes.get("ball")
    if ball is None:
        return
    ball.tx, ball.ty = game.ball_x, game.ball_y        # T: where the game put it
    ball.angle = game.ball_spin                        # R: rolls as it moves
    if _changed(memory, "ball_visible", game.ball_visible):
        ball.visible = game.ball_visible               # hidden at game over


def _sync_paddle(nodes, game):
    paddle = nodes.get("paddle")
    if paddle is None:
        return
    paddle.tx = game.paddle_x                          # T: player or attract mode
    paddle.ty = rules.PADDLE_Y - 0.12 * game.paddle_dip   # T: dips when the ball hits
    paddle.sx = game.paddle_width                      # S: slider x wide power-up


def _sync_bricks(nodes, game, memory):
    """A brick's transform is only written while it animates, and once more when
    it settles, so a size or rotation set in the GUI stays on idle bricks."""
    group = nodes.get("bricks")
    if group is None:
        return
    for node in group.children:
        try:
            row, col = (int(n) for n in node.name.split("_")[1:3])
            brick = game.bricks[row][col]
        except (ValueError, IndexError):
            continue                                   # not one of the game's bricks
        phase = brick["phase"]
        if _changed(memory, ("brick", row, col), phase):
            node.visible = brick["visible"]
            if phase == "idle":                        # settled: exact final values
                node.tx, node.ty = rules.brick_center(row, col)
                node.angle, node.sx, node.sy = 0.0, 1.0, 1.0
        if phase in ("build", "break"):
            x, y = rules.brick_center(row, col)
            node.tx, node.ty = x, y - brick["drop"]    # T: falls when broken
            node.angle = brick["angle"]                # R: spins when broken
            node.sx = node.sy = brick["scale"]         # S: shrinks / pops in


def _sync_ufo(nodes, game):
    ufo = nodes.get("ufo")
    if ufo is not None:
        ufo.tx, ufo.ty = game.ufo_x, game.ufo_y        # T: the curved path
        ufo.angle = game.ufo_angle                     # R: along the direction of motion
    ring = nodes.get("ufo_light_ring")
    if ring is not None:
        ring.angle = game.ufo_light_angle              # R: the lights orbit (hierarchy)
    for i in range(UFO_LIGHT_COUNT):
        light = nodes.get("ufo_light_%d" % i)
        if light is not None:                          # S: blink one after another
            wave = 0.5 + 0.5 * math.sin(6.0 * game.time - i * math.pi / 2.0)
            light.sx = light.sy = 0.8 + 0.6 * wave


def _sync_capsule(nodes, game, memory):
    capsule = nodes.get("capsule")
    if capsule is None:
        return
    capsule.visible = game.capsule_active
    if not game.capsule_active:
        return
    capsule.tx, capsule.ty = game.capsule_x, game.capsule_y   # T: falls
    capsule.angle = game.capsule_spin                         # R: spins
    capsule.sx = capsule.sy = 1.0 + 0.12 * math.sin(10.0 * game.time)   # S: pulses
    if _changed(memory, "capsule_kind", game.capsule_kind):   # colour shows the kind
        capsule.color = CAPSULE_COLOURS.get(game.capsule_kind, capsule.color)


def _sync_joystick(nodes, game):
    pivot = nodes.get("joystick_pivot")
    if pivot is not None:
        pivot.angle = game.joystick_tilt               # R: stick and knob follow (hierarchy)


def _sync_hearts(nodes, game):
    """Hearts beat (faster on the last life); the heart of a lost life grows to
    twice its size and then shrinks away."""
    rate = 2.4 if game.lives == 1 else 1.2             # beats per second
    beat = 1.0 + 0.1 * max(0.0, math.sin(2.0 * math.pi * rate * game.time))
    for i in range(rules.MAX_LIVES):
        heart_node = nodes.get("heart_%d" % i)
        if heart_node is None:
            continue
        if i == game.heart_pop_index:
            p = game.heart_pop_time / rules.HEART_POP_TIME
            scale = 1.0 + p / 0.4 if p < 0.4 else 2.0 * (1.0 - (p - 0.4) / 0.6)
            heart_node.visible = True
        else:
            scale = beat
            heart_node.visible = i < game.lives
        heart_node.sx = heart_node.sy = max(0.0, scale)


def _sync_score(nodes, game):
    score = nodes.get("score")
    if score is not None:
        score.sx = score.sy = 1.0 + 0.25 * game.score_pulse
