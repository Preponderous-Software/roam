import pytest

from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from screen.configScreen import ConfigScreen
from screen.screenType import ScreenType
from ui import palette

# Characterization tests for ConfigScreen (previously no dedicated test file):
# Esc/quit transitions, the cooldown-guarded config toggle, and scroll clamping.


def test_escape_returns_to_main_menu(resolve):
    screen = resolve(ConfigScreen)

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN
    assert screen.changeScreen is True


def test_quit_application_targets_none(resolve):
    screen = resolve(ConfigScreen)

    screen.quitApplication()

    assert screen.nextScreen == ScreenType.NONE
    assert screen.changeScreen is True


def test_toggle_flips_the_named_config_attribute(resolve):
    screen = resolve(ConfigScreen)
    screen.config.debug = False
    screen._lastToggleAt = 0.0  # ensure the cooldown does not suppress the toggle

    screen._toggleConfigAttribute("debug")

    assert screen.config.debug is True


def test_toggle_is_suppressed_within_the_cooldown(resolve):
    screen = resolve(ConfigScreen)
    screen.config.debug = False

    screen._lastToggleAt = 0.0
    screen._toggleConfigAttribute("debug")  # flips False -> True, stamps the clock
    assert screen.config.debug is True

    # An immediate second toggle is inside the 0.25s cooldown -> ignored.
    screen._toggleConfigAttribute("debug")
    assert screen.config.debug is True


def test_toggle_resumes_after_the_cooldown_elapses(resolve):
    screen = resolve(ConfigScreen)
    screen.config.debug = True

    screen._lastToggleAt = 0.0  # far in the past -> cooldown elapsed
    screen._toggleConfigAttribute("debug")

    assert screen.config.debug is False


def test_check_for_updates_is_a_toggleable_setting(resolve):
    screen = resolve(ConfigScreen)

    attributes = [attribute for _, attribute in screen._toggleButtons]
    assert "checkForUpdates" in attributes

    screen.config.checkForUpdates = False
    screen._lastToggleAt = 0.0

    screen._toggleConfigAttribute("checkForUpdates")

    assert screen.config.checkForUpdates is True


def test_scroll_moves_cursor_and_clamps(resolve):
    screen = resolve(ConfigScreen)

    class _Wheel:
        def __init__(self, scrollY):
            self.scrollY = scrollY

    assert screen._cursor == 0
    screen.handleScrollEvent(_Wheel(-1))  # scroll down -> cursor advances
    assert screen._cursor == 1
    screen.handleScrollEvent(_Wheel(1))  # scroll up -> cursor retreats
    assert screen._cursor == 0
    screen.handleScrollEvent(_Wheel(1))  # scroll up at 0 -> clamped
    assert screen._cursor == 0


# Characterization tests for keyboard navigation, event dispatch and the draw
# path, which run against the PygameRenderer-spec mock registered by conftest
# (display 1280x720, so all 10 rows fit; tests that need scrolling shrink it).

TOGGLE_COUNT = 10


def _textCalls(renderer, method):
    return [c.args for c in getattr(renderer, method).call_args_list]


def _setAllToggles(screen, value):
    for _, attribute in screen._toggleButtons:
        setattr(screen.config, attribute, value)


def test_lists_every_toggleable_setting_in_order(resolve):
    screen = resolve(ConfigScreen)

    assert [attribute for _, attribute in screen._toggleButtons] == [
        "debug",
        "fullscreen",
        "autoEatFoodInInventory",
        "removeDeadEntities",
        "showMiniMap",
        "cameraFollowPlayer",
        "limitTps",
        "pushableStone",
        "dayNightCycleEnabled",
        "checkForUpdates",
    ]


def test_down_key_advances_cursor_and_wraps_to_top(resolve):
    screen = resolve(ConfigScreen)

    screen.handleKeyDownEvent(KeyCode.DOWN)
    assert screen._cursor == 1

    screen._cursor = TOGGLE_COUNT - 1
    screen.handleKeyDownEvent(KeyCode.DOWN)
    assert screen._cursor == 0
    assert screen.changeScreen is False


def test_up_key_wraps_to_bottom_and_pulls_scroll_offset_back(resolve):
    screen = resolve(ConfigScreen)

    screen.handleKeyDownEvent(KeyCode.UP)
    assert screen._cursor == TOGGLE_COUNT - 1

    # Moving above the first visible row scrolls the window up with the cursor.
    screen._cursor = 4
    screen.scrollOffset = 4
    screen.handleKeyDownEvent(KeyCode.UP)
    assert screen._cursor == 3
    assert screen.scrollOffset == 3


@pytest.mark.parametrize("key", [KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE])
def test_confirm_keys_toggle_the_setting_under_the_cursor(resolve, key):
    screen = resolve(ConfigScreen)
    _setAllToggles(screen, False)
    screen._cursor = 2
    screen._lastToggleAt = 0.0

    screen.handleKeyDownEvent(key)

    assert screen.config.autoEatFoodInInventory is True
    assert screen.config.debug is False
    assert screen.config.fullscreen is False


def test_unbound_key_changes_nothing(resolve):
    screen = resolve(ConfigScreen)
    _setAllToggles(screen, False)
    screen._cursor = 3
    screen._lastToggleAt = 0.0

    screen.handleKeyDownEvent(KeyCode.A)

    assert screen._cursor == 3
    assert screen.changeScreen is False
    assert screen.config.removeDeadEntities is False


def test_handle_event_dispatches_key_down_and_mouse_wheel(resolve):
    screen = resolve(ConfigScreen)

    screen.handleEvent(InputEvent(EventType.KEY_DOWN, key=KeyCode.DOWN))
    assert screen._cursor == 1

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    assert screen._cursor == 2

    screen.handleEvent(InputEvent(EventType.MOUSE_DOWN, position=(0, 0), button=1))
    assert screen._cursor == 2
    assert screen.changeScreen is False


def test_scroll_down_stops_at_the_last_row(resolve):
    screen = resolve(ConfigScreen)
    screen._cursor = TOGGLE_COUNT - 1

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))

    assert screen._cursor == TOGGLE_COUNT - 1


def test_on_start_resets_cursor_and_scroll_offset(resolve):
    screen = resolve(ConfigScreen)
    screen._cursor = 5
    screen.scrollOffset = 3

    screen.onStart()

    assert screen._cursor == 0
    assert screen.scrollOffset == 0


def test_draw_title_shows_heading_and_key_hint(resolve):
    screen = resolve(ConfigScreen)

    screen.drawTitle()

    texts = _textCalls(screen.renderer, "drawText")
    assert texts[0] == ("Settings", 640, 25, 36, palette.WHITE)
    assert texts[1] == (
        "Up/Down: navigate  -  Enter/Space: toggle",
        640,
        50,
        14,
        palette.MEDIUM_GRAY,
    )


def test_menu_rows_show_labels_states_and_layout(resolve):
    screen = resolve(ConfigScreen)
    _setAllToggles(screen, False)
    screen.config.fullscreen = True

    screen.drawMenuButtons()

    rows = _textCalls(screen.renderer, "drawButton")
    assert len(rows) == TOGGLE_COUNT
    # Row 0 is selected: light-gray background, "> " marker, red OFF text.
    assert rows[0][:8] == (
        320,
        60,
        640,
        28,
        palette.LIGHT_GRAY,
        (200, 50, 50),
        20,
        "> Debug Mode: OFF",
    )
    # Row 1 is unselected and on: white background, green ON text, 35px lower.
    assert rows[1][:8] == (
        320,
        95,
        640,
        28,
        palette.WHITE,
        (0, 200, 0),
        20,
        "  Fullscreen: ON",
    )
    assert rows[-1][7] == "  Check For Updates: OFF"
    screen.renderer.drawSelectionHighlight.assert_called_once_with(
        320, 60, 640, 28, (255, 255, 0)
    )
    # Every row fits at 720px, so no scroll range is shown.
    screen.renderer.drawText.assert_not_called()


def test_menu_row_callback_toggles_its_own_setting(resolve):
    screen = resolve(ConfigScreen)
    _setAllToggles(screen, False)
    screen._lastToggleAt = 0.0

    screen.drawMenuButtons()
    callback = _textCalls(screen.renderer, "drawButton")[4][8]
    callback()

    assert screen.config.showMiniMap is True
    assert screen.config.debug is False


def test_highlight_follows_the_cursor(resolve):
    screen = resolve(ConfigScreen)
    _setAllToggles(screen, False)
    screen._cursor = 3

    screen.drawMenuButtons()

    labels = [args[7] for args in _textCalls(screen.renderer, "drawButton")]
    assert labels[3] == "> Remove Dead Creatures: OFF"
    assert labels[0] == "  Debug Mode: OFF"
    screen.renderer.drawSelectionHighlight.assert_called_once_with(
        320, 165, 640, 28, (255, 255, 0)
    )


def test_short_display_scrolls_to_keep_the_cursor_visible(resolve):
    # 300px tall -> (300 - 60 - 80) // 35 = 4 visible rows.
    screen = resolve(ConfigScreen)
    screen.renderer.getDisplaySize.return_value = (1280, 300)
    _setAllToggles(screen, False)
    screen._cursor = 5

    screen.drawMenuButtons()

    assert screen.scrollOffset == 2
    labels = [args[7] for args in _textCalls(screen.renderer, "drawButton")]
    assert labels == [
        "  Auto Eat Food: OFF",
        "  Remove Dead Creatures: OFF",
        "  Show Minimap: OFF",
        "> Camera Follow Player: OFF",
    ]
    screen.renderer.drawSelectionHighlight.assert_called_once_with(
        320, 165, 640, 28, (255, 255, 0)
    )
    screen.renderer.drawText.assert_called_once_with(
        "3-6 of 10", 640, 230, 16, palette.MEDIUM_GRAY
    )


def test_short_display_clamps_an_out_of_range_scroll_offset(resolve):
    screen = resolve(ConfigScreen)
    screen.renderer.getDisplaySize.return_value = (1280, 300)
    _setAllToggles(screen, False)
    screen.scrollOffset = 50

    screen.drawMenuButtons()

    assert screen.scrollOffset == TOGGLE_COUNT - 4
    screen.renderer.drawText.assert_called_once_with(
        "7-10 of 10", 640, 230, 16, palette.MEDIUM_GRAY
    )


def test_tall_display_resets_a_stale_scroll_offset(resolve):
    screen = resolve(ConfigScreen)
    _setAllToggles(screen, False)
    screen.scrollOffset = 4

    screen.drawMenuButtons()

    assert screen.scrollOffset == 0
    assert len(_textCalls(screen.renderer, "drawButton")) == TOGGLE_COUNT


def test_back_button_returns_to_main_menu(resolve):
    screen = resolve(ConfigScreen)

    screen.drawBottomButtons()

    args = screen.renderer.drawButton.call_args.args
    # Centered button one fifth of the width, 45px above the bottom edge.
    assert args[:4] == (512, 675, 256, 35)
    assert args[7] == "Back"
    args[8]()
    assert screen.changeScreen is True
    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN


def test_draw_clears_and_draws_title_rows_and_back_button(resolve):
    screen = resolve(ConfigScreen)
    _setAllToggles(screen, False)

    screen.draw()

    screen.renderer.clearScreen.assert_called_once_with(palette.BLACK)
    texts = [args[0] for args in _textCalls(screen.renderer, "drawText")]
    assert "Settings" in texts
    labels = [args[7] for args in _textCalls(screen.renderer, "drawButton")]
    assert len(labels) == TOGGLE_COUNT + 1
    assert labels[-1] == "Back"
