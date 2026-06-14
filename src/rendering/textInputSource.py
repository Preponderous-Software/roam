import sys

from rendering.inputEvent import EventType, InputEvent
from rendering.inputSource import InputSource
from rendering.keyCode import fromInt


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Terminal implementation of the InputSource interface (epic #433 / #239). It
# turns characters typed at the terminal into the neutral InputEvent / KeyCode
# model. KeyCode integer values are the SDL keycodes, which coincide with ASCII
# for letters, digits, Escape (27), Enter (13) and Space (32) — so a typed
# character maps straight through fromInt(ord(char)). The character source is
# injectable so tests can feed input deterministically without a real TTY.
class TextInputSource(InputSource):
    def __init__(self, charReader=None):
        self._charReader = charReader if charReader is not None else _readStdinChars

    def pollEvents(self):
        events = []
        for char in self._charReader():
            keyCode = fromInt(ord(char))
            events.append(InputEvent(EventType.KEY_DOWN, key=keyCode))
            if char.isprintable():
                events.append(InputEvent(EventType.TEXT_INPUT, text=char))
        return events

    def isPressed(self, keyCode):
        # A line/character terminal has no reliable held-key state.
        return False

    def getMousePosition(self):
        return (0, 0)

    def getMouseButtons(self):
        return (False, False, False)


def _readStdinChars():
    """Return any characters waiting on stdin without blocking. Returns "" when
    stdin is not an interactive terminal (tests, pipes, CI)."""
    try:
        if not sys.stdin.isatty():
            return ""
    except (ValueError, AttributeError):
        return ""
    import select

    ready, _, _ = select.select([sys.stdin], [], [], 0)
    if not ready:
        return ""
    return sys.stdin.read(1)
