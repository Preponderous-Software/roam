import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from rendering.displayInfo import getScreenSize


def test_get_screen_size_returns_a_positive_width_height_tuple():
    width, height = getScreenSize()
    assert isinstance(width, int)
    assert isinstance(height, int)
    assert width > 0
    assert height > 0
