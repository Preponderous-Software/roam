from rendering.keyCode import KeyCode, displayName, fromInt


def test_values_are_sdl_keycodes_for_config_back_compat():
    # The persisted int for each KeyCode must equal the SDL/pygame keycode that
    # earlier versions stored in config.yml, or saved keybindings would break.
    assert KeyCode.W == 119
    assert KeyCode.A == 97
    assert KeyCode.ESCAPE == 27
    assert KeyCode.RETURN == 13
    assert KeyCode.UP == 1073741906
    assert KeyCode.LSHIFT == 1073742049
    assert KeyCode.NUM_0 == 48
    assert KeyCode.KP_ENTER == 1073741912


def test_int_enum_compares_equal_to_raw_int():
    # Screens compare a frontend's raw key int against a KeyCode binding; the
    # IntEnum makes that comparison hold both directions.
    assert 119 == KeyCode.W
    assert KeyCode.W == 119
    assert int(KeyCode.W) == 119


def test_from_int_maps_known_and_unknown():
    assert fromInt(27) is KeyCode.ESCAPE
    assert fromInt(119) is KeyCode.W
    assert fromInt(999999) is None


def test_display_name():
    assert displayName(KeyCode.W) == "w"
    assert displayName(KeyCode.LSHIFT) == "left shift"
    assert displayName(KeyCode.EQUALS) == "="
    assert displayName(None) == "None"


def test_keycode_is_hashable_with_int_collisions():
    # KeyCode hashes like its int, so conflict detection that mixes KeyCode and
    # raw ints in one dict still collides them correctly.
    mapping = {KeyCode.W: "binding"}
    assert mapping[119] == "binding"
    assert hash(KeyCode.W) == hash(119)


# --- keys added for F-key-less terminals (Userland / Android) ---


def test_h_is_defined():
    assert KeyCode.H == 104


def test_backslash_is_defined():
    assert KeyCode.BACKSLASH == 92


def test_h_display_name():
    assert displayName(KeyCode.H) == "h"


def test_backslash_display_name():
    assert displayName(KeyCode.BACKSLASH) == "\\"


def test_from_int_h():
    assert fromInt(104) is KeyCode.H


def test_from_int_backslash():
    assert fromInt(92) is KeyCode.BACKSLASH


# --- every bound key needs a display name (#562) ---


def test_every_default_binding_has_a_display_name():
    # displayName() falls back to str(keyCode) for anything missing from the
    # table, which renders "KeyCode.F2" (or a bare SDL int on Python 3.11+) in
    # the Controls screen's key column instead of a readable name.
    from config.keyBindings import KeyBindings

    for action, key in KeyBindings.DEFAULT_BINDINGS.items():
        assert displayName(key) != str(key), action


def test_f2_display_name():
    assert displayName(KeyCode.F2) == "f2"


# --- keys added for paging the minimap between levels (#559) ---


def test_minimap_paging_keys_are_sdl_keycodes():
    assert KeyCode.PAGEUP == 1073741899
    assert KeyCode.PAGEDOWN == 1073741902
    assert KeyCode.HOME == 1073741898
    assert KeyCode.COMMA == 44
    assert KeyCode.PERIOD == 46
    assert KeyCode.SLASH == 47


def test_minimap_paging_display_names():
    assert displayName(KeyCode.PAGEUP) == "page up"
    assert displayName(KeyCode.PAGEDOWN) == "page down"
    assert displayName(KeyCode.HOME) == "home"
    assert displayName(KeyCode.COMMA) == ","
    assert displayName(KeyCode.PERIOD) == "."
    assert displayName(KeyCode.SLASH) == "/"
