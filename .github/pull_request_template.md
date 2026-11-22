## What this PR adds

<!-- One or two sentences. Link the issue: "Closes #<number>" -->

## Checklist (definition of done)

- [ ] I merged `main` into my branch and `python -m unittest` passes (run from `code/`)
- [ ] `python main.py` runs and nothing in the status bar turns red
- [ ] No `glTranslatef` / `glRotatef` / `glScalef` on objects (only `matrices.py` + `glMultMatrixf`)
- [ ] `game.py` has no OpenGL calls; renderers only read the game state
- [ ] Animation uses `dt` (no frame counting, no `sleep`)
- [ ] Code from a tutorial or AI tool has a comment naming the source
- [ ] My report paragraph and screenshot for this feature are written

## Reviewer

Rotation: M1 reviews M2, M2 reviews M3, M3 reviews M4, M4 reviews M1.
Approving means you can explain this code in the Q&A.
