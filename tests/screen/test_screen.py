from unittest.mock import MagicMock

from rendering.inputEvent import EventType, InputEvent
from screen.screen import Screen
from screen.screenType import ScreenType


class _FakeInputSource:
    """Returns each frame's InputEvent list in turn, then [] forever — so the
    base loop is driven deterministically without touching pygame."""

    def __init__(self, *frames):
        self._frames = list(frames)

    def pollEvents(self):
        return self._frames.pop(0) if self._frames else []


class _RecordingScreen(Screen):
    def __init__(self, inputSource, stopAfterFrames=1):
        self.renderer = MagicMock()
        self.inputSource = inputSource
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = False
        self.starts = 0
        self.exits = 0
        self.handled = []
        self.frames = 0
        self._stopAfterFrames = stopAfterFrames

    def onStart(self):
        self.starts += 1

    def onExit(self):
        self.exits += 1

    def handleEvent(self, event):
        self.handled.append(event.type)

    def draw(self):
        self.frames += 1
        if self.frames >= self._stopAfterFrames:
            self.changeScreen = True


def test_loop_draws_presents_and_returns_next_screen():
    screen = _RecordingScreen(_FakeInputSource(), stopAfterFrames=1)
    result = screen.run()
    assert result == ScreenType.OPTIONS_SCREEN
    assert screen.frames == 1
    assert screen.renderer.present.call_count == 1
    assert screen.starts == 1 and screen.exits == 1
    # changeScreen is reset so the screen can be re-run later.
    assert screen.changeScreen is False


def test_quit_event_requests_shutdown_without_dispatching_to_handle_event():
    inputSource = _FakeInputSource([InputEvent(EventType.QUIT)])
    screen = _RecordingScreen(inputSource, stopAfterFrames=99)
    result = screen.run()
    assert result == ScreenType.NONE
    assert screen.handled == []  # QUIT handled by the base, not the subclass


def test_non_quit_events_are_dispatched_to_handle_event():
    inputSource = _FakeInputSource([InputEvent(EventType.KEY_DOWN)])
    screen = _RecordingScreen(inputSource, stopAfterFrames=99)

    def handle(event):
        screen.handled.append(event.type)
        screen.changeScreen = True

    screen.handleEvent = handle
    result = screen.run()
    assert EventType.KEY_DOWN in screen.handled
    assert result == ScreenType.OPTIONS_SCREEN
