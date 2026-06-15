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

# Movement keys that need a synthetic KEY_UP immediately after KEY_DOWN so
# the player moves exactly one tile per keypress. Without this the terminal's
# OS-level key-repeat keeps firing KEY_DOWN events and the player walks
# indefinitely (there is no physical KEY_UP from a terminal).
_MOVEMENT_KEYS = {
    KeyCode.UP, KeyCode.DOWN, KeyCode.LEFT, KeyCode.RIGHT,
    KeyCode.W, KeyCode.A, KeyCode.S, KeyCode.D,
}

# Control bytes whose terminal value differs from the KeyCode (SDL) value. In
# cbreak mode the Enter key arrives as "\n" (CR translated to LF), not the
# "\r" KeyCode.RETURN expects; the terminal sends DEL ("\x7f") for Backspace,
# not "\x08". Map both forms so menus, save naming, etc. respond.
_CONTROL_CHARS = {
    "\n": KeyCode.RETURN,
    "\r": KeyCode.RETURN,
    "\x7f": KeyCode.BACKSPACE,
    "\x08": KeyCode.BACKSPACE,
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
                    events.append(InputEvent(EventType.KEY_UP, key=arrow))
                    index += 3
                    continue
                # A bare Escape (no following sequence bytes).
                events.append(InputEvent(EventType.KEY_DOWN, key=KeyCode.ESCAPE))
                index += 1
                continue
            keyCode = _CONTROL_CHARS.get(char)
            if keyCode is None:
                keyCode = fromInt(ord(char))
            events.append(InputEvent(EventType.KEY_DOWN, key=keyCode))
            if keyCode in _MOVEMENT_KEYS:
                events.append(InputEvent(EventType.KEY_UP, key=keyCode))
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
    timeout. Returns "" when stdin is not an interactive terminal (tests, pipes,
    CI).

    Reads via os.read on the raw file descriptor rather than sys.stdin.read so
    select() and the read see the same bytes: sys.stdin is buffered, so it can
    pull a whole escape sequence into Python's buffer while select() — which
    only sees the fd — then reports nothing more, splitting an arrow key's
    ESC [ A into a bare ESC. os.read grabs the entire pending burst at once."""
    try:
        if not sys.stdin.isatty():
            return ""
    except (ValueError, AttributeError):
        return ""
    import os
    import select

    fd = sys.stdin.fileno()
    try:
        ready, _, _ = select.select([fd], [], [], _POLL_TIMEOUT_SECONDS)
        if not ready:
            return ""
        # The whole pending burst (a typed char, or an arrow's 3-byte sequence)
        # is available in one non-blocking read.
        return os.read(fd, 64).decode("utf-8", errors="ignore")
    except (OSError, ValueError):
        # A signal interrupting the read (EINTR), or a closed/invalid fd during
        # shutdown — treat as "no input this frame" rather than crashing the loop.
        return ""
