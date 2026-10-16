import types

import rendering.webInputSource as webInputSourceModule
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from rendering.textInputSource import TextInputSource
from rendering.webInputSource import WebInputSource


def _noSleep(monkeypatch):
    # The empty-queue path sleeps to pace an idle loop; record instead of waiting.
    # Patch the module's own `time` reference, not the global time.sleep.
    sleeps = []
    monkeypatch.setattr(
        webInputSourceModule, "time", types.SimpleNamespace(sleep=sleeps.append)
    )
    return sleeps


def test_is_a_text_input_source_with_quiescent_mouse_defaults(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    assert isinstance(source, TextInputSource)
    assert source.getMousePosition() == (0, 0)
    assert source.getMouseButtons() == (False, False, False)
    assert source.pollEvents() == []


def test_fed_characters_are_parsed_like_terminal_input(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.feed("\x1b[A")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.UP]


def test_empty_feed_is_ignored(monkeypatch):
    sleeps = _noSleep(monkeypatch)
    source = WebInputSource()
    source.feed("")
    assert source.pollEvents() == []
    assert sleeps == [0.02]


def test_each_poll_consumes_one_fed_burst(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.feed("w")
    source.feed("\x1b")
    first = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    second = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert first == [KeyCode.W]
    assert second == [KeyCode.ESCAPE]


def test_idle_poll_sleeps_to_pace_the_loop(monkeypatch):
    sleeps = _noSleep(monkeypatch)
    source = WebInputSource()
    source.pollEvents()
    assert sleeps == [0.02]


def test_poll_with_pending_input_does_not_sleep(monkeypatch):
    sleeps = _noSleep(monkeypatch)
    source = WebInputSource()
    source.feed("a")
    source.pollEvents()
    assert sleeps == []


def test_mouse_down_sets_button_state_and_queues_event(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.updateMouse(12, 34, 3, True)
    assert source.getMousePosition() == (12, 34)
    assert source.getMouseButtons() == (False, False, True)
    events = source.pollEvents()
    assert len(events) == 1
    assert events[0].type is EventType.MOUSE_DOWN
    assert events[0].position == (12, 34)
    assert events[0].button == 3


def test_mouse_up_clears_button_state_and_queues_event(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.updateMouse(5, 6, 1, True)
    source.updateMouse(7, 8, 1, False)
    assert source.getMousePosition() == (7, 8)
    assert source.getMouseButtons() == (False, False, False)
    types = [e.type for e in source.pollEvents()]
    assert types == [EventType.MOUSE_DOWN, EventType.MOUSE_UP]


def test_out_of_range_button_queues_event_without_touching_button_state(
    monkeypatch,
):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.updateMouse(1, 2, 4, True)
    assert source.getMouseButtons() == (False, False, False)
    assert source.getMousePosition() == (1, 2)
    events = source.pollEvents()
    assert [e.button for e in events] == [4]


def test_button_zero_does_not_wrap_to_the_right_button(monkeypatch):
    # idx = button - 1 = -1 must not index the last slot.
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.updateMouse(0, 0, 0, True)
    assert source.getMouseButtons() == (False, False, False)


def test_move_mouse_updates_position_and_queues_motion(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.moveMouse(40, 50)
    assert source.getMousePosition() == (40, 50)
    events = source.pollEvents()
    assert len(events) == 1
    assert events[0].type is EventType.MOUSE_MOTION
    assert events[0].position == (40, 50)
    assert events[0].button is None


def test_consume_left_click_clears_only_the_left_button(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.updateMouse(0, 0, 1, True)
    source.updateMouse(0, 0, 3, True)
    source.consumeLeftClick()
    assert source.getMouseButtons() == (False, False, True)


def test_mouse_events_precede_key_events_from_the_same_poll(monkeypatch):
    _noSleep(monkeypatch)
    source = WebInputSource()
    source.feed("w")
    source.moveMouse(1, 1)
    types = [e.type for e in source.pollEvents()]
    assert types[0] is EventType.MOUSE_MOTION
    assert EventType.KEY_DOWN in types[1:]
