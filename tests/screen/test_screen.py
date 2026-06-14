from unittest.mock import MagicMock

import pygame

from screen.screen import Screen
from screen.screenType import ScreenType


class _FakeEvent:
    def __init__(self, eventType):
        self.type = eventType


def _eventGetReturning(*frames):
    """Build a pygame.event.get replacement that returns each frame's event
    list in turn, then [] forever — so the loop is driven deterministically
    without touching the global pygame event queue (which leaks across tests)."""
    queue = list(frames)

    def fake_get():
        return queue.pop(0) if queue else []

    return fake_get


class _RecordingScreen(Screen):
    def __init__(self, stopAfterFrames=1):
        self.renderer = MagicMock()
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


def test_loop_draws_presents_and_returns_next_screen(monkeypatch):
    monkeypatch.setattr(pygame.event, "get", _eventGetReturning())
    screen = _RecordingScreen(stopAfterFrames=1)
    result = screen.run()
    assert result == ScreenType.OPTIONS_SCREEN
    assert screen.frames == 1
    assert screen.renderer.present.call_count == 1
    assert screen.starts == 1 and screen.exits == 1
    # changeScreen is reset so the screen can be re-run later.
    assert screen.changeScreen is False


def test_quit_event_requests_shutdown_without_dispatching_to_handle_event(monkeypatch):
    monkeypatch.setattr(
        pygame.event, "get", _eventGetReturning([_FakeEvent(pygame.QUIT)])
    )
    screen = _RecordingScreen(stopAfterFrames=99)
    result = screen.run()
    assert result == ScreenType.NONE
    assert screen.handled == []  # QUIT handled by the base, not the subclass


def test_non_quit_events_are_dispatched_to_handle_event(monkeypatch):
    monkeypatch.setattr(
        pygame.event, "get", _eventGetReturning([_FakeEvent(pygame.KEYDOWN)])
    )
    screen = _RecordingScreen(stopAfterFrames=99)

    def handle(event):
        screen.handled.append(event.type)
        screen.changeScreen = True

    screen.handleEvent = handle
    result = screen.run()
    assert pygame.KEYDOWN in screen.handled
    assert result == ScreenType.OPTIONS_SCREEN
