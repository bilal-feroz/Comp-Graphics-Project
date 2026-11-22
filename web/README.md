# Web showcase: the 3D arcade intro

> **Presentation extra, made for the wow factor.**
> This folder is **not part of the graded project** and is not in the submission zip.
> The graded program is the Python + PyOpenGL + Tkinter code in [`code/`](../code).

Live site: **https://arcade-breakout-two.vercel.app** (deployed on Vercel).

## What it is

1. **Intro.** A 3D arcade hall built with three.js. It shows the project name, the
   course and the four team members, and has a START button.
2. **START.** A coin sound plays, the camera flies into the main cabinet's screen and
   the CRT "powers on".
3. **Play.** The same Breakout game runs in 2D and 3D. Esc (or "Back to the arcade")
   zooms back out.

The cabinet's screen shows the live game. Its joystick leans with the paddle, and its
red, green and blue buttons (Member 2's design) light up when points are scored.

## Everyone's work is unchanged

`engine.js` is a line-by-line JavaScript port of the team's Python program, so the
game in the browser behaves the same way:

| Python (graded) | Browser port in `engine.js` | Member |
|---|---|---|
| `matrices.py`, `scene.py` | own 3x3 / 4x4 matrices, `Node`, world = parent world . local | 1 |
| `figures.py` (2D), `render2d.py` | the same figures and scene; letterboxed 2D drawing | 2 |
| `game.py`, `anim2d.py` | the same rules, constants, collisions, UFO path, power-ups, demo AI, 2D animation | 3 |
| `figures.py` (3D), `render3d.py` | bevelled bricks, turned trophy, octahedron star, orbit camera, lighting from face normals | 4 |

The port was checked against the Python code: `fold_between`, `ufo_path`,
`circle_rect_contact` and the scene graph's world matrices give the same numbers.
Ten simulated minutes of demo mode ran with no errors and reached level 5.

The only differences are in how things are drawn. A web canvas replaces OpenGL, so the
3D view does its own perspective projection, back-face culling, flat lighting and
depth sort. The score bar replaces the Tkinter status bar.

## Files

| File | What it does |
|---|---|
| `index.html` | the page: intro, game layer, notes about the project |
| `arcade.js` | the three.js arcade hall, cabinet, lights, bloom and the camera zoom |
| `engine.js` | the game (port of the Python modules, see above) |
| `app.js` | START / zoom / back, keyboard, mouse and touch controls, score bar |
| `assets/` | recording and screenshots of the real Python program |

three.js r128 and its bloom post-processing load from a CDN. There is no build step.

## Run it locally

```
cd web
python -m http.server 8000
```

Then open http://localhost:8000.
