import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from unittest.mock import MagicMock

import pytest

from rendering.pygameFrontend import PygameFrontend, createFrontend
from rendering.renderer import Renderer


def _config(width=800, height=600, fullscreen=False):
    config = MagicMock()
    config.displayWidth = width
    config.displayHeight = height
    config.fullscreen = fullscreen
    return config


@pytest.fixture
def frontend():
    f = createFrontend(_config())
    yield f
    f.quit()


def test_create_frontend_returns_a_renderer_over_the_configured_display(frontend):
    renderer = frontend.getRenderer()
    assert isinstance(renderer, Renderer)
    assert renderer.getDisplaySize() == (800, 600)


def test_renderer_and_graphik_share_the_same_surface(frontend):
    assert frontend.getRenderer().graphik is frontend.getGraphik()


def test_reset_rebuilds_the_renderer_for_a_new_session(frontend):
    first = frontend.getRenderer()
    frontend.reset()
    second = frontend.getRenderer()
    assert second is not first
    assert second.getDisplaySize() == (800, 600)


def test_set_caption_does_not_raise(frontend):
    frontend.setCaption("Roam (smoke)")


def test_fullscreen_branch_builds_a_renderer():
    # Exercises the fullscreen branch of display creation. The dummy SDL driver
    # substitutes its own resolution for a fullscreen surface, so only the fact
    # that a usable renderer is produced is meaningful headless.
    f = PygameFrontend(_config(fullscreen=True))
    try:
        width, height = f.getRenderer().getDisplaySize()
        assert width > 0 and height > 0
    finally:
        f.quit()
