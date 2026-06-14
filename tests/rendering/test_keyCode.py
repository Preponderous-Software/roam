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
