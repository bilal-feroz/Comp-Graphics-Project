/* arcade.js - the 3D arcade hall for the intro (three.js r128).
 *
 * PRESENTATION EXTRA ("wow factor"): this file is not part of the graded
 * Python/OpenGL project. It only frames the game: the cabinet's screen shows
 * the live game canvas (engine.js), the joystick leans with the paddle and the
 * buttons light up when points are scored.
 *
 * Units are metres. The main cabinet faces +z; its screen is a 4:3 plane.
 * The zoom ends with the camera placed so the 3D screen covers exactly the
 * rectangle where the HTML game canvas sits, so the two can cross-fade.
 */
(function (root) {
  "use strict";

  function create(container, sourceCanvas, options) {
    const THREE = root.THREE;
    if (!THREE) throw new Error("three.js did not load");
    const reduced = !!(options && options.reduced);
    const rad = (d) => (d * Math.PI) / 180;

    // ------------------------------------------------------------------ renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(root.devicePixelRatio || 1, 1.5));
    container.appendChild(renderer.domElement);
    const maxAniso = renderer.capabilities.getMaxAnisotropy();

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x07060f);
    scene.fog = new THREE.Fog(0x07060f, 6, 17);
    const camera = new THREE.PerspectiveCamera(35, 1, 0.03, 60);

    // ------------------------------------------------------------------ textures drawn on canvases
    function makeCanvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
    function texture(c) { const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; t.anisotropy = Math.min(8, maxAniso); return t; }
    const BRICKS = ["#f44336", "#ff9800", "#ffeb3b", "#4caf50", "#2196f3"];

    // The screen: the game canvas, plus CRT scanlines and a vignette that fade
    // away as the camera arrives (fx = 1 in the hall, 0 at the end of the zoom).
    const crt = makeCanvas(960, 720), crtCtx = crt.getContext("2d");
    const scan = makeCanvas(1, 3), scanCtx = scan.getContext("2d");
    scanCtx.fillStyle = "rgba(0,0,0,0.32)"; scanCtx.fillRect(0, 2, 1, 1);
    const scanPattern = crtCtx.createPattern(scan, "repeat");
    const vignette = crtCtx.createRadialGradient(480, 360, 200, 480, 360, 640);
    vignette.addColorStop(0, "rgba(0,0,0,0)"); vignette.addColorStop(1, "rgba(0,0,0,0.6)");
    const screenTex = texture(crt);
    function updateScreen(fx) {
      crtCtx.globalAlpha = 1;
      crtCtx.drawImage(sourceCanvas, 0, 0, 960, 720);
      if (fx > 0.01) {
        crtCtx.globalAlpha = fx;
        crtCtx.fillStyle = scanPattern; crtCtx.fillRect(0, 0, 960, 720);
        crtCtx.fillStyle = vignette; crtCtx.fillRect(0, 0, 960, 720);
        crtCtx.globalAlpha = 1;
      }
      screenTex.needsUpdate = true;
    }

    const marquee = makeCanvas(1024, 256), mq = marquee.getContext("2d");
    const marqueeTex = texture(marquee);
    function drawMarquee() {
      const g = mq.createLinearGradient(0, 0, 0, 256);
      g.addColorStop(0, "#22104a"); g.addColorStop(1, "#08061a");
      mq.fillStyle = g; mq.fillRect(0, 0, 1024, 256);
      BRICKS.forEach((c, i) => { mq.fillStyle = c; mq.fillRect(40 + i * 192, 18, 176, 14); mq.fillRect(40 + i * 192, 224, 176, 14); });
      mq.textAlign = "center"; mq.textBaseline = "middle";
      mq.font = "700 40px Silkscreen, 'Courier New', monospace"; mq.fillStyle = "#ffd23f";
      mq.shadowColor = "#ffd23f"; mq.shadowBlur = 16; mq.fillText("ARCADE", 512, 72);
      mq.font = "700 118px Silkscreen, 'Courier New', monospace"; mq.fillStyle = "#eafcff";
      mq.shadowColor = "#33d6ff"; mq.shadowBlur = 34; mq.fillText("BREAKOUT", 512, 150);
      mq.shadowBlur = 0;
      marqueeTex.needsUpdate = true;
    }
    drawMarquee();
    if (document.fonts && document.fonts.load) document.fonts.load("700 118px Silkscreen").then(drawMarquee, () => {});

    const side = makeCanvas(512, 1024), sd = side.getContext("2d");
    (function drawSide() {
      const g = sd.createLinearGradient(0, 0, 512, 1024);
      g.addColorStop(0, "#1a1240"); g.addColorStop(1, "#0a0f2a");
      sd.fillStyle = g; sd.fillRect(0, 0, 512, 1024);
      sd.save(); sd.translate(256, 560); sd.rotate(-0.5);
      BRICKS.forEach((c, i) => { sd.fillStyle = c; sd.fillRect(-500, -150 + i * 64, 1000, 34); });
      sd.restore();
      sd.fillStyle = "#eafcff"; sd.beginPath(); sd.arc(360, 250, 34, 0, Math.PI * 2); sd.fill();
      sd.fillStyle = "#33d6ff"; sd.fillRect(150, 860, 220, 26);
    })();
    const sideTex = texture(side);
    sideTex.wrapS = sideTex.wrapT = THREE.RepeatWrapping;
    sideTex.repeat.set(1 / 0.81, 1 / 1.88); sideTex.offset.set(0.36 / 0.81, 0);

    const door = makeCanvas(256, 320), dr = door.getContext("2d");
    (function drawDoor() {
      const g = dr.createLinearGradient(0, 0, 0, 320);
      g.addColorStop(0, "#2a2f3f"); g.addColorStop(1, "#151926");
      dr.fillStyle = g; dr.fillRect(0, 0, 256, 320);
      dr.strokeStyle = "#454c66"; dr.lineWidth = 6; dr.strokeRect(10, 10, 236, 300);
      for (const x of [70, 150]) {
        dr.fillStyle = "#ff3b2f"; dr.shadowColor = "#ff3b2f"; dr.shadowBlur = 14;
        dr.fillRect(x, 70, 36, 70); dr.shadowBlur = 0;
        dr.fillStyle = "#16080a"; dr.fillRect(x + 15, 82, 6, 46);
      }
      dr.fillStyle = "#ff5a4e"; dr.font = "700 22px Silkscreen, 'Courier New', monospace"; dr.textAlign = "center";
      dr.fillText("INSERT", 128, 195); dr.fillText("COIN", 128, 225);
      dr.fillStyle = "#8c93ad"; dr.font = "16px 'Courier New', monospace"; dr.fillText("1 CREDIT", 128, 272);
    })();
    const doorTex = texture(door);

    const panel = makeCanvas(512, 192), pn = panel.getContext("2d");
    (function drawPanel() {
      pn.fillStyle = "#0d1022"; pn.fillRect(0, 0, 512, 192);
      BRICKS.forEach((c, i) => { pn.fillStyle = c; pn.fillRect(i * 102.4, 180, 102.4, 12); });
      pn.fillStyle = "#7d86a8"; pn.font = "600 15px 'Courier New', monospace"; pn.textAlign = "center";
      pn.fillText("MOVE", 132, 166);
      [["SERVE", 297], ["PAUSE", 353], ["VIEW", 408]].forEach(([t, x]) => pn.fillText(t, x, 166));
    })();
    const panelTex = texture(panel);

    // Floor grid as a mipmapped texture: thin GridHelper lines shimmer when the
    // camera moves; a filtered texture stays smooth.
    const gridCanvas = makeCanvas(256, 256), gc = gridCanvas.getContext("2d");
    gc.fillStyle = "#000"; gc.fillRect(0, 0, 256, 256);
    gc.strokeStyle = "rgba(120, 90, 255, 0.55)"; gc.lineWidth = 2;
    for (const p of [64, 128, 192]) { gc.beginPath(); gc.moveTo(p, 0); gc.lineTo(p, 256); gc.moveTo(0, p); gc.lineTo(256, p); gc.stroke(); }
    gc.strokeStyle = "rgba(255, 45, 149, 0.95)"; gc.lineWidth = 4; gc.strokeRect(0, 0, 256, 256);
    const gridTex = texture(gridCanvas);
    gridTex.wrapS = gridTex.wrapT = THREE.RepeatWrapping; gridTex.repeat.set(20, 20); gridTex.anisotropy = maxAniso;

    function radialTexture(stops) {
      const c = makeCanvas(256, 256), x = c.getContext("2d"), g = x.createRadialGradient(128, 128, 0, 128, 128, 128);
      stops.forEach(([o, col]) => g.addColorStop(o, col));
      x.fillStyle = g; x.fillRect(0, 0, 256, 256);
      return texture(c);
    }

    // ------------------------------------------------------------------ the cabinet
    // Side profile in the z-y plane (z forward, y up), extruded sideways.
    const PROFILE = [[-0.36, 0], [0.34, 0], [0.34, 0.86], [0.45, 0.94], [0.45, 1.0], [0.20, 1.06],
                     [0.12, 1.62], [0.31, 1.68], [0.31, 1.88], [-0.36, 1.88]];
    const sideShape = new THREE.Shape();
    PROFILE.forEach(([z, y], i) => (i ? sideShape.lineTo(z, y) : sideShape.moveTo(z, y)));
    const sideGeo = new THREE.ExtrudeGeometry(sideShape, { depth: 0.04, bevelEnabled: true, bevelThickness: 0.004, bevelSize: 0.004, bevelSegments: 1 });
    sideGeo.rotateY(-Math.PI / 2);                    // shape x -> world z, extrusion -> world -x

    const mats = {
      side: new THREE.MeshStandardMaterial({ map: sideTex, roughness: 0.55, metalness: 0.1 }),
      edge: new THREE.MeshStandardMaterial({ color: 0x141a33, roughness: 0.5 }),
      body: new THREE.MeshStandardMaterial({ color: 0x0f1228, roughness: 0.6, metalness: 0.2 }),
      black: new THREE.MeshStandardMaterial({ color: 0x06070c, roughness: 0.35, metalness: 0.4 }),
      neon: new THREE.MeshBasicMaterial({ color: 0x8fefff }),
      lightBar: new THREE.MeshBasicMaterial({ color: 0xdff8ff }),
      marquee: new THREE.MeshBasicMaterial({ map: marqueeTex }),
      door: new THREE.MeshStandardMaterial({ map: doorTex, emissive: 0xffffff, emissiveMap: doorTex, emissiveIntensity: 0.55, roughness: 0.5, metalness: 0.4 }),
      panelTop: new THREE.MeshStandardMaterial({ map: panelTex, roughness: 0.45, metalness: 0.2 }),
      knob: new THREE.MeshStandardMaterial({ color: 0xe0262b, roughness: 0.25, metalness: 0.1, emissive: 0x400000 }),
      chrome: new THREE.MeshStandardMaterial({ color: 0xcfd5e6, roughness: 0.2, metalness: 0.9 }),
    };
    const screenMat = new THREE.MeshBasicMaterial({ map: screenTex });
    const dimScreenMat = new THREE.MeshBasicMaterial({ map: screenTex, color: 0x6a6a7a });
    const buttonMats = [0xe63333, 0x33cc4d, 0x3380e6].map((c) =>
      new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.25, roughness: 0.3 }));

    function moldingPath(x) {                         // the profile as a closed path for the neon T-molding
      const path = new THREE.CurvePath();
      for (let i = 0; i < PROFILE.length; i++) {
        const [z0, y0] = PROFILE[i], [z1, y1] = PROFILE[(i + 1) % PROFILE.length];
        path.add(new THREE.LineCurve3(new THREE.Vector3(x, y0, z0), new THREE.Vector3(x, y1, z1)));
      }
      return path;
    }
    const moldingGeo = [-1, 1].map((sx) => new THREE.TubeGeometry(moldingPath(sx * 0.39), 260, 0.009, 6, true));
    function box(w, h, d, mat, x, y, z, rx) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
      m.position.set(x, y, z); if (rx) m.rotation.x = rx;
      return m;
    }

    function buildCabinet(screenMaterial) {
      const cab = new THREE.Group();
      [-1, 1].forEach((sx, i) => {
        const panelMesh = new THREE.Mesh(sideGeo, [mats.side, mats.edge]);
        panelMesh.position.x = sx < 0 ? -0.37 : 0.41;
        cab.add(panelMesh, new THREE.Mesh(moldingGeo[i], mats.neon));
      });
      cab.add(box(0.74, 0.86, 0.03, mats.body, 0, 0.43, 0.325));          // lower front
      cab.add(box(0.74, 0.08, 0.02, mats.black, 0, 0.04, 0.345));         // kick plate
      cab.add(box(0.26, 0.32, 0.015, mats.door, 0, 0.46, 0.345));         // coin door
      cab.add(box(0.74, 1.88, 0.02, mats.body, 0, 0.94, -0.35));          // back
      cab.add(box(0.74, 0.02, 0.67, mats.body, 0, 1.87, -0.025));         // top
      cab.add(box(0.74, 0.06, 0.2, mats.body, 0, 1.65, 0.215));           // under the marquee
      cab.add(box(0.70, 0.012, 0.02, mats.lightBar, 0, 1.615, 0.2));      // light bar over the screen
      cab.add(box(0.74, 0.20, 0.06, mats.black, 0, 1.78, 0.28));          // marquee box
      const mqFace = new THREE.Mesh(new THREE.PlaneGeometry(0.72, 0.18), mats.marquee);
      mqFace.position.set(0, 1.78, 0.3105); cab.add(mqFace);
      // Control panel: rises 14 degrees towards the screen.
      const cp = new THREE.Group();
      cp.position.set(0, 1.03, 0.325); cp.rotation.x = rad(14);
      cp.add(new THREE.Mesh(new THREE.BoxGeometry(0.74, 0.025, 0.25),
                            [mats.body, mats.body, mats.panelTop, mats.body, mats.body, mats.body]));
      // Joystick: base -> pivot (leans with the paddle) -> shaft + red knob (Member 2's design).
      const joyBase = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.04, 0.012, 24), mats.black);
      joyBase.position.set(-0.18, 0.018, -0.01); cp.add(joyBase);
      const pivot = new THREE.Group(); pivot.name = "joyPivot"; pivot.position.set(-0.18, 0.024, -0.01); cp.add(pivot);
      const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.007, 0.007, 0.09, 12), mats.chrome);
      shaft.position.y = 0.045; pivot.add(shaft);
      const knob = new THREE.Mesh(new THREE.SphereGeometry(0.026, 24, 16), mats.knob);
      knob.position.y = 0.095; pivot.add(knob);
      buttonMats.forEach((mat, i) => {                // Member 2's button colours
        const b = new THREE.Mesh(new THREE.CylinderGeometry(0.021, 0.021, 0.016, 24), mat);
        b.position.set(0.06 + i * 0.08, 0.02, -0.02); cp.add(b);
      });
      cab.add(cp);
      // Screen: bezel + 4:3 picture, leaning back about 8 degrees.
      const tilt = -Math.atan2(0.08, 0.56);
      cab.add(box(0.74, 0.58, 0.03, mats.black, 0, 1.34, 0.145, tilt));
      const screen = new THREE.Mesh(new THREE.PlaneGeometry(0.60, 0.45), screenMaterial);
      screen.name = "screen"; screen.rotation.x = tilt;
      screen.position.set(0, 1.34, 0.145).add(new THREE.Vector3(0, -Math.sin(tilt), Math.cos(tilt)).multiplyScalar(0.017));
      cab.add(screen);
      return cab;
    }

    // ------------------------------------------------------------------ the hall: three machines + their reflections
    const hall = new THREE.Group();
    const cabinet = buildCabinet(screenMat);
    hall.add(cabinet);
    for (const sx of [-1, 1]) {
      const other = buildCabinet(dimScreenMat);
      other.position.set(sx * 1.3, 0, -0.75); other.rotation.y = -sx * 0.32;
      hall.add(other);
    }
    scene.add(hall);
    const reflection = hall.clone();                 // mirrored under the glossy floor
    reflection.scale.y = -1;
    scene.add(reflection);
    const pivots = [cabinet.getObjectByName("joyPivot"), reflection.children[0].getObjectByName("joyPivot")];

    const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40),
      new THREE.MeshStandardMaterial({ color: 0x0b0918, roughness: 0.25, metalness: 0.5, transparent: true, opacity: 0.86 }));
    floor.rotation.x = -Math.PI / 2; scene.add(floor);
    const grid = new THREE.Mesh(new THREE.PlaneGeometry(40, 40),
      new THREE.MeshBasicMaterial({ map: gridTex, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false }));
    grid.rotation.x = -Math.PI / 2; grid.position.y = 0.003; scene.add(grid);
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 2.6),
      new THREE.MeshBasicMaterial({ map: radialTexture([[0, "rgba(51,214,255,0.55)"], [0.45, "rgba(120,60,255,0.18)"], [1, "rgba(0,0,0,0)"]]),
                                    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    glow.rotation.x = -Math.PI / 2; glow.position.set(0, 0.006, 0.35); scene.add(glow);

    const wall = new THREE.Mesh(new THREE.PlaneGeometry(40, 12), new THREE.MeshStandardMaterial({ color: 0x0a0816, roughness: 0.9 }));
    wall.position.set(0, 6, -3.4); scene.add(wall);
    BRICKS.forEach((c, row) => {                     // a neon brick wall behind the machines
      const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(c).multiplyScalar(0.3) });
      for (let col = 0; col < 10; col++) {
        const brick = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.16, 0.02), mat);
        brick.position.set(-2.75 + col * 0.61, 3.7 - row * 0.23, -3.38); scene.add(brick);
      }
    });

    // A soft beam of light falling on the main cabinet.
    const beamCanvas = makeCanvas(4, 256), bc = beamCanvas.getContext("2d"), bg = bc.createLinearGradient(0, 0, 0, 256);
    bg.addColorStop(0, "rgba(255,255,255,0)"); bg.addColorStop(0.35, "rgba(190,225,255,0.5)"); bg.addColorStop(1, "rgba(190,225,255,0)");
    bc.fillStyle = bg; bc.fillRect(0, 0, 4, 256);
    const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 1.15, 4.4, 48, 1, true),
      new THREE.MeshBasicMaterial({ map: texture(beamCanvas), transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending,
                                    depthWrite: false, side: THREE.DoubleSide }));
    beam.position.set(0, 2.35, 0.2); scene.add(beam);

    const STARS = 260, starPos = new Float32Array(STARS * 3), starSpeed = new Float32Array(STARS);
    for (let i = 0; i < STARS; i++) {
      starPos[i * 3] = (Math.random() - 0.5) * 9; starPos[i * 3 + 1] = Math.random() * 4; starPos[i * 3 + 2] = -3 + Math.random() * 5;
      starSpeed[i] = 0.03 + Math.random() * 0.08;
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
    scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0xaee6ff, size: 0.016, transparent: true, opacity: 0.75,
                                                                     depthWrite: false, blending: THREE.AdditiveBlending })));

    // ------------------------------------------------------------------ lights
    scene.add(new THREE.AmbientLight(0x3a3560, 0.55));
    scene.add(new THREE.HemisphereLight(0x7c6cff, 0x0a0812, 0.4));
    const spot = new THREE.SpotLight(0xffffff, 1.6, 12, 0.45, 0.6, 1.4);
    spot.position.set(0, 4.6, 1.6); spot.target.position.set(0, 1, 0.2); scene.add(spot, spot.target);
    const magenta = new THREE.PointLight(0xff2d95, 2.2, 6, 2); magenta.position.set(-1.7, 1.9, 1.2); scene.add(magenta);
    const cyan = new THREE.PointLight(0x33d6ff, 1.8, 6, 2); cyan.position.set(1.8, 1.2, 1.5); scene.add(cyan);

    // Where the main screen is in the world (for the zoom).
    hall.updateMatrixWorld(true);
    const screenMesh = cabinet.getObjectByName("screen");
    const screenCenter = new THREE.Vector3(), screenNormal = new THREE.Vector3(0, 0, 1);
    screenMesh.getWorldPosition(screenCenter);
    screenNormal.applyQuaternion(screenMesh.getWorldQuaternion(new THREE.Quaternion())).normalize();
    const screenGlow = new THREE.PointLight(0x9fe8ff, 0.9, 2.4, 2);
    screenGlow.position.copy(screenCenter).addScaledVector(screenNormal, 0.35); scene.add(screenGlow);

    // ------------------------------------------------------------------ bloom (optional)
    let composer = null;
    try {
      if (THREE.EffectComposer && THREE.RenderPass && THREE.UnrealBloomPass && THREE.ShaderPass && THREE.GammaCorrectionShader) {
        composer = new THREE.EffectComposer(renderer);
        composer.addPass(new THREE.RenderPass(scene, camera));
        composer.addPass(new THREE.UnrealBloomPass(new THREE.Vector2(512, 512), 0.75, 0.5, 0.42));
        composer.addPass(new THREE.ShaderPass(THREE.GammaCorrectionShader));
      }
    } catch (e) { composer = null; }
    if (!composer) renderer.outputEncoding = THREE.sRGBEncoding;

    // ------------------------------------------------------------------ camera poses and the zoom
    let width = 1, height = 1, clock = 0, tween = null, state = "intro", holdRect = null;
    const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
    container.addEventListener("pointermove", (e) => {
      const r = container.getBoundingClientRect();
      mouse.tx = ((e.clientX - r.left) / r.width - 0.5) * 2; mouse.ty = ((e.clientY - r.top) / r.height - 0.5) * 2;
    });

    function introPose() {
      // Distance so the cabinet (1.9 m tall) fills about 3/4 of the height,
      // or most of the width on a portrait phone. A slow, gentle sway.
      const a = width / height, portrait = a < 0.95;
      const R = portrait ? Math.min(9.5, Math.max(5, 3.9 / a)) : a < 1.45 ? 4.6 : 4.1;
      const ang = 0.5 + (reduced ? 0 : 0.09 * Math.sin(clock * 0.09)) + mouse.x * 0.04;
      return {
        pos: new THREE.Vector3(R * Math.sin(ang), 1.45 - mouse.y * 0.06 + (portrait ? 0.3 : 0), R * Math.cos(ang)),
        target: new THREE.Vector3(0, portrait ? 1.0 : 0.98, 0),
        sx: portrait ? 0 : a < 1.45 ? 0.22 : 0.2, sy: portrait ? 0.31 : 0,
      };
    }
    /* The pose where the 3D screen (0.60 x 0.45 m) covers exactly `rect`, a box in the
       container's CSS pixels: the camera sits on the screen's normal at the distance
       that makes 0.45 m as tall as the box, and a lens shift moves the picture so its
       centre lands on the box's centre. */
    function matchedPose(rect) {
      const t = Math.tan(rad(camera.fov / 2));
      if (!rect || rect.h < 8) {
        const d = Math.max(0.225 / t, 0.3 / (t * (width / height))) / 0.96;
        return { pos: screenCenter.clone().addScaledVector(screenNormal, d), target: screenCenter.clone(), sx: 0, sy: 0 };
      }
      const d = (0.225 / t) * (height / rect.h);
      const dx = rect.x + rect.w / 2 - width / 2, dy = rect.y + rect.h / 2 - height / 2;
      return { pos: screenCenter.clone().addScaledVector(screenNormal, d), target: screenCenter.clone(), sx: dx / width, sy: -dy / height };
    }
    let pose = introPose();
    const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
    function bezier(a, c, b, t) {
      return a.clone().multiplyScalar((1 - t) * (1 - t)).addScaledVector(c, 2 * (1 - t) * t).addScaledVector(b, t * t);
    }
    const arcPoint = () => screenCenter.clone().addScaledVector(screenNormal, 1.7).add(new THREE.Vector3(0, 0.1, 0));

    function zoomIn(getRect, onProgress, onDone) {
      state = "tween";
      tween = { from: pose, to: () => matchedPose(getRect()), dur: reduced ? 0.01 : 2.6, t: 0, onProgress,
                onDone: () => { state = "inside"; holdRect = getRect; onDone(); } };
    }
    function holdAt(getRect) { tween = null; state = "inside"; holdRect = getRect; pose = matchedPose(getRect()); }
    function zoomOut(onDone) {
      state = "tween";
      tween = { from: pose, to: introPose, dur: reduced ? 0.01 : 2.2, t: 0, onDone: () => { state = "intro"; onDone(); } };
    }

    function applyCamera() {
      camera.position.copy(pose.pos);
      camera.lookAt(pose.target);
      camera.setViewOffset(width, height, -pose.sx * width, pose.sy * height, width, height);
    }
    function resize() {
      width = Math.max(1, container.clientWidth); height = Math.max(1, container.clientHeight);
      renderer.setSize(width, height, false);
      if (composer) composer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }
    new ResizeObserver(resize).observe(container);
    resize();

    // ------------------------------------------------------------------ every frame
    function update(dt, game, fx) {
      clock += dt;
      mouse.x += (mouse.tx - mouse.x) * Math.min(1, dt * 2); mouse.y += (mouse.ty - mouse.y) * Math.min(1, dt * 2);
      if (tween) {
        tween.t += dt;
        const p = Math.min(1, tween.t / tween.dur), e = ease(p), to = tween.to();
        pose = { pos: bezier(tween.from.pos, arcPoint(), to.pos, e), target: tween.from.target.clone().lerp(to.target, e),
                 sx: tween.from.sx + (to.sx - tween.from.sx) * e, sy: tween.from.sy + (to.sy - tween.from.sy) * e };
        if (tween.onProgress) tween.onProgress(p);
        if (p >= 1) { const done = tween.onDone; tween = null; done(); }
      } else if (state === "intro") {
        pose = introPose();
      } else if (holdRect) {
        pose = matchedPose(holdRect());
      }
      applyCamera();

      if (game) {                                     // the cabinet plays along with the game
        for (const p of pivots) if (p) p.rotation.z = rad(game.joystickTilt);
        buttonMats.forEach((m, i) => { m.emissiveIntensity = 0.25 + 1.6 * Math.max(0, game.scorePulse - i * 0.12); });
      }
      const pos = starGeo.attributes.position.array;
      for (let i = 0; i < STARS; i++) {
        pos[i * 3 + 1] += starSpeed[i] * dt;
        if (pos[i * 3 + 1] > 4) pos[i * 3 + 1] = 0;
      }
      starGeo.attributes.position.needsUpdate = true;
      mats.neon.color.setHSL(0.52, 1, 0.72 + 0.04 * Math.sin(clock * 1.6));

      updateScreen(fx === undefined ? 1 : fx);
      if (composer) composer.render(); else renderer.render(scene, camera);
    }

    return { update, zoomIn, zoomOut, holdAt, resize };
  }

  root.Arcade = { create };
})(typeof window !== "undefined" ? window : globalThis);
