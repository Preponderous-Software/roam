import os
import sys

import pytest

from rendering.inputEvent import EventType
from rendering.inputSource import InputSource
from rendering.keyCode import KeyCode
from rendering.textInputSource import TextInputSource


def _sourceFeeding(chars):
    # A char reader that yields `chars` once, then nothing.
    pending = [chars]

    def reader():
        return pending.pop(0) if pending else ""

    return TextInputSource(charReader=reader)


def test_is_an_input_source_with_quiescent_pointer_defaults():
    source = TextInputSource(charReader=lambda: "")
    assert isinstance(source, InputSource)
    assert source.pollEvents() == []
    assert source.getMousePosition() == (0, 0)
    assert source.getMouseButtons() == (False, False, False)
    assert source.isPressed(KeyCode.W) is False


def test_typed_letter_maps_to_a_keycode_key_down_event():
    source = _sourceFeeding("w")
    events = source.pollEvents()
    keyDown = [e for e in events if e.type is EventType.KEY_DOWN]
    assert len(keyDown) == 1
    assert keyDown[0].key is KeyCode.W


def test_escape_maps_to_keycode_escape():
    source = _sourceFeeding("\x1b")  # ESC
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.ESCAPE]


def test_printable_character_also_emits_a_text_input_event():
    source = _sourceFeeding("a")
    types = [e.type for e in source.pollEvents()]
    assert EventType.KEY_DOWN in types
    assert EventType.TEXT_INPUT in types


def test_arrow_escape_sequence_maps_to_an_arrow_keycode():
    # A terminal sends the up arrow as ESC [ A — it must not be read as Escape.
    source = _sourceFeeding("\x1b[A")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.UP]


def test_application_mode_arrow_sequence_is_decoded():
    source = _sourceFeeding("\x1bOB")  # SS3 down arrow
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.DOWN]


def test_bare_escape_still_maps_to_escape():
    source = _sourceFeeding("\x1b")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.ESCAPE]


def test_a_drained_burst_decodes_arrow_then_letter():
    source = _sourceFeeding("\x1b[Bw")  # down arrow immediately followed by 'w'
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.DOWN, KeyCode.W]


@pytest.mark.skipif(not hasattr(os, "openpty"), reason="needs a unix pty")
def test_default_reader_decodes_an_arrow_over_a_real_pty():
    # Exercises the actual os.read path (not the injected mock): a real tty fd,
    # so this catches the buffering bug where select() and a buffered
    # sys.stdin.read split an arrow's ESC [ A into a bare Escape.
    import tty

    master, slave = os.openpty()
    tty.setcbreak(slave)  # what TextFrontend does — non-canonical, so no newline needed
    savedStdin = sys.stdin
    try:
        sys.stdin = os.fdopen(slave, "rb", buffering=0)
        os.write(master, b"\x1b[A")  # up arrow
        keys = [
            e.key
            for e in TextInputSource().pollEvents()
            if e.type is EventType.KEY_DOWN
        ]
        assert keys == [KeyCode.UP]
    finally:
        sys.stdin.close()
        sys.stdin = savedStdin
        os.close(master)


def test_arrow_key_emits_key_up_after_key_down():
    # Terminal key-repeat sends repeated KEY_DOWN; the synthetic KEY_UP stops
    # the player after one tile instead of letting them walk indefinitely.
    source = _sourceFeeding("\x1b[A")  # up arrow
    events = source.pollEvents()
    types = [e.type for e in events]
    assert EventType.KEY_DOWN in types
    assert EventType.KEY_UP in types
    downIdx = next(i for i, e in enumerate(events) if e.type is EventType.KEY_DOWN)
    upIdx = next(i for i, e in enumerate(events) if e.type is EventType.KEY_UP)
    assert upIdx > downIdx
    assert events[upIdx].key is KeyCode.UP


def test_wasd_movement_key_emits_key_up_after_key_down():
    for key_char, expected_key in [("w", KeyCode.W), ("a", KeyCode.A), ("s", KeyCode.S), ("d", KeyCode.D)]:
        source = _sourceFeeding(key_char)
        events = source.pollEvents()
        down_events = [e for e in events if e.type is EventType.KEY_DOWN]
        up_events = [e for e in events if e.type is EventType.KEY_UP]
        assert len(down_events) == 1 and down_events[0].key is expected_key, key_char
        assert len(up_events) == 1 and up_events[0].key is expected_key, key_char


def test_non_movement_key_does_not_emit_key_up():
    source = _sourceFeeding("i")  # inventory key — not a movement key
    events = source.pollEvents()
    assert not any(e.type is EventType.KEY_UP for e in events)


def test_newline_and_carriage_return_map_to_return():
    # cbreak delivers Enter as "\n"; raw mode as "\r" — both are Return.
    for ch in ("\n", "\r"):
        keys = [
            e.key
            for e in _sourceFeeding(ch).pollEvents()
            if e.type is EventType.KEY_DOWN
        ]
        assert keys == [KeyCode.RETURN]


def test_newline_does_not_also_emit_text_input():
    types = [e.type for e in _sourceFeeding("\n").pollEvents()]
    assert EventType.TEXT_INPUT not in types


def test_del_and_backspace_bytes_map_to_backspace():
    for ch in ("\x7f", "\x08"):
        keys = [
            e.key
            for e in _sourceFeeding(ch).pollEvents()
            if e.type is EventType.KEY_DOWN
        ]
        assert keys == [KeyCode.BACKSPACE]


@pytest.mark.skipif(not hasattr(os, "openpty"), reason="needs a unix pty")
def test_default_reader_decodes_enter_over_a_real_pty():
    # The Enter key sends CR; under cbreak the terminal hands us LF. The real
    # os.read path must still resolve it to Return.
    import tty

    master, slave = os.openpty()
    tty.setcbreak(slave)
    savedStdin = sys.stdin
    try:
        sys.stdin = os.fdopen(slave, "rb", buffering=0)
        os.write(master, b"\r")
        keys = [
            e.key
            for e in TextInputSource().pollEvents()
            if e.type is EventType.KEY_DOWN
        ]
        assert keys == [KeyCode.RETURN]
    finally:
        sys.stdin.close()
        sys.stdin = savedStdin
        os.close(master)


# --- new keys added for F-key-less terminals ---

def test_h_key_maps_to_keycode_h():
    source = _sourceFeeding("h")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.H]


def test_backslash_maps_to_keycode_backslash():
    source = _sourceFeeding("\\")   # single backslash, ord 92
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.BACKSLASH]


def test_h_key_does_not_emit_synthetic_key_up():
    # H is not a movement key — no synthetic KEY_UP should follow.
    source = _sourceFeeding("h")
    events = source.pollEvents()
    assert not any(e.type is EventType.KEY_UP for e in events)


# --- more key coverage ---

def test_space_key_maps_to_keycode_space():
    source = _sourceFeeding(" ")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.SPACE]


def test_tab_key_maps_to_keycode_tab():
    source = _sourceFeeding("\t")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.TAB]


def test_digit_keys_map_to_num_keycodes():
    for char, expected in [("1", KeyCode.NUM_1), ("9", KeyCode.NUM_9), ("0", KeyCode.NUM_0)]:
        keys = [
            e.key
            for e in _sourceFeeding(char).pollEvents()
            if e.type is EventType.KEY_DOWN
        ]
        assert keys == [expected], char


def test_left_bracket_maps_to_leftbracket():
    source = _sourceFeeding("[")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.LEFTBRACKET]


def test_right_bracket_maps_to_rightbracket():
    source = _sourceFeeding("]")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.RIGHTBRACKET]


def test_right_arrow_sequence_maps_to_right():
    source = _sourceFeeding("\x1b[C")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.RIGHT]


def test_left_arrow_sequence_maps_to_left():
    source = _sourceFeeding("\x1b[D")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.LEFT]


def test_unknown_control_char_has_none_key():
    # ctrl-A (value 1) has no matching KeyCode entry — fromInt returns None.
    source = _sourceFeeding("\x01")
    events = source.pollEvents()
    down = [e for e in events if e.type is EventType.KEY_DOWN]
    assert len(down) == 1
    assert down[0].key is None


def test_space_is_printable_so_emits_text_input():
    source = _sourceFeeding(" ")
    types = [e.type for e in source.pollEvents()]
    assert EventType.TEXT_INPUT in types


def test_tab_is_not_printable_so_no_text_input():
    source = _sourceFeeding("\t")
    types = [e.type for e in source.pollEvents()]
    assert EventType.TEXT_INPUT not in types


# --- third batch ---

def test_minus_key_maps_to_minus():
    source = _sourceFeeding("-")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.MINUS]


def test_equals_key_maps_to_equals():
    source = _sourceFeeding("=")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.EQUALS]


def test_multiple_chars_in_burst_decoded_in_order():
    # Three chars arriving together must all decode in order (KeyCode.B doesn't
    # exist — use A, C, D which are defined in the enum).
    source = _sourceFeeding("acd")
    keys = [e.key for e in source.pollEvents() if e.type is EventType.KEY_DOWN]
    assert keys == [KeyCode.A, KeyCode.C, KeyCode.D]
