"""
gui.py - the window: OpenGL canvas, control panel, status bar and input.  [Member 1]

    +--------------------------------+------------------------+
    |                                | Simulation             |
    |                                | Selected object        |
    |        OpenGL canvas           | [Game tuning|Camera]   |
    |        (2D or 3D view)         |   (two tabs)           |
    |                                | World matrix           |
    +--------------------------------+------------------------+
    | help line (always visible)                              |
    | status bar:  time | FPS | view | selected | messages     |
    +---------------------------------------------------------+

How the GUI talks to the rest of the program:
  * widgets only call App methods (main.py) or change a Node / Game value;
    they never draw anything themselves,
  * the canvas asks App.draw() for a new picture every frame,
  * the status bar and matrix panel are refreshed 5 times a second.

"The program never crashes":
  * sliders cannot leave their range and typed values are clamped to it,
  * entry boxes refuse letters while you type (validatecommand),
  * every callback goes through safe(): an exception becomes a red message
    in the status bar instead of a crash.
"""
import math
import re
import tkinter as tk
from tkinter import colorchooser
from tkinter import ttk

from OpenGL.GL import glClearColor
from pyopengltk import OpenGLFrame
MESSAGE_SHOW_MS = 6000


# ======================================================================= input helpers
# Plain functions without widgets, so test_graphics.py can test them.

_PARTIAL_NUMBER = re.compile(r"^-?\d*\.?\d*$")


def is_partial_number(text):
    """True while the text can still become a number: '', '-', '1.', '-0.5'.
    Used as the entry boxes' validatecommand, so a letter is refused the
    moment it is typed."""
    return bool(_PARTIAL_NUMBER.match(text))


def clamp(value, low, high):
    """Keep value inside [low, high]."""
    return max(low, min(high, value))


def parse_number(text, low, high):
    """Entry text -> float inside [low, high]. Raises ValueError for text that
    is not a finite number (for example '' or '-')."""
    try:
        value = float(text)
    except ValueError:
        raise ValueError("'%s' is not a number" % text) from None
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("'%s' is not a finite number" % text)
    return clamp(value, low, high)


def wrap_degrees(angle):
    """Any angle -> the same direction in (-180, 180], for the rotation slider."""
    angle = math.fmod(angle, 360.0)
    if angle > 180.0:
        angle -= 360.0
    elif angle <= -180.0:
        angle += 360.0
    return angle


def color_to_hex(color):
    """(r, g, b) with floats 0..1 -> '#rrggbb' for Tk widgets."""
    r, g, b = (int(round(clamp(c, 0.0, 1.0) * 255)) for c in color)
    return "#%02x%02x%02x" % (r, g, b)


# ======================================================================= widgets

class GLCanvas(OpenGLFrame):
    """The OpenGL drawing area: pyopengltk puts an OpenGL context inside a
    Tk frame. Double buffering: we draw into the hidden back buffer and
    tkSwapBuffers() shows the finished picture in one go, so it never flickers."""

    def __init__(self, parent, app, **options):
        super().__init__(parent, **options)
        self.app = app

    def initgl(self):
        """Called by pyopengltk when the window appears (and on resize)."""
        glClearColor(0.02, 0.02, 0.06, 1.0)

    def redraw(self):
        """Called by pyopengltk; the App decides which view to draw."""
        self.app.draw(max(1, self.winfo_width()), max(1, self.winfo_height()))

    def render_frame(self):
        """Draw one frame now (App.tick calls this every frame)."""
        if not self.context_created:      # window not on screen yet
            return
        self.tkMakeCurrent()
        self.redraw()
        self.tkSwapBuffers()


class SliderRow:
    """One numeric control: label + slider + entry box that always agree.

    on_change(value) receives a float that is already inside [low, high].
    on_error(error) is called when the typed text is not a number.
    """

    def __init__(self, parent, row, text, low, high, value, on_change, on_error, digits=2):
        self.low, self.high = float(low), float(high)
        self.on_change = on_change
        self.on_error = on_error
        self.digits = digits
        self.var = tk.DoubleVar(value=clamp(float(value), self.low, self.high))

        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=1)
        self.scale = ttk.Scale(parent, from_=self.low, to=self.high, variable=self.var,
                               command=self._slider_moved, takefocus=False)
        self.scale.grid(row=row, column=1, sticky="ew", padx=4)
        only_numbers = (parent.register(is_partial_number), "%P")
        self.entry = ttk.Entry(parent, width=7, validate="key", validatecommand=only_numbers)
        self.entry.grid(row=row, column=2, sticky="e")
        self.entry.bind("<Return>", self._typed)
        self.entry.bind("<FocusOut>", self._typed)
        self._show(self.var.get())

    def get(self):
        return clamp(self.var.get(), self.low, self.high)

    def set(self, value):
        """Move the slider from code. Does NOT call on_change."""
        value = clamp(float(value), self.low, self.high)
        self.var.set(value)
        self._show(value)

    def set_enabled(self, enabled):
        flag = ["!disabled"] if enabled else ["disabled"]
        self.scale.state(flag)
        self.entry.state(flag)

    def _show(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, "%.*f" % (self.digits, value))

    def _slider_moved(self, _text):
        value = self.get()
        self._show(value)
        self._notify(value)

    def _typed(self, _event=None):
        try:
            value = parse_number(self.entry.get(), self.low, self.high)
        except ValueError as error:
            self.on_error(error)
            self._show(self.get())        # put the last good value back
            return
        self.set(value)
        self._notify(value)

    def _notify(self, value):
        try:
            self.on_change(value)
        except Exception as error:       # never let a callback crash the GUI
            self.on_error(error)


# ======================================================================= main window

class MainWindow:
    """Builds every widget and turns keyboard and mouse input into App calls."""

    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.selector_nodes = []          # node for each line of the dropdown
        self.message_job = None
        self.camera = None                # CameraControls, created with the camera tab
        # Fit the window on the screen (lab PCs and laptops differ).
        width = min(1280, root.winfo_screenwidth() - 60)
        height = min(800, root.winfo_screenheight() - 110)
        root.geometry("%dx%d+20+10" % (width, height))
        root.minsize(800, 560)
        root.report_callback_exception = self._tk_error    # last safety net
        self._build_layout()
        self._build_simulation_section()
        self._build_selection_section()
        self.refresh_selector()

    # ------------------------------------------------------------------ layout

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.canvas = GLCanvas(self.root, self.app, width=800, height=600)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.panel = ttk.Frame(self.root, padding=(8, 6))
        self.panel.grid(row=0, column=1, sticky="ns")

        status = ttk.Frame(self.root, relief="sunken", padding=(4, 1))
        status.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_message = ttk.Label(status, anchor="w")
        self.status_message.pack(side="left", fill="x", expand=True)

    def _section(self, title):
        """A titled box in the control panel; column 1 (the sliders) stretches."""
        box = ttk.LabelFrame(self.panel, text=title, padding=(6, 4))
        box.pack(fill="x", pady=(0, 6))
        box.columnconfigure(1, weight=1)
        return box

    def _build_simulation_section(self):
        box = self._section("Simulation")
        buttons = ttk.Frame(box)
        buttons.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        self.pause_button = ttk.Button(buttons, text="Pause", width=10, takefocus=False,
                                       command=self.safe(self.app.toggle_pause))
        self.pause_button.pack(side="left")
        ttk.Button(buttons, text="Reset", width=10, takefocus=False,
                   command=self.safe(self.app.reset)).pack(side="left", padx=6)
        self.speed = SliderRow(box, 1, "Speed (x)", 0.1, 3.0, self.app.speed,
                               self.app.set_speed, self.app.report_error)

        ttk.Label(box, text="View").grid(row=2, column=0, sticky="w")
        self.view_var = tk.StringVar(value=self.app.view)
        views = ttk.Frame(box)
        views.grid(row=2, column=1, columnspan=2, sticky="w")
        for name in ("2D", "3D"):
            ttk.Radiobutton(views, text=name, value=name, variable=self.view_var, takefocus=False,
                            command=self.safe(lambda: self.app.set_view(self.view_var.get()))
                            ).pack(side="left", padx=(0, 12))

    def _build_selection_section(self):
        box = self._section("Selected object")
        ttk.Label(box, text="Object").grid(row=0, column=0, sticky="w")
        self.selector = ttk.Combobox(box, state="readonly", width=26, height=20)
        self.selector.grid(row=0, column=1, columnspan=2, sticky="ew", pady=(0, 4))
        self.selector.bind("<<ComboboxSelected>>", self.safe(self._selector_changed))
        self.size = SliderRow(box, 1, "Size (scale)", 0.1, 3.0, 1.0,
                              self._size_changed, self.app.report_error)
        self.rotation = SliderRow(box, 2, "Rotation (deg)", -180, 180, 0,
                                  self._rotation_changed, self.app.report_error, digits=0)
        row = ttk.Frame(box)
        row.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        ttk.Label(row, text="Colour").pack(side="left")
        self.swatch = tk.Label(row, width=4, relief="solid", bd=1)
        self.swatch.pack(side="left", padx=6)
        self.colour_button = ttk.Button(row, text="Pick colour...", takefocus=False,
                                        command=self.safe(self._pick_colour))
        self.colour_button.pack(side="left")
        self.visible_var = tk.BooleanVar(value=True)
        self.visible_check = ttk.Checkbutton(row, text="Visible", variable=self.visible_var,
                                             takefocus=False,
                                             command=self.safe(self._visible_changed))
        self.visible_check.pack(side="right")

    # ------------------------------------------------------------------ App -> GUI

    def refresh_controls(self):
        """Make the widgets show the App state (after a key press, reset, ...)."""
        self.pause_button.config(text="Play" if self.app.paused else "Pause")
        self.speed.set(self.app.speed)
        self.view_var.set(self.app.view)

    def refresh_selector(self):
        """Fill the dropdown from scene.all_nodes() of the current view.
        Children are indented under their parent, so the list shows the tree."""
        self.selector_nodes = self.app.current_scene().all_nodes()
        self.selector["values"] = ["   " * node.depth() + node.name for node in self.selector_nodes]
        self.show_selection(self.app.selected)

    def show_selection(self, node):
        """Load the selected node into the controls (App.select calls this)."""
        if node in self.selector_nodes:
            self.selector.current(self.selector_nodes.index(node))
        else:
            self.selector.set("")
        enabled = node is not None
        for slider in (self.size, self.rotation):
            slider.set_enabled(enabled)
        for widget in (self.colour_button, self.visible_check):
            widget.state(["!disabled"] if enabled else ["disabled"])
        if node is None:
            self.swatch.config(bg=self.root.cget("bg"))
            return
        self.size.set(node.sx)
        self.rotation.set(wrap_degrees(node.angle if node.dim == 2 else node.ry))
        self.swatch.config(bg=color_to_hex(node.color))
        self.visible_var.set(node.visible)

    def count_frame(self):
        """App.tick calls this once per drawn frame (for the FPS counter)."""

    def show_message(self, text, error=False):
        """Show a message in the status bar for a few seconds (errors in red)."""
        self.status_message.config(text=("Error: " if error else "") + str(text),
                                   foreground="#c62828" if error else "#1b5e20")
        if self.message_job is not None:
            self.root.after_cancel(self.message_job)
        self.message_job = self.root.after(MESSAGE_SHOW_MS,
                                           lambda: self.status_message.config(text=""))

    # ------------------------------------------------------------------ safety

    def safe(self, callback):
        """Wrap a callback: an exception goes to the status bar, the program
        keeps running."""
        def wrapped(*args):
            try:
                return callback(*args)
            except Exception as error:
                self.app.report_error(error)
        return wrapped

    def _tk_error(self, exc_type, error, traceback_):
        """Tk calls this for any callback error we did not catch ourselves."""
        self.app.report_error(error)

    # ------------------------------------------------------------------ selected object

    def _selector_changed(self, _event=None):
        index = self.selector.current()
        if 0 <= index < len(self.selector_nodes):
            self.app.select(self.selector_nodes[index])
        self.selector.selection_clear()
        self.canvas.focus_set()           # so the keyboard shortcuts work again

    def _size_changed(self, value):
        node = self.app.selected
        if node is not None:
            node.sx = node.sy = value
            if node.dim == 3:
                node.sz = value

    def _rotation_changed(self, value):
        node = self.app.selected
        if node is None:
            return
        if node.dim == 2:
            node.angle = value
        else:
            node.ry = value

    def _pick_colour(self):
        node = self.app.selected
        if node is None:
            raise ValueError("select an object first")
        rgb, hex_code = colorchooser.askcolor(color=color_to_hex(node.color), parent=self.root,
                                              title="Colour of " + node.name)
        if rgb is None:                   # dialog cancelled
            return
        colour = tuple(int(c) / 255.0 for c in rgb)
        # A group node has no figure of its own, so colour its whole subtree.
        targets = node.all_nodes() if node.figure is None else [node]
        for target in targets:
            target.color = colour
        self.swatch.config(bg=hex_code)
        self.canvas.focus_set()

    def _visible_changed(self):
        if self.app.selected is not None:
            self.app.selected.visible = self.visible_var.get()
