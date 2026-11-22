"""
persist.py - save / load settings and screenshots (optional).             [Member 3]

SKELETON by Member 1 (lead). Optional creativity marks:
  * save_settings / load_settings: speed, colours, sizes and camera as JSON
  * save_screenshot: glReadPixels -> Pillow image -> PNG
"""


def save_settings(path, settings):
    """Write the settings dictionary to `path` as JSON."""
    raise NotImplementedError("TODO(M3): JSON save")


def load_settings(path):
    """Read a settings dictionary back from `path`."""
    raise NotImplementedError("TODO(M3): JSON load")


def save_screenshot(path, width, height):
    """Save the current OpenGL frame as a PNG."""
    raise NotImplementedError("TODO(M3): glReadPixels + Pillow")
