from rendering.keyCode import KeyCode
from screen.configScreen import ConfigScreen
from screen.screenType import ScreenType


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


def test_scroll_moves_cursor_and_clamps(resolve):
    screen = resolve(ConfigScreen)

    class _Wheel:
        def __init__(self, scrollY):
            self.scrollY = scrollY

    assert screen._cursor == 0
    screen.handleScrollEvent(_Wheel(-1))  # scroll down -> cursor advances
    assert screen._cursor == 1
    screen.handleScrollEvent(_Wheel(1))   # scroll up -> cursor retreats
    assert screen._cursor == 0
    screen.handleScrollEvent(_Wheel(1))   # scroll up at 0 -> clamped
    assert screen._cursor == 0
