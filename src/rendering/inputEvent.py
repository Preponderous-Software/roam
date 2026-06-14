from enum import Enum


# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# Backend-neutral input event model (frontend-abstraction epic #433, Phase 4).
# Screens consume InputEvent / EventType instead of pygame event objects and
# type constants, so the same handling code works behind any InputSource.
class EventType(Enum):
    QUIT = "quit"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    MOUSE_DOWN = "mouse_down"
    MOUSE_UP = "mouse_up"
    MOUSE_MOTION = "mouse_motion"
    MOUSE_WHEEL = "mouse_wheel"
    TEXT_INPUT = "text_input"
    WINDOW_RESIZE = "window_resize"
    FOCUS_LOST = "focus_lost"
    FOCUS_GAINED = "focus_gained"
    OTHER = "other"


class InputEvent:
    """A single input event. Only the fields relevant to `type` are populated:
    key (KEY_DOWN/KEY_UP), position + button (MOUSE_DOWN/MOUSE_UP),
    position (MOUSE_MOTION), scrollY (MOUSE_WHEEL), text (TEXT_INPUT),
    size (WINDOW_RESIZE).

    `key` is a backend-neutral `KeyCode` (or None for an unmodeled key), so
    screens and KeyBindings compare against KeyCode members rather than pygame
    constants. The frontend maps native key events to KeyCode at the boundary.
    """

    __slots__ = ("type", "key", "position", "button", "scrollY", "text", "size")

    def __init__(
        self,
        type,
        key=None,
        position=None,
        button=None,
        scrollY=0,
        text=None,
        size=None,
    ):
        self.type = type
        self.key = key
        self.position = position
        self.button = button
        self.scrollY = scrollY
        self.text = text
        self.size = size

    def __repr__(self):
        return (
            "InputEvent(%r, key=%r, position=%r, button=%r, scrollY=%r, text=%r, size=%r)"
            % (
                self.type,
                self.key,
                self.position,
                self.button,
                self.scrollY,
                self.text,
                self.size,
            )
        )
