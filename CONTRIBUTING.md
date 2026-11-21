# Team workflow

`main` is protected: everything reaches it through a reviewed pull request.

## Setup (once)

```
git clone https://github.com/bilal-feroz/Comp-Graphics-Project.git
cd Comp-Graphics-Project
pip install -r requirements.txt
cd code
python main.py
```

## Every feature

1. Branch from an up-to-date `main`, named `<member>-<feature>`:
   `m2-raster`, `m3-collisions`, `m4-camera`, `m1-gui-panel`.
2. Commit every working session, with small commits and clear messages.
3. Before the pull request: `git merge main`, then run `python -m unittest` from `code/`.
4. Open the pull request and fill in the checklist. GitHub Actions runs the tests too.
5. Review rotation: **M1 reviews M2, M2 reviews M3, M3 reviews M4, M4 reviews M1.**
   Approving means you can explain that code in the Q&A.

## Rules for all code

* No `glTranslatef`, `glRotatef` or `glScalef` on objects. Use `matrices.py` and
  `glMultMatrixf`. OpenGL matrix calls are only for the camera and projection.
* `game.py` holds the game state in world units and never calls OpenGL.
  `render2d.py` and `render3d.py` only read it.
* Animation uses `dt` (seconds since the last frame) times the speed slider.
  No frame counting, no `sleep`, no busy-wait loops.
* Keep the function names in the interfaces (`build_scene`, `sync`, `draw`, `pick`,
  `on_drag`, `on_wheel`). `main.py` and `gui.py` call them.
* Code taken from a tutorial or an AI tool gets a comment naming the source, plus a
  line in the report.

## Coordinates

* 2D world: x from -10 to 10, y from -7.5 to 7.5 (4:3), origin at the centre of the field.
* 3D world: same x and y, z pointing towards the camera.
* Every figure is defined in its own model coordinates, centred on the origin, and
  placed only through its node's transform.

## Definition of done

1. Merged to `main` through a reviewed pull request.
2. Tests pass with `python -m unittest`.
3. Runs on a lab machine, not only on your laptop.
4. Your reviewer can explain it without you in the room.
5. Its report paragraph and screenshot are written.
