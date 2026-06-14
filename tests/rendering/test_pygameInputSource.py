import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from rendering.pygameInputSource import PygameInputSource


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((100, 100))
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def drain_events():
    pygame.event.clear()
    yield
    pygame.event.clear()


def _pollOne(eventDict):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(eventDict.pop("type"), **eventDict))
    events = PygameInputSource().pollEvents()
    assert len(events) == 1
    return events[0]


def test_keydown_maps_to_neutral_keycode():
    event = _pollOne({"type": pygame.KEYDOWN, "key": pygame.K_w})
    assert event.type is EventType.KEY_DOWN
    assert event.key is KeyCode.W


def test_keyup_maps_to_key_up():
    event = _pollOne({"type": pygame.KEYUP, "key": pygame.K_ESCAPE})
    assert event.type is EventType.KEY_UP
    assert event.key is KeyCode.ESCAPE


def test_unmodeled_key_becomes_none():
    # A key the game never binds (e.g. F12) maps to None rather than raising.
    event = _pollOne({"type": pygame.KEYDOWN, "key": pygame.K_F12})
    assert event.type is EventType.KEY_DOWN
    assert event.key is None


def test_mouse_button_down_carries_position_and_button():
    event = _pollOne({"type": pygame.MOUSEBUTTONDOWN, "pos": (12, 34), "button": 1})
    assert event.type is EventType.MOUSE_DOWN
    assert event.position == (12, 34)
    assert event.button == 1


def test_mouse_wheel_carries_scroll():
    event = _pollOne({"type": pygame.MOUSEWHEEL, "y": -2})
    assert event.type is EventType.MOUSE_WHEEL
    assert event.scrollY == -2


def test_text_input_carries_text():
    event = _pollOne({"type": pygame.TEXTINPUT, "text": "Q"})
    assert event.type is EventType.TEXT_INPUT
    assert event.text == "Q"


def test_quit_maps_to_quit():
    event = _pollOne({"type": pygame.QUIT})
    assert event.type is EventType.QUIT


def test_poll_drains_and_preserves_order():
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    source = PygameInputSource()
    events = source.pollEvents()
    assert [e.key for e in events] == [KeyCode.A, KeyCode.D]
    # queue is drained
    assert source.pollEvents() == []


def test_is_pressed_is_safe_for_large_keycodes():
    # Arrow/modifier keycodes fall outside pygame.key.get_pressed()'s range;
    # the query must return a clean False, never raise.
    source = PygameInputSource()
    assert source.isPressed(KeyCode.UP) is False
    assert source.isPressed(None) is False


def test_mouse_helpers_return_state():
    source = PygameInputSource()
    assert len(source.getMousePosition()) == 2
    assert len(source.getMouseButtons()) >= 3
