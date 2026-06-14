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
