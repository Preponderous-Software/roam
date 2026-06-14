import sys

from rendering.inputEvent import EventType, InputEvent
from rendering.inputSource import InputSource
from rendering.keyCode import KeyCode, fromInt


# ANSI escape sequences the arrow keys emit (CSI and the SS3 "application"
# variant). Recognizing these stops the leading ESC (\x1b) from being misread
# as a bare Escape keypress.
_ARROW_SEQUENCES = {
    "\x1b[A": KeyCode.UP,
    "\x1b[B": KeyCode.DOWN,
    "\x1b[C": KeyCode.RIGHT,
    "\x1b[D": KeyCode.LEFT,
    "\x1bOA": KeyCode.UP,
    "\x1bOB": KeyCode.DOWN,
    "\x1bOC": KeyCode.RIGHT,
    "\x1bOD": KeyCode.LEFT,
}


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Terminal implementation of the InputSource interface (epic #433 / #239). It
# turns characters typed at the terminal into the neutral InputEvent / KeyCode
# model. KeyCode integer values are the SDL keycodes, which coincide with ASCII
# for letters, digits, Escape (27), Enter (13) and Space (32) — so a typed
# character maps straight through fromInt(ord(char)). Arrow keys arrive as
# multi-byte ANSI escape sequences and are decoded specially. The character
# source is injectable so tests can feed input deterministically without a TTY.
class TextInputSource(InputSource):
    def __init__(self, charReader=None):
        self._charReader = charReader if charReader is not None else _readStdinChars

    def pollEvents(self):
        chars = self._charReader()
        events = []
        index = 0
        length = len(chars)
        while index < length:
            char = chars[index]
            if char == "\x1b":
                arrow = _ARROW_SEQUENCES.get(chars[index : index + 3])
                if arrow is not None:
                    events.append(InputEvent(EventType.KEY_DOWN, key=arrow))
                    index += 3
                    continue
                # A bare Escape (no following sequence bytes).
                events.append(InputEvent(EventType.KEY_DOWN, key=KeyCode.ESCAPE))
                index += 1
                continue
            events.append(InputEvent(EventType.KEY_DOWN, key=fromInt(ord(char))))
            if char.isprintable():
                events.append(InputEvent(EventType.TEXT_INPUT, text=char))
            index += 1
        return events

    def isPressed(self, keyCode):
        # A line/character terminal has no reliable held-key state.
        return False

    def getMousePosition(self):
        return (0, 0)

    def getMouseButtons(self):
        return (False, False, False)


# A short poll wait so a loop driven by pollEvents (notably the menu screens,
# which have no Clock) paces itself instead of busy-spinning the terminal.
_POLL_TIMEOUT_SECONDS = 0.02


def _readStdinChars():
    """Return the characters currently waiting on stdin, blocking up to a short
    timeout for the first one and then draining the rest (so a multi-byte arrow
    escape sequence arrives as one unit). Returns "" when stdin is not an
    interactive terminal (tests, pipes, CI)."""
    try:
        if not sys.stdin.isatty():
            return ""
    except (ValueError, AttributeError):
        return ""
    import select

    ready, _, _ = select.select([sys.stdin], [], [], _POLL_TIMEOUT_SECONDS)
    if not ready:
        return ""
    chars = []
    while True:
        chars.append(sys.stdin.read(1))
        if not select.select([sys.stdin], [], [], 0)[0]:
            break
    return "".join(chars)
