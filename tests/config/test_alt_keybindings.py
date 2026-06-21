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
