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
