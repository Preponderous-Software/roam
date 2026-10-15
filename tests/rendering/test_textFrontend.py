import io
import os
import signal
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import rendering.textFrontend as textFrontendModule
from rendering.clock import Clock
from rendering.inputEvent import EventType
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


# --- terminal lifecycle ---


class _FakeTtyStdin:
    def isatty(self):
        return True

    def fileno(self):
        return 7


class _FailingStdout:
    def write(self, text):
        raise OSError("terminal gone")

    def flush(self):
        raise OSError("terminal gone")


def _fakeTermiosModule(savedState="saved-attrs"):
    termios = MagicMock()
    termios.TCSADRAIN = 1
    termios.tcgetattr.return_value = savedState
    return termios


def _enterFakeTerminal(monkeypatch, termios, tty, stdout):
    monkeypatch.setitem(sys.modules, "termios", termios)
    monkeypatch.setitem(sys.modules, "tty", tty)
    monkeypatch.setattr("sys.stdin", _FakeTtyStdin())
    monkeypatch.setattr("sys.stdout", stdout)


def _patchTerminalSize(monkeypatch, getTerminalSize):
    # Patch only the module's own `os` reference: replacing the real
    # os.get_terminal_size also breaks pytest's progress output.
    monkeypatch.setattr(
        textFrontendModule, "os", SimpleNamespace(get_terminal_size=getTerminalSize)
    )


def _ensureSigwinch(monkeypatch):
    # SIGWINCH does not exist on Windows; give it a value so the
    # registration path runs on every platform.
    monkeypatch.setattr(signal, "SIGWINCH", 28, raising=False)


def test_renderer_is_sized_from_the_terminal(monkeypatch):
    _patchTerminalSize(monkeypatch, lambda: os.terminal_size((100, 30)))
    renderer = createTextFrontend(MagicMock()).getRenderer()
    assert renderer.columns == 100
    assert renderer.rows == 30


def test_zero_terminal_size_falls_back_to_80_by_24(monkeypatch):
    _patchTerminalSize(monkeypatch, lambda: os.terminal_size((0, 0)))
    renderer = createTextFrontend(MagicMock()).getRenderer()
    assert renderer.columns == 80
    assert renderer.rows == 24


def test_unavailable_terminal_size_falls_back_to_80_by_24(monkeypatch):
    def raiseOSError():
        raise OSError("not a terminal")

    _patchTerminalSize(monkeypatch, raiseOSError)
    renderer = createTextFrontend(MagicMock()).getRenderer()
    assert renderer.columns == 80
    assert renderer.rows == 24


def test_resize_handler_is_registered_for_sigwinch(monkeypatch):
    _ensureSigwinch(monkeypatch)
    registered = {}
    monkeypatch.setattr(
        signal, "signal", lambda signum, handler: registered.update({signum: handler})
    )
    frontend = createTextFrontend(MagicMock())
    assert registered[signal.SIGWINCH] == frontend._onResize


def test_resize_handler_registration_failure_is_swallowed(monkeypatch):
    _ensureSigwinch(monkeypatch)

    def raiseValueError(signum, handler):
        raise ValueError("signal only works in main thread")

    monkeypatch.setattr(signal, "signal", raiseValueError)
    frontend = createTextFrontend(MagicMock())  # must not raise
    assert isinstance(frontend.getRenderer(), Renderer)


def test_on_resize_resizes_renderer_and_queues_window_resize_event(monkeypatch):
    frontend = createTextFrontend(MagicMock())
    _patchTerminalSize(monkeypatch, lambda: os.terminal_size((60, 18)))
    frontend._onResize(None, None)

    renderer = frontend.getRenderer()
    assert renderer.columns == 60
    assert renderer.rows == 18
    inputSource = frontend.getInputSource()
    inputSource._charReader = lambda: ""
    events = inputSource.pollEvents()
    assert [event.type for event in events] == [EventType.WINDOW_RESIZE]


def test_non_tty_stdin_leaves_terminal_untouched(monkeypatch):
    termios = _fakeTermiosModule()
    tty = MagicMock()
    monkeypatch.setitem(sys.modules, "termios", termios)
    monkeypatch.setitem(sys.modules, "tty", tty)
    frontend = createTextFrontend(MagicMock())
    assert frontend._terminalState is None
    termios.tcgetattr.assert_not_called()
    tty.setcbreak.assert_not_called()


def test_tty_stdin_enters_cbreak_mode_and_alternate_screen(monkeypatch):
    termios = _fakeTermiosModule()
    tty = MagicMock()
    buf = io.StringIO()
    _enterFakeTerminal(monkeypatch, termios, tty, buf)

    frontend = createTextFrontend(MagicMock())

    assert frontend._terminalState == "saved-attrs"
    tty.setcbreak.assert_called_once_with(7)
    assert buf.getvalue() == "\033[?1049h\033[?25l\033]2;Roam\007"


def test_cbreak_setup_failure_leaves_terminal_state_unset(monkeypatch):
    termios = _fakeTermiosModule()
    termios.tcgetattr.side_effect = OSError("inappropriate ioctl")
    tty = MagicMock()
    _enterFakeTerminal(monkeypatch, termios, tty, io.StringIO())

    frontend = createTextFrontend(MagicMock())

    assert frontend._terminalState is None
    tty.setcbreak.assert_not_called()


def test_quit_restores_screen_then_terminal_attributes(monkeypatch):
    termios = _fakeTermiosModule()
    tty = MagicMock()
    buf = io.StringIO()
    _enterFakeTerminal(monkeypatch, termios, tty, buf)
    frontend = createTextFrontend(MagicMock())
    stdin = sys.stdin

    frontend.quit()

    assert buf.getvalue().endswith("\033[?25h\033[?1049l")
    termios.tcsetattr.assert_called_once_with(stdin, 1, "saved-attrs")
    assert frontend._terminalState is None


def test_second_quit_does_not_restore_terminal_again(monkeypatch):
    termios = _fakeTermiosModule()
    _enterFakeTerminal(monkeypatch, termios, MagicMock(), io.StringIO())
    frontend = createTextFrontend(MagicMock())

    frontend.quit()
    frontend.quit()

    assert termios.tcsetattr.call_count == 1


def test_quit_restores_terminal_attributes_even_when_stdout_fails(monkeypatch):
    termios = _fakeTermiosModule()
    _enterFakeTerminal(monkeypatch, termios, MagicMock(), io.StringIO())
    frontend = createTextFrontend(MagicMock())
    monkeypatch.setattr("sys.stdout", _FailingStdout())

    frontend.quit()  # must not raise

    termios.tcsetattr.assert_called_once()
    assert frontend._terminalState is None


def test_set_caption_tolerates_stdout_failure_when_terminal_active(monkeypatch):
    frontend = createTextFrontend(MagicMock())
    frontend._terminalState = object()
    monkeypatch.setattr("sys.stdout", _FailingStdout())

    frontend.setCaption("Roam (save2)")  # must not raise

    assert frontend.getRenderer()._caption == "Roam (save2)"
