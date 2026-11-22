/* Arcade Breakout - browser port of the team's Python program (web showcase only:
 * a presentation extra; the graded program is the Python code in code/).
 *
 * Same rules (game.py, Member 3), same 2D figures and scene (figures.py and
 * render2d.py, Member 2), same 2D animation (anim2d.py, Member 3), same 3D models
 * and camera (figures.py and render3d.py, Member 4), same scene graph and our own
 * matrices (scene.py and matrices.py, Member 1).
 *
 * The canvas stands in for OpenGL: every node is still placed ONLY by its
 * world matrix = parent world . local, with local = T . R . S built from our
 * own 3x3 / 4x4 matrices. The 3D view does its own perspective projection,
 * back-face culling, flat lighting and depth sort (painter's algorithm).
 */
(function (root) {
  "use strict";
  const PI = Math.PI;
  const rad = (d) => (d * PI) / 180;
  const deg = (r) => (r * 180) / PI;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const mod = (a, b) => ((a % b) + b) % b;          // Python's % (never negative)

  // ===================================================================== matrices.py
  const identity3 = () => [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const translate2 = (tx, ty) => [[1, 0, tx], [0, 1, ty], [0, 0, 1]];
  const scale2 = (sx, sy) => [[sx, 0, 0], [0, sy, 0], [0, 0, 1]];
  function rotate2(t) { const c = Math.cos(t), s = Math.sin(t); return [[c, -s, 0], [s, c, 0], [0, 0, 1]]; }
  function mul(A, B) {                              // row of A . column of B
    const n = A.length, m = B[0].length, k = B.length, out = [];
    for (let i = 0; i < n; i++) {
      const row = [];
      for (let j = 0; j < m; j++) { let s = 0; for (let x = 0; x < k; x++) s += A[i][x] * B[x][j]; row.push(s); }
      out.push(row);
    }
    return out;
  }
  const compose = (...ms) => ms.reduce((acc, m) => mul(acc, m));
  const apply2 = (M, pts) => pts.map(([x, y]) => [M[0][0] * x + M[0][1] * y + M[0][2], M[1][0] * x + M[1][1] * y + M[1][2]]);
  const translate3 = (x, y, z) => [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]];
  const scale3 = (x, y, z) => [[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z, 0], [0, 0, 0, 1]];
  function rotX(t) { const c = Math.cos(t), s = Math.sin(t); return [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]; }
  function rotY(t) { const c = Math.cos(t), s = Math.sin(t); return [[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]]; }
  function rotZ(t) { const c = Math.cos(t), s = Math.sin(t); return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]; }
  const apply3 = (M, pts) => pts.map(([x, y, z]) => [
    M[0][0] * x + M[0][1] * y + M[0][2] * z + M[0][3],
    M[1][0] * x + M[1][1] * y + M[1][2] * z + M[1][3],
    M[2][0] * x + M[2][1] * y + M[2][2] * z + M[2][3]]);

  // ===================================================================== scene.py
  const FIELDS = ["tx", "ty", "tz", "angle", "rx", "ry", "rz", "sx", "sy", "sz"];
  class Node {
    constructor(name, figure = null, color = [1, 1, 1], dim = 2, t = {}) {
      this.name = name; this.figure = figure; this.color = color.slice(); this.dim = dim;
      this.visible = true; this.parent = null; this.children = [];
      this.tx = this.ty = this.tz = 0; this.angle = 0; this.rx = this.ry = this.rz = 0;
      this.sx = this.sy = this.sz = 1;
      for (const k of Object.keys(t)) { if (!FIELDS.includes(k)) throw new Error("unknown field " + k); this[k] = t[k]; }
    }
    local() {                                       // T . R . S
      if (this.dim === 2) return compose(translate2(this.tx, this.ty), rotate2(rad(this.angle)), scale2(this.sx, this.sy));
      return compose(translate3(this.tx, this.ty, this.tz), rotZ(rad(this.rz)), rotY(rad(this.ry)),
                     rotX(rad(this.rx)), scale3(this.sx, this.sy, this.sz));
    }
    world() { return this.parent ? mul(this.parent.world(), this.local()) : this.local(); }
    add(child) { child.parent = this; this.children.push(child); return child; }
    allNodes() { const out = [this]; for (const c of this.children) out.push(...c.allNodes()); return out; }
    find(name) { return this.allNodes().find((n) => n.name === name) || null; }
  }
  /* Draw traversal: parent world handed down, world = parent_world . local. */
  function walk(node, parentWorld, visit) {
    if (!node.visible) return;
    const world = parentWorld ? mul(parentWorld, node.local()) : node.world();
    if (node.figure) visit(node, world);
    for (const c of node.children) walk(c, world, visit);
  }

  // ===================================================================== figures.py
  const rect = (w, h) => [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]];
  const regularPolygon = (n, r) => Array.from({ length: n }, (_, i) => [r * Math.cos((2 * PI * i) / n), r * Math.sin((2 * PI * i) / n)]);
  const circle = (r, steps = 32) => regularPolygon(steps, r);
  function roundedPaddle(w = 3, h = 0.4, steps = 10) {
    const r = h / 2, hw = Math.max(r, w / 2), inner = hw - r, pts = [];
    for (let i = 0; i <= steps; i++) { const a = -PI / 2 + (PI * i) / steps; pts.push([inner + r * Math.cos(a), r * Math.sin(a)]); }
    for (let i = 0; i <= steps; i++) { const a = PI / 2 + (PI * i) / steps; pts.push([-inner + r * Math.cos(a), r * Math.sin(a)]); }
    return pts;
  }
  const ufoBody = (w = 2, h = 0.8, steps = 24) => Array.from({ length: steps }, (_, i) => [(w / 2) * Math.cos((2 * PI * i) / steps), (h / 2) * Math.sin((2 * PI * i) / steps)]);
  function ufoDome(w = 1, h = 0.6, steps = 12) {
    const pts = [];
    for (let i = 0; i <= steps; i++) { const a = (PI * i) / steps; pts.push([(w / 2) * Math.cos(a), h * Math.sin(a)]); }
    pts.push([-w / 2, 0]);
    return pts;
  }
  function heart(size = 0.4, steps = 24) {
    const pts = [];
    for (let i = 0; i < steps; i++) {
      const t = (2 * PI * i) / steps;
      const x = 16 * Math.sin(t) ** 3;
      const y = 13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
      pts.push([(x / 16) * size, (y / 16) * size]);
    }
    return pts;
  }
  function joystickBase(w = 1.2, h = 0.5) { const hw = w / 2, top = hw * 0.7, hh = h / 2; return [[-hw, -hh], [hw, -hh], [top, hh], [-top, hh]]; }
  function capsuleShape(halfW, halfH, segments = 8) {           // anim2d.py (Member 3)
    const r = halfH, cx = halfW - halfH, pts = [];
    for (let i = 0; i <= segments; i++) { const a = -PI / 2 + (PI * i) / segments; pts.push([cx + r * Math.cos(a), r * Math.sin(a)]); }
    for (let i = 0; i <= segments; i++) { const a = PI / 2 + (PI * i) / segments; pts.push([-cx + r * Math.cos(a), r * Math.sin(a)]); }
    return pts;
  }
  function box(w, h, d) {
    const x = w / 2, y = h / 2, z = d / 2;
    return [[[-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z], [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]],
            [[4, 5, 6, 7], [1, 0, 3, 2], [1, 2, 6, 5], [0, 4, 7, 3], [3, 7, 6, 2], [0, 1, 5, 4]]];
  }
  function star() {
    return [[[0, 0.2, 0], [0, -0.2, 0], [-0.2, 0, 0], [0.2, 0, 0], [0, 0, 0.2], [0, 0, -0.2]],
            [[0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2], [1, 4, 2], [1, 3, 4], [1, 5, 3], [1, 2, 5]]];
  }
  function bevelledBrick(w, h, d) {
    const x = w / 2, y = h / 2, z = d / 2, c = Math.min(w, h) * 0.15;
    const v = [[-x + c, -y, -z], [x - c, -y, -z], [x, -y + c, -z], [x, y - c, -z], [x - c, y, -z], [-x + c, y, -z], [-x, y - c, -z], [-x, -y + c, -z],
               [-x + c, -y, z], [x - c, -y, z], [x, -y + c, z], [x, y - c, z], [x - c, y, z], [-x + c, y, z], [-x, y - c, z], [-x, -y + c, z]];
    const f = [[8, 9, 10, 11, 12, 13, 14, 15], [7, 6, 5, 4, 3, 2, 1, 0], [0, 1, 9, 8], [1, 2, 10, 9], [2, 3, 11, 10],
               [3, 4, 12, 11], [4, 5, 13, 12], [5, 6, 14, 13], [6, 7, 15, 14], [7, 0, 8, 15]];
    return [v, f];
  }
  function trophy() {
    const profile = [[0, -1], [0.5, -1], [0.5, -0.7], [0.8, -0.4], [0.9, 0.3], [0.7, 0.7], [0.4, 0.9], [0, 0.9]];
    const steps = 16, v = [], f = [], n = profile.length;
    for (let i = 0; i < steps; i++) { const a = (2 * PI * i) / steps; for (const [r, y] of profile) v.push([r * Math.cos(a), y, r * Math.sin(a)]); }
    for (let i = 0; i < steps; i++) {
      const ni = (i + 1) % steps;
      for (let j = 0; j < n - 1; j++) f.push([i * n + j, i * n + j + 1, ni * n + j + 1, ni * n + j]);
    }
    return [v, f];
  }

  // ===================================================================== game.py (Member 3)
  const G = {
    WORLD_LEFT: -10, WORLD_RIGHT: 10, WORLD_BOTTOM: -7.5, WORLD_TOP: 7.5,
    BALL_RADIUS: 0.3, PADDLE_Y: -6.5, PADDLE_HALF_WIDTH: 1.5, PADDLE_HALF_HEIGHT: 0.2, PADDLE_SPEED: 12,
    MAX_BOUNCE_DEG: 60, MIN_VERTICAL: 0.3, MAX_BALL_SPEED: 20, SERVE_ANGLE_DEG: 25,
    BRICK_ROWS: 5, BRICK_COLS: 10, BRICK_W: 1.8, BRICK_H: 0.6, BRICK_GAP_X: 0.2, BRICK_GAP_Y: 0.25,
    BRICK_TOP_Y: 5, BRICK_POINTS: 10, BREAK_TIME: 0.45, BUILD_TIME: 0.35, BUILD_STAGGER: 0.02,
    UFO_POINTS: 50, UFO_RANGE_X: 12, UFO_PERIOD: 16, UFO_CENTRE_Y: 6.45, UFO_WAVE_Y: 0.4, UFO_WAVELENGTH: 8,
    UFO_HALF_W: 1, UFO_HALF_H: 0.4, UFO_VISIBLE_X: 9, UFO_HIT_COOLDOWN: 0.4,
    CAPSULE_HALF_W: 0.45, CAPSULE_HALF_H: 0.2, CAPSULE_FALL_SPEED: 3, CAPSULE_SPIN_SPEED: 180,
    CAPSULE_INTERVAL: 18, CAPSULE_POINTS: 25, WIDE_FACTOR: 1.6, WIDE_TIME: 10, SLOW_FACTOR: 0.65, SLOW_TIME: 8,
    START_LIVES: 3, MAX_LIVES: 5, SERVE_DELAY: 1.2, LEVEL_SERVE_DELAY: 2.2, LEVEL_SPEEDUP: 0.1,
    GAME_OVER_RESTART: 3, JOYSTICK_MAX_TILT: 25, HEART_POP_TIME: 0.6,
  };
  const KINDS = ["wide", "slow", "life"], WEIGHTS = [0.45, 0.35, 0.2];
  const brickCenter = (row, col) => [G.WORLD_LEFT + 1 + col * (G.BRICK_W + G.BRICK_GAP_X), G.BRICK_TOP_Y - row * (G.BRICK_H + G.BRICK_GAP_Y)];
  function circleRectContact(cx, cy, r, rx, ry, hw, hh) {
    const dx = cx - rx, dy = cy - ry;
    const ox = dx - clamp(dx, -hw, hw), oy = dy - clamp(dy, -hh, hh);
    const d2 = ox * ox + oy * oy;
    if (d2 > r * r) return null;
    if (d2 > 1e-12) { const d = Math.sqrt(d2); return [ox / d, oy / d, r - d]; }
    const px = hw - Math.abs(dx) + r, py = hh - Math.abs(dy) + r;
    return px < py ? [dx >= 0 ? 1 : -1, 0, px] : [0, dy >= 0 ? 1 : -1, py];
  }
  const rectsOverlap = (ax, ay, aw, ah, bx, by, bw, bh) => Math.abs(ax - bx) <= aw + bw && Math.abs(ay - by) <= ah + bh;
  function foldBetween(x, lo, hi) { const w = hi - lo; if (w <= 0) return lo; const u = mod(x - lo, 2 * w); return lo + (u <= w ? u : 2 * w - u); }
  function ufoPath(t) {
    const w = (2 * PI) / G.UFO_PERIOD, k = (2 * PI) / G.UFO_WAVELENGTH;
    const x = G.UFO_RANGE_X * Math.sin(w * t), vx = G.UFO_RANGE_X * w * Math.cos(w * t);
    const y = G.UFO_CENTRE_Y + G.UFO_WAVE_Y * Math.sin(k * x), vy = G.UFO_WAVE_Y * k * Math.cos(k * x) * vx;
    return [x, y, vx, vy];
  }
  const uprightTilt = (h) => (h > 90 ? h - 180 : h < -90 ? h + 180 : h);
  function easeOutBack(p) { p = clamp(p, 0, 1) - 1; const k = 1.70158; return 1 + p * p * ((k + 1) * p + k); }

  class Game {
    constructor(seed = 2026) {
      this.seed = seed; this.ballSpeed = 6; this.ufoOrbitSpeed = 120; this.paddleBase = 1; this.paddleBoost = 1;
      this.highScore = 0; this.attract = false; this.events = [];
      this.reset();
    }
    get paddleWidth() { return this.paddleBase * this.paddleBoost; }
    paddleHalfWidth() { return G.PADDLE_HALF_WIDTH * this.paddleWidth; }
    rand() {                                         // seeded (mulberry32), state kept as a number
      let t = (this.rngState = (this.rngState + 0x6d2b79f5) | 0);
      t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }
    reset() { this.attract = false; this.newGame(); }
    newGame() {
      this.rngState = this.seed | 0; this.time = 0; this.state = "serve"; this.stateTime = 0;
      this.score = 0; this.lives = G.START_LIVES; this.level = 1;
      this.paddleX = 0; this.paddleInput = 0; this.paddleVelocity = 0; this.paddleBoost = 1; this.paddleDip = 0; this.joystickTilt = 0;
      this.wideTime = 0; this.slowTime = 0; this.capsuleActive = false; this.capsuleX = this.capsuleY = 0;
      this.capsuleKind = KINDS[0]; this.capsuleSpin = 0; this.capsuleTimer = G.CAPSULE_INTERVAL;
      this.ballVx = 0; this.ballVy = 0; this.ballSpin = 0; this.ballVisible = true; this.serveTimer = G.SERVE_DELAY;
      this.placeBallOnPaddle();
      this.rebuildTimer = null; this.buildBricks(true);
      this.ufoLightAngle = 0; this.ufoWobble = 0; this.ufoCooldown = 0; this.moveUfo(0);
      this.scorePulse = 0; this.heartPopIndex = null; this.heartPopTime = 0;
      this.events = []; this.event("New game - break all the bricks!");
    }
    buildBricks(animated) {
      this.bricks = [];
      for (let row = 0; row < G.BRICK_ROWS; row++) {
        const line = [];
        for (let col = 0; col < G.BRICK_COLS; col++) {
          line.push({ alive: true, visible: true, scale: animated ? 0 : 1, alpha: 1, angle: 0, drop: 0,
                      phase: animated ? "build" : "idle", t: 0, delay: G.BUILD_STAGGER * (row * G.BRICK_COLS + col),
                      spin: (row + col) % 2 === 0 ? 1 : -1 });
        }
        this.bricks.push(line);
      }
      this.bricksLeft = G.BRICK_ROWS * G.BRICK_COLS;
    }
    toggleAttract() { this.attract = !this.attract; this.event(this.attract ? "Demo mode on - the paddle plays by itself" : "Demo mode off - your turn"); }
    launch() { if (this.state === "serve" && this.rebuildTimer === null) this._launch(); }
    popEvents() { const e = this.events; this.events = []; return e; }
    event(text) { this.events.push(text); }
    get banner() { if (this.state === "game_over") return "GAME OVER"; if (this.state === "serve") return this.level > 1 ? "LEVEL " + this.level : "GET READY"; return ""; }
    currentBallSpeed() { let s = this.ballSpeed * (1 + G.LEVEL_SPEEDUP * (this.level - 1)); if (this.slowTime > 0) s *= G.SLOW_FACTOR; return clamp(s, 0.5, G.MAX_BALL_SPEED); }

    update(dt) {
      if (!(dt > 0)) return;
      dt = Math.min(dt, 0.5); this.time += dt; this.stateTime += dt;
      this.updatePowerUps(dt); this.movePaddle(dt); this.moveJoystick(dt); this.moveUfo(dt);
      if (this.state === "serve") this.updateServe(dt);
      else if (this.state === "play") this.moveBall(dt);
      else this.updateGameOver();
      this.moveCapsule(dt); this.animateBricks(dt); this.animateHud(dt);
    }
    movePaddle(dt) {
      const dir = clamp(this.attract ? this.attractDirection(dt) : this.paddleInput, -1, 1);
      const old = this.paddleX, half = this.paddleHalfWidth();
      this.paddleX = clamp(this.paddleX + dir * G.PADDLE_SPEED * dt, G.WORLD_LEFT + half, G.WORLD_RIGHT - half);
      this.paddleVelocity = (this.paddleX - old) / dt;
    }
    moveJoystick(dt) {
      const target = -G.JOYSTICK_MAX_TILT * clamp(this.paddleVelocity / G.PADDLE_SPEED, -1, 1);
      this.joystickTilt += (target - this.joystickTilt) * Math.min(1, 15 * dt);
    }
    moveUfo(dt) {
      [this.ufoX, this.ufoY, this.ufoVx, this.ufoVy] = ufoPath(this.time);
      this.ufoHeading = deg(Math.atan2(this.ufoVy, this.ufoVx));
      this.ufoWobble *= Math.exp(-3 * dt);
      this.ufoAngle = uprightTilt(this.ufoHeading) + 20 * this.ufoWobble * Math.sin(25 * this.time);
      this.ufoLightAngle = mod(this.ufoLightAngle + this.ufoOrbitSpeed * dt, 360);
      this.ufoCooldown = Math.max(0, this.ufoCooldown - dt);
    }
    placeBallOnPaddle() { this.ballX = this.paddleX; this.ballY = G.PADDLE_Y + G.PADDLE_HALF_HEIGHT + G.BALL_RADIUS + 0.01; }
    updateServe(dt) {
      if (this.rebuildTimer !== null) { this.rebuildTimer -= dt; if (this.rebuildTimer <= 0) { this.rebuildTimer = null; this.buildBricks(true); } }
      this.placeBallOnPaddle();
      this.serveTimer -= dt;
      if (this.serveTimer <= 0 && this.rebuildTimer === null) this._launch();
    }
    _launch() {
      const a = rad(-G.SERVE_ANGLE_DEG + this.rand() * 2 * G.SERVE_ANGLE_DEG), s = this.currentBallSpeed();
      this.ballVx = s * Math.sin(a); this.ballVy = s * Math.cos(a); this.setState("play");
    }
    updateGameOver() { if (this.attract && this.stateTime >= G.GAME_OVER_RESTART) { this.newGame(); this.event("Demo mode: new game"); } }
    setState(s) { this.state = s; this.stateTime = 0; }
    moveBall(dt) {
      const speed = this.currentBallSpeed();
      let len = Math.hypot(this.ballVx, this.ballVy);
      if (len < 1e-9) { this.ballVx = 0; this.ballVy = speed; len = speed; }
      this.ballVx *= speed / len; this.ballVy *= speed / len;
      const steps = Math.max(1, Math.ceil((speed * dt) / (0.5 * G.BALL_RADIUS))), h = dt / steps;
      for (let i = 0; i < steps; i++) {
        this.ballX += this.ballVx * h; this.ballY += this.ballVy * h;
        this.collideWalls(); this.collidePaddle(); this.collideUfo(); this.collideBricks();
        if (this.state !== "play") return;
        if (this.ballY < G.WORLD_BOTTOM - G.BALL_RADIUS) { this.loseBall(); return; }
      }
      this.ballSpin = mod(this.ballSpin - deg((this.ballVx * dt) / G.BALL_RADIUS), 360);
    }
    bounce(nx, ny, depth) {
      this.ballX += nx * depth; this.ballY += ny * depth;
      const dot = this.ballVx * nx + this.ballVy * ny;
      if (dot >= 0) return false;
      this.ballVx -= 2 * dot * nx; this.ballVy -= 2 * dot * ny; this.keepSteep();
      return true;
    }
    keepSteep() {
      const s = Math.hypot(this.ballVx, this.ballVy);
      if (Math.abs(this.ballVy) < G.MIN_VERTICAL * s) {
        const sy = this.ballVy > 0 ? 1 : -1, sx = this.ballVx >= 0 ? 1 : -1;
        this.ballVy = sy * G.MIN_VERTICAL * s; this.ballVx = sx * Math.sqrt(s * s - this.ballVy ** 2);
      }
    }
    collideWalls() {
      const right = G.WORLD_RIGHT - G.BALL_RADIUS, left = G.WORLD_LEFT + G.BALL_RADIUS, top = G.WORLD_TOP - G.BALL_RADIUS;
      if (this.ballX > right) this.bounce(-1, 0, this.ballX - right);
      else if (this.ballX < left) this.bounce(1, 0, left - this.ballX);
      if (this.ballY > top) this.bounce(0, -1, this.ballY - top);
    }
    collidePaddle() {
      if (this.ballVy > 0) return;
      const half = this.paddleHalfWidth();
      const c = circleRectContact(this.ballX, this.ballY, G.BALL_RADIUS, this.paddleX, G.PADDLE_Y, half, G.PADDLE_HALF_HEIGHT);
      if (!c) return;
      if (c[1] > 0.5) {
        const off = clamp((this.ballX - this.paddleX) / half, -1, 1), a = rad(off * G.MAX_BOUNCE_DEG), s = Math.hypot(this.ballVx, this.ballVy);
        this.ballVx = s * Math.sin(a); this.ballVy = s * Math.cos(a);
        this.ballY = G.PADDLE_Y + G.PADDLE_HALF_HEIGHT + G.BALL_RADIUS; this.paddleDip = 1;
      } else this.bounce(...c);
    }
    collideUfo() {
      if (this.ufoCooldown > 0) return;
      const c = circleRectContact(this.ballX, this.ballY, G.BALL_RADIUS, this.ufoX, this.ufoY, G.UFO_HALF_W, G.UFO_HALF_H);
      if (!c) return;
      this.bounce(...c); this.ufoCooldown = G.UFO_HIT_COOLDOWN; this.ufoWobble = 1;
      this.addScore(G.UFO_POINTS); this.event("UFO hit! +" + G.UFO_POINTS); this.dropCapsule();
    }
    collideBricks() {
      const px = G.BRICK_W + G.BRICK_GAP_X, py = G.BRICK_H + G.BRICK_GAP_Y;
      const col0 = Math.round((this.ballX - (G.WORLD_LEFT + 1)) / px), row0 = Math.round((G.BRICK_TOP_Y - this.ballY) / py);
      let best = null;
      for (let row = Math.max(0, row0 - 1); row < Math.min(G.BRICK_ROWS, row0 + 2); row++) {
        for (let col = Math.max(0, col0 - 1); col < Math.min(G.BRICK_COLS, col0 + 2); col++) {
          if (!this.bricks[row][col].alive) continue;
          const [bx, by] = brickCenter(row, col);
          const c = circleRectContact(this.ballX, this.ballY, G.BALL_RADIUS, bx, by, G.BRICK_W / 2, G.BRICK_H / 2);
          if (c && (!best || c[2] > best[0][2])) best = [c, row, col];
        }
      }
      if (best && this.bounce(...best[0])) this.breakBrick(best[1], best[2]);
    }
    breakBrick(row, col) {
      const b = this.bricks[row][col];
      b.alive = false; b.phase = "break"; b.t = 0; this.bricksLeft -= 1; this.addScore(G.BRICK_POINTS);
      if (this.bricksLeft === 0) this.nextLevel();
    }
    loseBall() {
      this.lives -= 1; this.heartPopIndex = this.lives; this.heartPopTime = 0;
      this.capsuleActive = false; this.wideTime = this.slowTime = 0;
      if (this.lives <= 0) {
        this.lives = 0; this.ballVisible = false; this.setState("game_over");
        this.event("Game over - score " + this.score + ". Press R or Reset for a new game");
      } else {
        this.setState("serve"); this.serveTimer = G.SERVE_DELAY; this.placeBallOnPaddle();
        this.event("Ball lost - " + this.lives + (this.lives === 1 ? " life" : " lives") + " left");
      }
    }
    nextLevel() {
      this.level += 1; this.capsuleActive = false; this.setState("serve");
      this.serveTimer = G.LEVEL_SERVE_DELAY; this.rebuildTimer = G.BREAK_TIME + 0.15; this.placeBallOnPaddle();
      this.event("Level " + this.level + "! The ball is " + Math.round(100 * G.LEVEL_SPEEDUP * (this.level - 1)) + "% faster");
    }
    addScore(p) { this.score += p; this.scorePulse = 1; if (!this.attract && this.score > this.highScore) this.highScore = this.score; }
    dropCapsule() {
      if (this.capsuleActive || this.state !== "play" || Math.abs(this.ufoX) > G.UFO_VISIBLE_X) return false;
      let r = this.rand(), i = 0;
      while (i < KINDS.length - 1 && r >= WEIGHTS[i]) { r -= WEIGHTS[i]; i++; }
      this.capsuleKind = KINDS[i]; this.capsuleActive = true;
      this.capsuleX = this.ufoX; this.capsuleY = this.ufoY - 0.6; this.capsuleSpin = 0;
      return true;
    }
    moveCapsule(dt) {
      if (this.state === "play") { this.capsuleTimer -= dt; if (this.capsuleTimer <= 0 && this.dropCapsule()) this.capsuleTimer = G.CAPSULE_INTERVAL; }
      if (!this.capsuleActive) return;
      this.capsuleY -= G.CAPSULE_FALL_SPEED * dt; this.capsuleSpin = mod(this.capsuleSpin + G.CAPSULE_SPIN_SPEED * dt, 360);
      if (rectsOverlap(this.capsuleX, this.capsuleY, G.CAPSULE_HALF_W, G.CAPSULE_HALF_H, this.paddleX, G.PADDLE_Y, this.paddleHalfWidth(), G.PADDLE_HALF_HEIGHT)) this.catchCapsule();
      else if (this.capsuleY < G.WORLD_BOTTOM - 1) this.capsuleActive = false;
    }
    catchCapsule() {
      this.capsuleActive = false; this.addScore(G.CAPSULE_POINTS);
      if (this.capsuleKind === "wide") { this.wideTime = G.WIDE_TIME; this.event("Power-up: wide paddle for " + G.WIDE_TIME + " s"); }
      else if (this.capsuleKind === "slow") { this.slowTime = G.SLOW_TIME; this.event("Power-up: slow ball for " + G.SLOW_TIME + " s"); }
      else { this.lives = Math.min(G.MAX_LIVES, this.lives + 1); this.event("Power-up: extra life (" + this.lives + " lives)"); }
    }
    updatePowerUps(dt) {
      this.wideTime = Math.max(0, this.wideTime - dt); this.slowTime = Math.max(0, this.slowTime - dt);
      const target = this.wideTime > 0 ? G.WIDE_FACTOR : 1;
      this.paddleBoost += (target - this.paddleBoost) * Math.min(1, 6 * dt);
    }
    animateBricks(dt) {
      for (const line of this.bricks) for (const b of line) {
        if (b.phase === "idle" || b.phase === "gone") continue;
        b.t += dt;
        if (b.phase === "break") {
          const p = b.t / G.BREAK_TIME;
          if (p >= 1) { Object.assign(b, { phase: "gone", visible: false, scale: 0, alpha: 0 }); continue; }
          b.scale = 1 - p; b.alpha = 1 - p; b.angle = 180 * p * b.spin; b.drop = 1.5 * p * p;
        } else {
          const p = (b.t - b.delay) / G.BUILD_TIME;
          b.scale = p > 0 ? easeOutBack(p) : 0;
          if (p >= 1) { b.phase = "idle"; b.scale = 1; }
        }
      }
    }
    animateHud(dt) {
      this.scorePulse *= Math.exp(-5 * dt); this.paddleDip *= Math.exp(-8 * dt);
      if (this.heartPopIndex !== null) { this.heartPopTime += dt; if (this.heartPopTime >= G.HEART_POP_TIME) this.heartPopIndex = null; }
    }
    attractDirection(dt) { const diff = this.attractTarget() - this.paddleX; return Math.abs(diff) < 0.02 ? 0 : clamp(diff / (G.PADDLE_SPEED * dt), -1, 1); }
    attractTarget() {
      const half = this.paddleHalfWidth();
      if (this.state !== "play") return this.capsuleActive ? this.capsuleX : 0;
      const hitY = G.PADDLE_Y + G.PADDLE_HALF_HEIGHT + G.BALL_RADIUS;
      if (this.ballVy < 0) {
        const t = (this.ballY - hitY) / -this.ballVy;
        const x = foldBetween(this.ballX + this.ballVx * t, G.WORLD_LEFT + G.BALL_RADIUS, G.WORLD_RIGHT - G.BALL_RADIUS);
        return x - this.attractAim(x, hitY) * half;
      }
      return this.capsuleActive ? this.capsuleX : this.ballX;
    }
    attractAim(x, hitY) {
      let bestCol = null, bestCount = 0;
      for (let col = 0; col < G.BRICK_COLS; col++) {
        let n = 0; for (let row = 0; row < G.BRICK_ROWS; row++) if (this.bricks[row][col].alive) n++;
        if (n > bestCount) { bestCol = col; bestCount = n; }
      }
      if (bestCol === null) return 0;
      let low = 0; for (let row = 0; row < G.BRICK_ROWS; row++) if (this.bricks[row][bestCol].alive) low = row;
      const [tx, ty] = brickCenter(low, bestCol);
      return clamp(deg(Math.atan2(tx - x, ty - hitY)) / G.MAX_BOUNCE_DEG, -0.85, 0.85);
    }
  }

  // ===================================================================== render2d.py scene (Member 2) + anim2d.py (Member 3)
  const BRICK_COLOURS = [[0.95, 0.26, 0.21], [1, 0.6, 0], [1, 0.92, 0.23], [0.3, 0.69, 0.31], [0.13, 0.59, 0.95]];
  const CAPSULE_COLOURS = { wide: [0.25, 0.65, 1], slow: [0.3, 0.9, 0.45], life: [1, 0.35, 0.55] };
  function buildScene2D() {
    const root = new Node("world");
    root.add(new Node("cabinet_frame", rect(20, 15), [0.35, 0.38, 0.45]));
    root.add(new Node("left_wall", rect(0.2, 14.6), [0.45, 0.5, 0.6], 2, { tx: G.WORLD_LEFT + 0.1 }));
    root.add(new Node("right_wall", rect(0.2, 14.6), [0.45, 0.5, 0.6], 2, { tx: G.WORLD_RIGHT - 0.1 }));
    root.add(new Node("top_wall", rect(19.8, 0.2), [0.45, 0.5, 0.6], 2, { ty: G.WORLD_TOP - 0.1 }));
    root.add(new Node("paddle", roundedPaddle(2 * G.PADDLE_HALF_WIDTH, 0.4), [0.2, 0.85, 1], 2, { ty: G.PADDLE_Y }));
    root.add(new Node("ball", circle(G.BALL_RADIUS, 24), [1, 1, 1]));
    const bricks = root.add(new Node("bricks"));
    for (let row = 0; row < G.BRICK_ROWS; row++) for (let col = 0; col < G.BRICK_COLS; col++) {
      const [x, y] = brickCenter(row, col);
      bricks.add(new Node("brick_" + row + "_" + col, rect(G.BRICK_W, G.BRICK_H), BRICK_COLOURS[row % 5], 2, { tx: x, ty: y }));
    }
    const ufo = root.add(new Node("ufo", ufoBody(2, 0.8), [0.5, 0.95, 0.5], 2, { ty: 6.4 }));
    ufo.add(new Node("ufo_dome", ufoDome(1, 0.5), [0.7, 1, 0.8], 2, { ty: 0.15 }));
    const ring = ufo.add(new Node("ufo_light_ring"));
    for (let i = 0; i < 4; i++) {
      const a = rad(90 * i);
      ring.add(new Node("ufo_light_" + i, regularPolygon(8, 0.12), [1, 0.92, 0.2], 2, { tx: Math.cos(a), ty: 0.35 * Math.sin(a) }));
    }
    const lives = root.add(new Node("lives", null, [1, 1, 1], 2, { tx: -8.2, ty: 6.8 }));
    for (let i = 0; i < G.MAX_LIVES; i++) lives.add(new Node("heart_" + i, heart(0.35), [0.95, 0.2, 0.3], 2, { tx: i * 0.8 }));
    const controls = root.add(new Node("controls_panel", null, [1, 1, 1], 2, { ty: -7.1 }));
    const joy = controls.add(new Node("joystick", joystickBase(1, 0.3), [0.25, 0.25, 0.3], 2, { tx: -5 }));
    const pivot = joy.add(new Node("joystick_pivot", null, [1, 1, 1], 2, { ty: 0.1 }));
    const stick = pivot.add(new Node("joystick_stick", rect(0.12, 0.5), [0.6, 0.6, 0.6], 2, { ty: 0.25 }));
    stick.add(new Node("joystick_knob", circle(0.2, 16), [0.9, 0.15, 0.15], 2, { ty: 0.25 }));
    controls.add(new Node("button_1", regularPolygon(16, 0.22), [0.9, 0.2, 0.2], 2, { tx: 4.5 }));
    controls.add(new Node("button_2", regularPolygon(16, 0.22), [0.2, 0.8, 0.3], 2, { tx: 5.2 }));
    controls.add(new Node("button_3", regularPolygon(16, 0.22), [0.2, 0.5, 0.9], 2, { tx: 5.9 }));
    root.add(new Node("capsule", capsuleShape(G.CAPSULE_HALF_W, G.CAPSULE_HALF_H), CAPSULE_COLOURS.wide));   // anim2d.ensure_nodes
    root.byName = Object.fromEntries(root.allNodes().map((n) => [n.name, n]));
    root.memory = {};
    return root;
  }
  function changed(memory, key, value) { if (key in memory && memory[key] === value) return false; memory[key] = value; return true; }
  function sync2D(root, g) {                         // anim2d.sync (Member 3)
    const n = root.byName, mem = root.memory;
    const ball = n.ball;
    ball.tx = g.ballX; ball.ty = g.ballY; ball.angle = g.ballSpin;
    if (changed(mem, "ballVisible", g.ballVisible)) ball.visible = g.ballVisible;
    const paddle = n.paddle;
    paddle.tx = g.paddleX; paddle.ty = G.PADDLE_Y - 0.12 * g.paddleDip; paddle.sx = g.paddleWidth;
    for (const node of n.bricks.children) {
      const [, r, c] = node.name.split("_"), row = +r, col = +c, b = g.bricks[row][col];
      if (changed(mem, "brick" + row + "_" + col, b.phase)) {
        node.visible = b.visible;
        if (b.phase === "idle") { [node.tx, node.ty] = brickCenter(row, col); node.angle = 0; node.sx = node.sy = 1; }
      }
      if (b.phase === "build" || b.phase === "break") {
        const [x, y] = brickCenter(row, col);
        node.tx = x; node.ty = y - b.drop; node.angle = b.angle; node.sx = node.sy = b.scale;
      }
    }
    n.ufo.tx = g.ufoX; n.ufo.ty = g.ufoY; n.ufo.angle = g.ufoAngle;
    n.ufo_light_ring.angle = g.ufoLightAngle;
    for (let i = 0; i < 4; i++) { const wave = 0.5 + 0.5 * Math.sin(6 * g.time - (i * PI) / 2); n["ufo_light_" + i].sx = n["ufo_light_" + i].sy = 0.8 + 0.6 * wave; }
    const cap = n.capsule;
    cap.visible = g.capsuleActive;
    if (g.capsuleActive) {
      cap.tx = g.capsuleX; cap.ty = g.capsuleY; cap.angle = g.capsuleSpin; cap.sx = cap.sy = 1 + 0.12 * Math.sin(10 * g.time);
      if (changed(mem, "capsuleKind", g.capsuleKind)) cap.color = CAPSULE_COLOURS[g.capsuleKind].slice();
    }
    n.joystick_pivot.angle = g.joystickTilt;
    const beat = 1 + 0.1 * Math.max(0, Math.sin(2 * PI * (g.lives === 1 ? 2.4 : 1.2) * g.time));
    for (let i = 0; i < G.MAX_LIVES; i++) {
      const h = n["heart_" + i];
      let s;
      if (i === g.heartPopIndex) { const p = g.heartPopTime / G.HEART_POP_TIME; s = p < 0.4 ? 1 + p / 0.4 : 2 * (1 - (p - 0.4) / 0.6); h.visible = true; }
      else { s = beat; h.visible = i < g.lives; }
      h.sx = h.sy = Math.max(0, s);
    }
  }

  // ===================================================================== drawing helpers
  const css = (c, k = 1) => "rgb(" + c.map((v) => Math.round(clamp(v * k, 0, 1) * 255)).join(",") + ")";
  const CLEAR = "rgb(5,5,15)";                       // glClearColor(0.02, 0.02, 0.06)

  function letterbox(w, h) {                         // render2d.compute_letterbox (Member 2)
    const target = 20 / 15, win = w / Math.max(1, h);
    if (win > target) { const vw = Math.floor(h * target); return [Math.floor((w - vw) / 2), 0, vw, h]; }
    const vh = Math.floor(w / target); return [0, Math.floor((h - vh) / 2), w, vh];
  }

  /* 2D: like glOrtho + glMultMatrixf. pixel = Screen . world(node) . vertex */
  function draw2D(ctx, root, W, H) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = CLEAR; ctx.fillRect(0, 0, W, H);
    const [vx, vy, vw, vh] = letterbox(W, H);
    const k = vw / 20;                               // pixels per world unit
    const screen = [[k, 0, vx + vw / 2], [0, -k, vy + vh / 2], [0, 0, 1]];  // world -> pixels (y flips)
    ctx.lineJoin = "round";
    walk(root, null, (node, world) => {
      const m = mul(screen, world);
      ctx.setTransform(m[0][0], m[1][0], m[0][1], m[1][1], m[0][2], m[1][2]);
      ctx.beginPath();
      node.figure.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      ctx.closePath();
      ctx.setTransform(1, 0, 0, 1, 0, 0);            // stroke width in pixels, like glLineWidth
      ctx.fillStyle = css(node.color); ctx.fill();
      ctx.lineWidth = Math.max(1, 1.2 * (W / 800)); ctx.strokeStyle = css(node.color, 0.7); ctx.stroke();
    });
  }

  // ===================================================================== render3d.py (Member 4)
  function buildScene3D() {
    const root = new Node("world", null, [1, 1, 1], 3);
    root.add(new Node("paddle", box(2 * G.PADDLE_HALF_WIDTH, 0.4, 0.6), [0.2, 0.85, 1], 3, { ty: G.PADDLE_Y }));
    root.add(new Node("ball", "sphere", [1, 1, 1], 3));                       // gluSphere(0.3)
    const bricks = root.add(new Node("bricks", null, [1, 1, 1], 3));
    for (let row = 0; row < G.BRICK_ROWS; row++) for (let col = 0; col < G.BRICK_COLS; col++) {
      const [x, y] = brickCenter(row, col);
      bricks.add(new Node("brick_" + row + "_" + col, bevelledBrick(G.BRICK_W, G.BRICK_H, 0.6), [0.9, 0.45, 0.3], 3, { tx: x, ty: y }));
    }
    const tro = root.add(new Node("trophy", trophy(), [1, 0.84, 0], 3, { ty: 9, tz: -4 }));
    tro.add(new Node("star", star(), [1, 1, 0.6], 3, { tx: 2, ty: 0.5 }));
    root.byName = Object.fromEntries(root.allNodes().map((n) => [n.name, n]));
    return root;
  }
  function sync3D(root, g, dt) {
    const n = root.byName;
    n.ball.tx = g.ballX; n.ball.ty = g.ballY; n.ball.rz = g.ballSpin; n.ball.visible = g.ballVisible;
    n.paddle.tx = g.paddleX; n.paddle.sx = g.paddleWidth;
    for (const node of n.bricks.children) { const [, r, c] = node.name.split("_"); node.visible = g.bricks[+r][+c].alive; }
    n.trophy.ry += 45 * dt;
    const s = n.star; s.ry += 90 * dt;
    s.tx = 2 * Math.cos(rad(s.ry)); s.tz = 2 * Math.sin(rad(s.ry));
  }
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
  function lookAt(eye, target, up) {                 // what gluLookAt builds
    const f = norm(sub(target, eye)), s = norm(cross(f, up)), u = cross(s, f);
    return mul([[s[0], s[1], s[2], 0], [u[0], u[1], u[2], 0], [-f[0], -f[1], -f[2], 0], [0, 0, 0, 1]], translate3(-eye[0], -eye[1], -eye[2]));
  }
  function cameraEye(cam) {                          // Member 4's orbit camera
    const y = rad(cam.yaw), p = rad(cam.pitch);
    return [cam.distance * Math.cos(p) * Math.sin(y), 1 + cam.distance * Math.sin(p), cam.distance * Math.cos(p) * Math.cos(y)];
  }
  const LIGHT = [5, 8, 10];                          // glLightfv(GL_LIGHT0, GL_POSITION, (5, 8, 10, 1))
  function draw3D(ctx, root, W, H, cam) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = CLEAR; ctx.fillRect(0, 0, W, H);
    const eye = cameraEye(cam), view = lookAt(eye, [0, 1, 0], [0, 1, 0]);
    const f = 1 / Math.tan(rad(45) / 2), aspect = W / H;  // gluPerspective(45, aspect, 0.1, 100)
    const project = ([x, y, z]) => [((f / aspect) * x / -z + 1) * W / 2, (1 - (f * y) / -z) * H / 2];
    const items = [];
    walk(root, null, (node, world) => {
      if (node.figure === "sphere") {
        const [c] = apply3(world, [[0, 0, 0]]), [v] = apply3(view, [c]);
        if (v[2] > -0.1) return;
        const [sx, sy] = project(v), r = (0.3 * f) / -v[2] * H / 2;
        items.push({ z: v[2], sphere: true, sx, sy, r, color: node.color, toLight: norm(sub(LIGHT, c)) });
        return;
      }
      const [verts, faces] = node.figure;
      const wv = apply3(world, verts), vv = apply3(view, wv);
      for (const face of faces) {
        let n = [0, 0, 0], c = [0, 0, 0];
        for (let i = 0; i < face.length; i++) {        // Newell's method: robust face normal
          const a = wv[face[i]], b = wv[face[(i + 1) % face.length]];
          n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1]);
          c[0] += a[0]; c[1] += a[1]; c[2] += a[2];
        }
        c = c.map((v) => v / face.length);
        if (dot(n, sub(eye, c)) <= 0) continue;          // back face: hidden
        let z = 0, behind = false;
        const pts = face.map((i) => { const v = vv[i]; z += v[2]; if (v[2] > -0.1) behind = true; return project(v); });
        if (behind) continue;
        const light = 0.2 + Math.max(0, dot(norm(n), norm(sub(LIGHT, c))));   // ambient + diffuse
        items.push({ z: z / face.length, pts, color: css(node.color, light) });
      }
    });
    items.sort((a, b) => a.z - b.z);                 // painter's algorithm: far first
    for (const it of items) {
      if (it.sphere) {
        const g = ctx.createRadialGradient(it.sx - it.r * 0.35 * it.toLight[0], it.sy - it.r * 0.35 * it.toLight[1], it.r * 0.1, it.sx, it.sy, it.r);
        g.addColorStop(0, css(it.color)); g.addColorStop(1, css(it.color, 0.35));
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(it.sx, it.sy, it.r, 0, 2 * PI); ctx.fill();
        continue;
      }
      ctx.beginPath();
      it.pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      ctx.closePath();
      ctx.fillStyle = it.color; ctx.fill();
      ctx.lineWidth = 0.75; ctx.strokeStyle = it.color; ctx.stroke();   // hides seams between faces
    }
  }
  const camera = {
    yaw: 0, pitch: 15, distance: 27,                 // gui.CameraControls defaults (whole field + trophy in view)
    drag(dx, dy) { this.yaw = mod(this.yaw + dx * 0.5 + 180, 360) - 180; this.pitch = clamp(this.pitch + dy * 0.5, -80, 80); },
    wheel(steps) { this.distance = clamp(this.distance - steps * 1.5, 8, 40); },
  };

  const api = { G, Game, Node, mul, compose, apply2, rotate2, translate2, scale2, foldBetween, ufoPath, circleRectContact, letterbox,
                brickCenter, buildScene2D, sync2D, draw2D, buildScene3D, sync3D, draw3D, camera, walk };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Breakout = api;
})(typeof window !== "undefined" ? window : globalThis);
