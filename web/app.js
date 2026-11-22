/* app.js - intro, START zoom and the playable game layer.
 *
 * The game itself is engine.js: the browser port of the team's Python program
 * (same rules, figures, scene graph and matrices). This file only wires it to
 * the page: the intro (arcade.js, a presentation extra), the START button, the
 * keyboard / mouse / touch controls and the score bar.
 */
(function () {
  "use strict";
  const B = window.Breakout, G = B.G;
  const $ = (id) => document.getElementById(id);
  const reduced = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  const canvas = $("screen"), ctx = canvas.getContext("2d");
  const gameMode = $("gameMode"), introUi = $("introUi"), flash = $("flash"), screenBox = $("screenBox");

  let mode = "intro";                                 // intro -> zoom-in -> game -> zoom-out -> intro
  let game, scene2, scene3, view = "2D", paused = false, speed = 1, best = 0;
  try { best = +localStorage.getItem("arcade-breakout-best") || 0; } catch (e) { /* private mode */ }
  const held = { left: false, right: false };
  let pointerX = null, dragging = null, toastTimer = 0, introClock = 0;
  const introCam = { yaw: -25, pitch: 24, distance: 24 };   // 3D demo camera on the cabinet's screen

  function newGame(attract) {
    game = new B.Game(Math.floor(Math.random() * 1e6));
    game.highScore = best;
    if (attract) game.toggleAttract();
    game.popEvents();
    scene2 = B.buildScene2D(); scene3 = B.buildScene3D();
    B.sync2D(scene2, game); B.sync3D(scene3, game, 0);
  }
  newGame(true);                                      // the cabinet plays its demo

  // ------------------------------------------------------------------ canvas size
  function setCanvasSize(w, h) { if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; } }
  function fit() {
    if (mode !== "game") return;
    const w = canvas.clientWidth, dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (w > 0) setCanvasSize(Math.round(w * dpr), Math.round(w * 0.75 * dpr));
  }
  new ResizeObserver(fit).observe(canvas);

  // ------------------------------------------------------------------ the 3D arcade (optional)
  let arcade = null;
  try { arcade = window.Arcade.create($("stage"), canvas, { reduced }); }
  catch (e) { console.warn("3D intro unavailable:", e.message); $("stage").classList.add("fallback"); }
  let introVisible = true;
  new IntersectionObserver((entries) => { introVisible = entries[0].isIntersecting; }).observe($("intro"));

  function coinSound() {                              // two square-wave beeps, like a coin drop
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)(), o = ac.createOscillator(), g = ac.createGain(), t = ac.currentTime;
      o.type = "square"; o.frequency.setValueAtTime(988, t); o.frequency.setValueAtTime(1319, t + 0.09);
      g.gain.setValueAtTime(0.05, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);
      o.connect(g); g.connect(ac.destination); o.start(t); o.stop(t + 0.42);
    } catch (e) { /* no sound */ }
  }

  // ------------------------------------------------------------------ START, the zoom and back
  function start() {
    if (mode !== "intro") return;
    coinSound();
    window.scrollTo({ top: 0, behavior: "auto" });
    introUi.classList.add("gone"); $("scrollHint").classList.add("gone");
    mode = "zoom-in";
    if (!arcade) { enterGame(); return; }
    arcade.zoomIn((p) => { if (p > 0.82) flash.classList.add("on"); }, () => setTimeout(enterGame, reduced ? 0 : 140));
  }
  function enterGame() {
    mode = "game";
    document.documentElement.style.overflow = "hidden";
    gameMode.hidden = false;
    fit();
    newGame(false);
    paused = false; view = "2D";
    refreshButtons();
    screenBox.classList.remove("power-off"); void screenBox.offsetWidth; screenBox.classList.add("power-on");
    requestAnimationFrame(() => flash.classList.remove("on"));
  }
  function exitGame() {
    if (mode !== "game") return;
    mode = "zoom-out";
    held.left = held.right = false; pointerX = null; dragging = null;
    screenBox.classList.remove("power-on"); void screenBox.offsetWidth; screenBox.classList.add("power-off");
    setTimeout(() => {
      gameMode.hidden = true;
      document.documentElement.style.overflow = "";
      setCanvasSize(960, 720);
      newGame(true);
      if (arcade) arcade.zoomOut(backToIntro); else backToIntro();
    }, reduced ? 0 : 340);
  }
  function backToIntro() {
    mode = "intro";
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
    if (mode !== "game") return;
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
    const inGame = mode === "game";
    if (!(inGame && paused)) {
      const step = dt * (inGame ? speed : 1);
      if (inGame) steer(step);
      game.update(step);
      B.sync2D(scene2, game);
      B.sync3D(scene3, game, step);
    }
    if (inGame) {
      if (view === "2D") B.draw2D(ctx, scene2, canvas.width, canvas.height);
      else B.draw3D(ctx, scene3, canvas.width, canvas.height, B.camera);
      hud(dt);
    } else if (arcade && (introVisible || mode !== "intro")) {
      introClock += dt;                               // the cabinet shows 2D for 14 s, then 3D for 7 s
      if (introClock % 21 > 14) {
        introCam.yaw = -25 + 25 * Math.sin(introClock * 0.5);
        B.draw3D(ctx, scene3, canvas.width, canvas.height, introCam);
      } else {
        B.draw2D(ctx, scene2, canvas.width, canvas.height);
      }
      arcade.update(dt, game);
    }
    requestAnimationFrame(frame);
  }
  refreshButtons();
  requestAnimationFrame(frame);
})();
