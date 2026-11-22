/* app.js - intro, START zoom and the playable game layer.
 *
 * The game itself is engine.js: the browser port of the team's Python program
 * (same rules, figures, scene graph and matrices). This file only wires it to
 * the page: the intro (arcade.js, a presentation extra), the START button, the
 * keyboard / mouse / touch controls and the score bar.
 *
 * Modes:  intro -> zoom-in -> fade-in -> game -> fade-out -> zoom-out -> intro
 * The zoom ends with the 3D screen covering exactly the HTML game canvas, which
 * shows the same frame, so the game layer can simply cross-fade in on top.
 */
(function () {
  "use strict";
  const B = window.Breakout, G = B.G;
  const $ = (id) => document.getElementById(id);
  const reduced = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  const canvas = $("screen"), ctx = canvas.getContext("2d");
  const gameMode = $("gameMode"), introUi = $("introUi"), stage = $("stage");
  const ZOOM_SECONDS = reduced ? 0 : 2.6, FADE_MS = reduced ? 0 : 650;

  let mode = "intro";
  let game, scene2, scene3, view = "2D", paused = false, speed = 1, best = 0;
  try { best = +localStorage.getItem("arcade-breakout-best") || 0; } catch (e) { /* private mode */ }
  const held = { left: false, right: false };
  let pointerX = null, dragging = null, toastTimer = 0, introClock = 0, fx = 1;
  const introCam = { yaw: -25, pitch: 15, distance: 27 };   // 3D demo camera on the cabinet's screen

  function newGame(attract) {
    game = new B.Game(Math.floor(Math.random() * 1e6));
    game.highScore = best;
    if (attract) game.toggleAttract();
    game.popEvents();
    scene2 = B.buildScene2D(); scene3 = B.buildScene3D();
    B.sync2D(scene2, game); B.sync3D(scene3, game, 0);
  }
  newGame(true);                                      // the cabinet plays its demo

  // ------------------------------------------------------------------ the intro text appears once the fonts are in
  let revealed = false;
  function reveal() { if (!revealed) { revealed = true; introUi.classList.add("ready"); } }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(reveal, reveal);
  setTimeout(reveal, 700);

  // ------------------------------------------------------------------ canvas size
  function setCanvasSize(w, h) { if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; } }
  function fit() {
    if (gameMode.hidden) return;
    const w = canvas.clientWidth, dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (w > 0) setCanvasSize(Math.round(w * dpr), Math.round(w * 0.75 * dpr));
  }
  new ResizeObserver(fit).observe(canvas);
  function canvasRect() {                             // the game canvas, in the 3D stage's pixels
    const r = canvas.getBoundingClientRect(), s = stage.getBoundingClientRect();
    return { x: r.left - s.left, y: r.top - s.top, w: r.width, h: r.height };
  }

  // ------------------------------------------------------------------ the 3D arcade (optional)
  let arcade = null;
  try { arcade = window.Arcade.create(stage, canvas, { reduced }); }
  catch (e) { console.warn("3D intro unavailable:", e.message); stage.classList.add("fallback"); }
  let introVisible = true;
  new IntersectionObserver((entries) => { introVisible = entries[0].isIntersecting; }).observe($("intro"));

  function coinSound() {                              // a soft two-note coin chime
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)(), t = ac.currentTime;
      [[988, 0], [1319, 0.085]].forEach(([f, at]) => {
        const o = ac.createOscillator(), g = ac.createGain();
        o.type = "triangle"; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, t + at); g.gain.exponentialRampToValueAtTime(0.06, t + at + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t + at + 0.35);
        o.connect(g); g.connect(ac.destination); o.start(t + at); o.stop(t + at + 0.4);
      });
    } catch (e) { /* no sound */ }
  }

  // ------------------------------------------------------------------ START: zoom in, cross-fade into the game
  function start() {
    if (mode !== "intro") return;
    coinSound();
    window.scrollTo(0, 0);
    introUi.classList.add("gone"); $("scrollHint").classList.add("gone");
    document.documentElement.style.overflow = "hidden";
    // Lay the game layer out (still invisible) so the camera knows where to land.
    gameMode.hidden = false; gameMode.classList.remove("show");
    fit();
    // A fresh game for the player: its bricks pop in on the cabinet screen during the
    // flight, and it waits to serve until a moment after the game layer is up.
    newGame(false); paused = false; view = "2D"; refreshButtons();
    game.serveTimer = ZOOM_SECONDS + FADE_MS / 1000 + 1.2;
    mode = "zoom-in";
    if (!arcade) { showGame(); return; }
    arcade.zoomIn(canvasRect, (p) => { fx = 1 - p * p; }, showGame);
  }
  function showGame() {
    mode = "fade-in"; fx = 0;
    gameMode.classList.add("show");
    setTimeout(() => { if (mode === "fade-in") mode = "game"; }, FADE_MS);
  }

  // ------------------------------------------------------------------ back: cross-fade out, zoom out
  function exitGame() {
    if (mode !== "game") return;
    mode = "fade-out"; fx = 0;
    held.left = held.right = false; pointerX = null; dragging = null; paused = false;
    if (!game.attract) game.toggleAttract();          // the cabinet plays on by itself
    game.popEvents();
    if (arcade) arcade.holdAt(canvasRect);            // the 3D screen sits right under the canvas
    gameMode.classList.remove("show");
    setTimeout(() => {
      gameMode.hidden = true;
      document.documentElement.style.overflow = "";
      setCanvasSize(960, 720);
      mode = "zoom-out";
      if (arcade) arcade.zoomOut(backToIntro); else backToIntro();
    }, FADE_MS);
  }
  function backToIntro() {
    mode = "intro"; view = "2D"; introClock = 0;
    introUi.classList.remove("gone"); $("scrollHint").classList.remove("gone");
    $("start").focus({ preventScroll: true });
  }
  $("start").addEventListener("click", start);
  $("exit").addEventListener("click", exitGame);

  // ------------------------------------------------------------------ game controls
  function togglePause() { paused = !paused; refreshButtons(); }
  function setView(v) { view = v; refreshButtons(); }
  function toggleDemo() { game.toggleAttract(); showToast(game.popEvents().pop()); refreshButtons(); }
  function reset() { newGame(false); paused = false; showToast("New game"); refreshButtons(); }
  function refreshButtons() {
    $("view2d").setAttribute("aria-pressed", view === "2D"); $("view3d").setAttribute("aria-pressed", view === "3D");
    $("pause").textContent = paused ? "Resume" : "Pause";
    $("demo").setAttribute("aria-pressed", game.attract);
    canvas.style.cursor = view === "3D" ? "grab" : "crosshair";
  }
  function showToast(text) { if (!text) return; const t = $("toast"); t.textContent = text; t.hidden = false; toastTimer = 2.6; }

  $("reset").addEventListener("click", reset);
  $("pause").addEventListener("click", togglePause);
  $("serve").addEventListener("click", () => game.launch());
  $("demo").addEventListener("click", toggleDemo);
  $("view2d").addEventListener("click", () => setView("2D"));
  $("view3d").addEventListener("click", () => setView("3D"));
  $("speed").addEventListener("input", (e) => { speed = +e.target.value; $("speedOut").textContent = speed.toFixed(1) + "x"; });
  document.querySelectorAll(".deck button, .views button").forEach((b) => b.addEventListener("click", () => b.blur()));
  for (const side of ["left", "right"]) {             // hold-to-move buttons for touch screens
    const b = $(side);
    b.addEventListener("pointerdown", (e) => { e.preventDefault(); held[side] = true; pointerX = null; b.classList.add("down"); });
    for (const ev of ["pointerup", "pointerleave", "pointercancel"]) b.addEventListener(ev, () => { held[side] = false; b.classList.remove("down"); });
  }

  window.addEventListener("keydown", (e) => {
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input") return;
    if (mode === "intro") {
      if (e.key === "Enter" && tag !== "button" && tag !== "a" && introVisible) { e.preventDefault(); start(); }
      return;
    }
    if (mode !== "game") { if (e.key === " " || e.key.startsWith("Arrow")) e.preventDefault(); return; }
    if (tag === "button" && (e.key === " " || e.key === "Enter")) return;   // the button handles it
    let used = true;
    switch (e.key) {
      case "ArrowLeft": held.left = true; pointerX = null; break;
      case "ArrowRight": held.right = true; pointerX = null; break;
      case "ArrowUp": game.launch(); break;
      case " ": togglePause(); break;
      case "v": case "V": setView(view === "2D" ? "3D" : "2D"); break;
      case "m": case "M": toggleDemo(); break;
      case "r": case "R": reset(); break;
      case "Escape": exitGame(); break;
      default: used = false;
    }
    if (used) e.preventDefault();
  });
  window.addEventListener("keyup", (e) => { if (e.key === "ArrowLeft") held.left = false; if (e.key === "ArrowRight") held.right = false; });
  window.addEventListener("blur", () => { held.left = held.right = false; });

  function worldX(e) {
    const r = canvas.getBoundingClientRect(), [vx, , vw] = B.letterbox(r.width, r.height);
    return G.WORLD_LEFT + ((e.clientX - r.left - vx) / vw) * (G.WORLD_RIGHT - G.WORLD_LEFT);
  }
  canvas.addEventListener("pointerdown", (e) => {
    if (mode !== "game") return;
    canvas.setPointerCapture(e.pointerId);
    if (view === "3D") { dragging = { x: e.clientX, y: e.clientY }; canvas.style.cursor = "grabbing"; return; }
    pointerX = worldX(e); game.launch();
  });
  canvas.addEventListener("pointermove", (e) => {
    if (mode !== "game") return;
    if (view === "3D") {
      if (!dragging) return;
      B.camera.drag(e.clientX - dragging.x, e.clientY - dragging.y);
      dragging = { x: e.clientX, y: e.clientY };
      return;
    }
    if ((e.pointerType === "mouse" || e.buttons) && !held.left && !held.right) pointerX = worldX(e);
  });
  const endDrag = () => { dragging = null; refreshButtons(); };
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);
  canvas.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") pointerX = null; });
  canvas.addEventListener("wheel", (e) => { if (mode !== "game" || view !== "3D") return; e.preventDefault(); B.camera.wheel(e.deltaY < 0 ? 1 : -1); }, { passive: false });

  // ------------------------------------------------------------------ the frame loop (dt-based, like main.py)
  function steer(dt) {
    if (game.attract) return;
    if (held.left || held.right) { game.paddleInput = (held.right ? 1 : 0) - (held.left ? 1 : 0); return; }
    if (pointerX !== null) {                          // chase the pointer at the normal paddle speed
      const diff = pointerX - game.paddleX;
      game.paddleInput = Math.abs(diff) < 0.05 ? 0 : Math.max(-1, Math.min(1, diff / (G.PADDLE_SPEED * Math.max(dt, 1e-3))));
      return;
    }
    game.paddleInput = 0;
  }
  const pad = (n) => String(n).padStart(5, "0");
  const shown = {};
  function hud(dt) {
    if (game.highScore > best) { best = game.highScore; try { localStorage.setItem("arcade-breakout-best", best); } catch (e) { /* ignore */ } }
    const s = { score: pad(game.score), level: game.level, lives: String.fromCharCode(0x2665).repeat(game.lives) || String.fromCharCode(0x2014), best: pad(best) };
    for (const k in s) if (shown[k] !== s[k]) { $(k).textContent = s[k]; shown[k] = s[k]; }
    const text = paused ? "PAUSED" : game.banner, banner = $("banner");
    if (banner.textContent !== text) banner.textContent = text;
    banner.hidden = !text;
    for (const ev of game.popEvents()) showToast(ev);
    if (toastTimer > 0) { toastTimer -= dt; if (toastTimer <= 0) $("toast").hidden = true; }
  }

  let last = performance.now();
  function frame(now) {
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    const playing = mode === "game";
    if (!(playing && paused)) {
      const step = dt * (playing ? speed : 1);
      if (playing) steer(step);
      game.update(step);
      B.sync2D(scene2, game);
      B.sync3D(scene3, game, step);
    }
    // What the screen shows: the player's view while the game layer is (nearly) up,
    // otherwise the cabinet's attract loop (2D for 14 s, then 3D for 7 s).
    const playerView = mode === "game" || mode === "fade-in" || mode === "fade-out" || mode === "zoom-in";
    if (playerView) {
      if (view === "2D") B.draw2D(ctx, scene2, canvas.width, canvas.height);
      else B.draw3D(ctx, scene3, canvas.width, canvas.height, B.camera);
    } else if (introVisible || mode !== "intro") {
      introClock += dt;
      if (introClock % 21 > 14) {
        introCam.yaw = -25 + 25 * Math.sin(introClock * 0.5);
        B.draw3D(ctx, scene3, canvas.width, canvas.height, introCam);
      } else {
        B.draw2D(ctx, scene2, canvas.width, canvas.height);
      }
    }
    if (mode !== "intro" && mode !== "zoom-out") hud(dt);
    // The 3D hall renders whenever it can be seen (not behind the opaque game layer).
    // Scanlines: gone while the screen is the game, back gradually while zooming out.
    if (mode === "zoom-out") fx = Math.min(1, fx + dt / 1.8);
    if (arcade && mode !== "game" && (introVisible || mode !== "intro")) arcade.update(dt, game, mode === "intro" ? 1 : fx);
    requestAnimationFrame(frame);
  }
  refreshButtons();
  requestAnimationFrame(frame);
})();
