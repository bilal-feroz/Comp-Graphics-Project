"""
main.py - program entry point and the animation loop.                     [Member 1]

Run from the code/ folder:      python main.py

One frame (Tk calls tick() again about every 16 ms with after()):
  1. dt = seconds since the last frame, measured with time.perf_counter()
  2. if not paused:  step = dt x speed slider
        game.update(step)                     the game numbers change     (game.py)
        render2d.sync / render3d.sync         numbers copied onto nodes   (scene graph)
  3. canvas.render_frame()                    draw the active view, swap buffers
There is no sleep() and no busy-wait loop: the Tk event loop stays free for
the mouse and keyboard between frames.
"""
import time
import tkinter as tk
import traceback

import game as game_module
import render2d
import render3d
from gui import MainWindow

FRAME_MS = 16        # ask for a new frame every 16 ms (about 60 per second)
MAX_DT = 0.1         # if the window froze (e.g. while dragged), do not jump ahead


class App:
    """The state every part of the program shares: the game, the two scene
    graphs, pause / speed / view, and the selected node."""

    def __init__(self, root):
        self.root = root
        self.game = game_module.Game()
        self.scene2d = render2d.build_scene()
        self.scene3d = render3d.build_scene()
        self.view = "2D"              # "2D" or "3D"
        self.paused = False
        self.speed = 1.0              # speed slider, 0.1 .. 3
        self.elapsed = 0.0            # animation time in seconds (scaled by speed)
        self.selected = None          # the Node chosen in the GUI
        self.gui = None
        self._last_error = None
        self.gui = MainWindow(root, self)
        self.last_time = time.perf_counter()
        self.tick()

    # ------------------------------------------------------------------ animation loop

    def tick(self):
        """One frame. Always schedules the next one, even after an error."""
        try:
            now = time.perf_counter()
            dt = min(now - self.last_time, MAX_DT)
            self.last_time = now
            if not self.paused:
                self.step(dt * self.speed)
            self.gui.canvas.render_frame()
            self.gui.count_frame()
        except Exception as error:
            self.report_error(error)
        finally:
            self.root.after(FRAME_MS, self.tick)

    def step(self, dt):
        """Move the world forward by dt (already scaled by the speed slider)."""
        self.elapsed += dt
        self.game.update(dt)
        render2d.sync(self.scene2d, self.game, dt)
        render3d.sync(self.scene3d, self.game, dt)

    def draw(self, width, height):
        """Called by the canvas: draw the active view."""
        if self.view == "2D":
            render2d.draw(self.scene2d, width, height, self.selected)
        else:
            render3d.draw(self.scene3d, width, height, self.gui.camera, self.selected)

    def current_scene(self):
        """Root node of the scene graph that is on screen."""
        return self.scene2d if self.view == "2D" else self.scene3d

    def report_error(self, error):
        """Show an error in the status bar; print the full traceback once."""
        message = str(error) or error.__class__.__name__
        if message != self._last_error:   # not 60 times a second
            traceback.print_exception(type(error), error, error.__traceback__)
            self._last_error = message
        if self.gui is not None:
            self.gui.show_message(message, error=True)


def main():
    root = tk.Tk()
    root.title("Arcade Breakout - OpenGL Animated World")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
