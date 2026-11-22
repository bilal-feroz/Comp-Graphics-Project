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
import os
import sys
import time
import tkinter as tk
import traceback

import OpenGL

# PyOpenGL normally calls glGetError() after EVERY gl call. That doubles the
# cost of immediate-mode drawing, so it is switched off (set True to debug).
# It must be set before any OpenGL module is imported.
OpenGL.ERROR_CHECKING = False

import game as game_module
import persist
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
        now = time.perf_counter()
        try:
            dt = min(now - self.last_time, MAX_DT)
            self.last_time = now
            if not self.paused:
                self.step(dt * self.speed)
            self.show_game_events()
            self.gui.canvas.render_frame()
            self.gui.count_frame()
        except Exception as error:
            self.report_error(error)
        finally:
            # Wait only for what is left of this frame's 16 ms.
            used_ms = (time.perf_counter() - now) * 1000.0
            self.root.after(max(1, int(FRAME_MS - used_ms)), self.tick)

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

    def show_game_events(self):
        """Game messages (ball lost, level up, power-up...) go to the status bar."""
        for text in self.game.pop_events():
            self.gui.show_message(text)

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

    # ------------------------------------------------------------------ actions (buttons + keys)

    def toggle_pause(self):
        """Space / Play-Pause button."""
        self.paused = not self.paused
        self.gui.refresh_controls()

    def reset(self):
        """R / Reset button: new game, fresh scene graphs, time back to 0."""
        name = self.selected.name if self.selected else None
        self.game.reset()
        self.scene2d = render2d.build_scene()
        self.scene3d = render3d.build_scene()
        render2d.sync(self.scene2d, self.game, 0.0)
        render3d.sync(self.scene3d, self.game, 0.0)
        self.elapsed = 0.0
        self.selected = self.current_scene().find(name) if name else None
        self.gui.refresh_selector()
        self.gui.refresh_controls()
        self.gui.show_message("Reset")

    def set_speed(self, value):
        """Speed slider (the GUI has already clamped it to 0.1 .. 3)."""
        self.speed = float(value)

    def set_view(self, view):
        """2D / 3D radio buttons. Keeps the selection if the other view has a
        node with the same name (ball, paddle, bricks, ...)."""
        if view not in ("2D", "3D"):
            raise ValueError("unknown view %r" % view)
        name = self.selected.name if self.selected else None
        self.view = view
        self.selected = self.current_scene().find(name) if name else None
        self.gui.refresh_selector()
        self.gui.refresh_controls()

    def toggle_view(self):
        """V key."""
        self.set_view("3D" if self.view == "2D" else "2D")

    def select(self, node):
        """Object selector or a click on the canvas."""
        self.selected = node
        self.gui.show_selection(node)

    # ------------------------------------------------------------------ save / load (persist.py, Member 3)

    def save_settings(self):
        """Ctrl+S / Save button."""
        path = persist.save_settings(persist.SETTINGS_PATH, persist.collect_settings(self))
        self.gui.show_message("Settings saved to %s" % os.path.basename(path))

    def load_settings(self):
        """Ctrl+O / Load button. A bad file only gives a message (gui.safe)."""
        data = persist.load_settings(persist.SETTINGS_PATH)
        changed = persist.apply_settings(self, data)
        self.gui.refresh_controls()
        self.gui.refresh_tuning()
        self.gui.show_selection(self.selected)
        self.gui.show_message("Settings loaded (%d objects, saved %s)"
                              % (changed, data.get("saved", "?")))

    def save_screenshot(self):
        """P / Screenshot button."""
        path = self.gui.canvas.capture(persist.screenshot_path())
        self.gui.show_message("Screenshot saved: screenshots/%s" % os.path.basename(path))


def main():
    if sys.platform == "win32":
        # Windows timers tick every 15.6 ms by default, so after(16) really
        # waits about 31 ms (30 FPS). Ask Windows for 1 ms timers while we run.
        import ctypes
        ctypes.windll.winmm.timeBeginPeriod(1)
    root = tk.Tk()
    root.title("Arcade Breakout - OpenGL Animated World")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
