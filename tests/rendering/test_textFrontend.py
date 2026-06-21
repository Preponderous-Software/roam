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


# --- second batch ---


def test_set_caption_emits_osc_title_sequence_when_terminal_active(monkeypatch):
    import io

    frontend = createTextFrontend(MagicMock())
    frontend._terminalState = object()  # non-None → OSC branch executes
    buf = io.StringIO()
    monkeypatch.setattr("sys.stdout", buf)
    frontend.setCaption("MyGame")
    assert "\033]2;MyGame\007" in buf.getvalue()


def test_resize_updates_renderer_to_new_dimensions():
    frontend = createTextFrontend(MagicMock())
    r = frontend.getRenderer()
    r.resize(40, 20)
    assert r.getDisplayWidth() == 40 * 8
    assert r.getDisplayHeight() == 20 * 16


def test_text_clock_zero_fps_returns_zero():
    assert TextClock().tick(0) == 0


def test_frontend_set_caption_does_not_raise_without_terminal():
    # In the test environment _terminalState is None — setCaption must be a no-op.
    frontend = createTextFrontend(MagicMock())
    frontend.setCaption("Test")


# --- third batch ---


def test_frontend_renderer_is_a_text_renderer():
    from rendering.textRenderer import TextRenderer

    frontend = createTextFrontend(MagicMock())
    assert isinstance(frontend.getRenderer(), TextRenderer)


def test_frontend_input_source_is_text_input_source():
    from rendering.textInputSource import TextInputSource

    frontend = createTextFrontend(MagicMock())
    assert isinstance(frontend.getInputSource(), TextInputSource)
