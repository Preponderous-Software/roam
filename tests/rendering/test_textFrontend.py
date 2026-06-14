from unittest.mock import MagicMock

from rendering.clock import Clock
from rendering.inputSource import InputSource
from rendering.renderer import Renderer
from rendering.textClock import TextClock
from rendering.textFrontend import TextFrontend, createTextFrontend


def test_frontend_builds_the_three_interface_implementations():
    frontend = createTextFrontend(MagicMock())
    assert isinstance(frontend, TextFrontend)
    assert isinstance(frontend.getRenderer(), Renderer)
    assert isinstance(frontend.getInputSource(), InputSource)
    assert isinstance(frontend.getClock(), Clock)


def test_reset_rebuilds_the_renderer():
    frontend = createTextFrontend(MagicMock())
    first = frontend.getRenderer()
    frontend.reset()
    assert frontend.getRenderer() is not first


def test_set_caption_is_accepted_and_quit_is_a_noop():
    frontend = createTextFrontend(MagicMock())
    frontend.setCaption("Roam (save1)")
    frontend.quit()  # must not raise


def test_text_clock_tick_returns_nonnegative_milliseconds():
    clock = TextClock()
    assert clock.tick(1000) >= 0
    assert clock.tick(0) == 0
