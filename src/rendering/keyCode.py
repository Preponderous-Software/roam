from enum import IntEnum


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Backend-neutral keyboard codes (frontend-abstraction epic #433, Phase 4).
#
# Game logic (KeyBindings, screens) refers to keys by these members instead of
# pygame's K_* constants, so the same code runs behind any InputSource. An input
# frontend maps its native key events to/from KeyCode at the boundary.
#
# The integer VALUES are the SDL keycodes — i.e. exactly what pygame's K_*
# constants already are. This is deliberate, for two reasons:
#   1. Back-compat: existing config.yml `key_*` entries store the old pygame
#      ints; because KeyCode(<that int>) round-trips, saved keybindings keep
#      working with no migration.
#   2. The pygame frontend can map a raw event key with a plain KeyCode(event.key).
# SDL keycodes are a stable, well-documented standard, so anchoring to them does
# not couple game logic back to pygame — only the values happen to coincide.
class KeyCode(IntEnum):
    # letters
    A = 97
    C = 99
    D = 100
    F = 102
    G = 103
    I = 105
    L = 108
    M = 109
    S = 115
    T = 116
    U = 117
    W = 119

    # digits
    NUM_0 = 48
    NUM_1 = 49
    NUM_2 = 50
    NUM_3 = 51
    NUM_4 = 52
    NUM_5 = 53
    NUM_6 = 54
    NUM_7 = 55
    NUM_8 = 56
    NUM_9 = 57

    # arrows
    UP = 1073741906
    DOWN = 1073741905
    LEFT = 1073741904
    RIGHT = 1073741903

    # modifiers
    LSHIFT = 1073742049
    RSHIFT = 1073742053
    LCTRL = 1073742048
    RCTRL = 1073742052

    # function / special
    F1 = 1073741882
    F3 = 1073741884
    PRINTSCREEN = 1073741894
    LEFTBRACKET = 91
    RIGHTBRACKET = 93
    EQUALS = 61
    MINUS = 45
    ESCAPE = 27
    RETURN = 13
    KP_ENTER = 1073741912
    BACKSPACE = 8
    SPACE = 32


# Human-readable names for the controls UI. Mirrors pygame.key.name() output for
# the bound keys, so the keybinding screen reads the same after the migration.
_DISPLAY_NAMES = {
    KeyCode.A: "a",
    KeyCode.C: "c",
    KeyCode.D: "d",
    KeyCode.F: "f",
    KeyCode.G: "g",
    KeyCode.I: "i",
    KeyCode.L: "l",
    KeyCode.M: "m",
    KeyCode.S: "s",
    KeyCode.T: "t",
    KeyCode.U: "u",
    KeyCode.W: "w",
    KeyCode.NUM_0: "0",
    KeyCode.NUM_1: "1",
    KeyCode.NUM_2: "2",
    KeyCode.NUM_3: "3",
    KeyCode.NUM_4: "4",
    KeyCode.NUM_5: "5",
    KeyCode.NUM_6: "6",
    KeyCode.NUM_7: "7",
    KeyCode.NUM_8: "8",
    KeyCode.NUM_9: "9",
    KeyCode.UP: "up",
    KeyCode.DOWN: "down",
    KeyCode.LEFT: "left",
    KeyCode.RIGHT: "right",
    KeyCode.LSHIFT: "left shift",
    KeyCode.RSHIFT: "right shift",
    KeyCode.LCTRL: "left ctrl",
    KeyCode.RCTRL: "right ctrl",
    KeyCode.F1: "f1",
    KeyCode.F3: "f3",
    KeyCode.PRINTSCREEN: "print screen",
    KeyCode.LEFTBRACKET: "[",
    KeyCode.RIGHTBRACKET: "]",
    KeyCode.EQUALS: "=",
    KeyCode.MINUS: "-",
    KeyCode.ESCAPE: "escape",
    KeyCode.RETURN: "return",
    KeyCode.KP_ENTER: "enter",
    KeyCode.BACKSPACE: "backspace",
    KeyCode.SPACE: "space",
}


def fromInt(value):
    """Map a raw integer keycode to a KeyCode, or None if it is not one we
    model. Lets a frontend translate native key events without raising on the
    many keys the game never binds."""
    try:
        return KeyCode(value)
    except ValueError:
        return None


def displayName(keyCode):
    """Human-readable name for a KeyCode (for the controls screen)."""
    if keyCode is None:
        return "None"
    return _DISPLAY_NAMES.get(keyCode, str(keyCode))
