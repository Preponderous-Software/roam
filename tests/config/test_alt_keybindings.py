from rendering.keyCode import KeyCode
from config.keyBindings import KeyBindings


def test_alt_toggle_help_defaults_to_h():
    kb = KeyBindings()
    assert kb.getKey("alt_toggle_help") is KeyCode.H


def test_alt_toggle_debug_defaults_to_backslash():
    kb = KeyBindings()
    assert kb.getKey("alt_toggle_debug") is KeyCode.BACKSLASH


def test_alt_toggle_help_label():
    kb = KeyBindings()
    assert kb.getLabel("alt_toggle_help") == "Toggle Help (Alt)"


def test_alt_toggle_debug_label():
    kb = KeyBindings()
    assert kb.getLabel("alt_toggle_debug") == "Toggle Debug (Alt)"


def test_alt_bindings_have_no_conflict_with_primary():
    # H and \ must not clash with any other default binding.
    kb = KeyBindings()
    assert not kb.hasConflicts()


def test_alt_actions_are_in_get_actions():
    kb = KeyBindings()
    assert "alt_toggle_help" in kb.getActions()
    assert "alt_toggle_debug" in kb.getActions()


def test_alt_toggle_help_key_name():
    kb = KeyBindings()
    assert kb.getKeyName("alt_toggle_help") == "h"


def test_alt_toggle_debug_key_name():
    kb = KeyBindings()
    assert kb.getKeyName("alt_toggle_debug") == "\\"


def test_alt_screenshot_defaults_to_p():
    # Print Screen is unreachable from a terminal (see the typability guard
    # below), so text mode needs an ASCII alternative.
    kb = KeyBindings()
    assert kb.getKey("alt_screenshot") is KeyCode.P


def test_alt_screenshot_label_and_key_name():
    kb = KeyBindings()
    assert kb.getLabel("alt_screenshot") == "Screenshot (Alt)"
    assert kb.getKeyName("alt_screenshot") == "p"


def test_alt_screenshot_is_in_get_actions():
    kb = KeyBindings()
    assert "alt_screenshot" in kb.getActions()


def test_every_binding_has_an_action_label():
    # The Controls screen renders getLabel(action) for every action, so a
    # binding with no label would show its raw key there.
    kb = KeyBindings()
    for action in kb.getActions():
        assert action in KeyBindings.ACTION_LABELS, action


# TextInputSource turns terminal input into KeyCodes via fromInt(ord(char)),
# the four arrow escape sequences, and the Enter/Backspace control chars — so
# a key whose value is outside ASCII (F-keys, Print Screen, modifiers) can
# never be pressed in --text mode. Every alt_ binding exists precisely to give
# such an action a terminal-typable trigger, so each one must stay in range.
_TERMINAL_ARROWS = {KeyCode.UP, KeyCode.DOWN, KeyCode.LEFT, KeyCode.RIGHT}


def test_every_alt_binding_is_typable_in_text_mode():
    kb = KeyBindings()
    for action, key in KeyBindings.DEFAULT_BINDINGS.items():
        if not action.startswith("alt_"):
            continue
        assert key in _TERMINAL_ARROWS or int(key) < 128, action
