ARCADE BREAKOUT - OpenGL Animated World
Introduction to Computer Graphics (0102460) - Course Project

Breakout inside an arcade cabinet: a playable 2D Breakout scene, the same game
drawn in 3D with a spinning trophy, and a Tkinter control panel.


REQUIREMENTS
------------
Python 3.11 (tested on Windows with 3.11.9; any Python 3.8+ should work)

Libraries (all from PyPI):
    PyOpenGL     OpenGL calls from Python
    pyopengltk   an OpenGL canvas inside a Tkinter window
    numpy        used by PyOpenGL for arrays
    Pillow       screenshots (optional feature)

Install them once:
    pip install -r requirements.txt


RUN
---
    cd code
    python main.py


TESTS
-----
    cd code
    python -m unittest -v


CONTROLS
--------
Keyboard
    Space        pause / play
    R            reset the game and the scene
    V            switch between the 2D and 3D view
    Left, Right  move the paddle
    M            attract mode (the paddle plays by itself)
    H            open / close the help window
    (A help line with these keys is always shown under the picture.)

Mouse
    2D view      click an object to select it
    3D view      drag to orbit the camera, mouse wheel to zoom

Control panel (right side)
    Play / Pause, Reset      same as Space and R
    Speed (x)                animation speed from 0.1x to 3x
    View 2D / 3D             same as V
    Object                   choose any node of the scene graph; children are
                             indented under their parent
    Size (scale)             scales the selected object and its children
    Rotation (deg)           rotates the selected object and its children
    Colour                   colour picker for the selected object
                             (a group node colours its whole group)
    Visible                  hide / show the selected object and its children
    Game tuning tab          ball speed, UFO orbit speed, paddle width
    Camera (3D view) tab     yaw, pitch and distance of the 3D camera
    World matrix panel       local and world matrix of the selected object,
                             refreshed 5 times a second

Status bar (bottom): animation time, frames per second, view, selected object,
and messages. Wrong input never crashes the program: sliders stay in range,
entry boxes refuse letters, typed numbers are clamped, and any error is shown
in red in the status bar.


FILES (code/)
-------------
    main.py           program start, animation loop (after + dt)       Member 1
    matrices.py       our own 3x3 and 4x4 matrix functions              Member 1
    scene.py          Node class and scene graph                        Member 1
    gui.py            window, control panel, status bar, input          Member 1
    test_graphics.py  unit tests (python -m unittest)                   Member 1 + all
    figures.py        2D figures (Member 2), 3D figures (Member 4)
    raster.py         Bresenham, midpoint circle, scan-line fill        Member 2
    render2d.py       draws the 2D scene                                Member 2
    game.py           game state, update(dt), collisions, score         Member 3
    persist.py        JSON save / load, screenshot (optional)           Member 3
    render3d.py       3D drawing, lights, camera                        Member 4

More detail: docs/HOW_IT_WORKS.md (architecture, scene graph, frame loop).
