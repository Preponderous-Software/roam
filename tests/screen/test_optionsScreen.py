from rendering.keyCode import KeyCode
from screen.optionsScreen import OptionsScreen
from screen.screenType import ScreenType

# Characterization tests for OptionsScreen (previously no dedicated test file).
# They assert the screen's current behavior — no behavior change intended.


def test_escape_returns_to_world_when_not_confirming(resolve):
    screen = resolve(OptionsScreen)
    assert screen.confirmingMainMenu is False

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    assert screen.nextScreen == ScreenType.WORLD_SCREEN
    assert screen.changeScreen is True


def test_escape_while_confirming_cancels_without_transition(resolve):
    screen = resolve(OptionsScreen)
    screen.requestMainMenuConfirmation()

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    # The confirmation is dismissed; no screen transition is requested.
    assert screen.confirmingMainMenu is False
    assert screen.changeScreen is False


def test_request_and_cancel_main_menu_confirmation_toggle_the_flag(resolve):
    screen = resolve(OptionsScreen)

    screen.requestMainMenuConfirmation()
    assert screen.confirmingMainMenu is True
    # Requesting confirmation must not itself transition.
    assert screen.changeScreen is False

    screen.cancelMainMenuConfirmation()
    assert screen.confirmingMainMenu is False


def test_unbound_key_is_ignored(resolve):
    screen = resolve(OptionsScreen)

    screen.handleKeyDownEvent(KeyCode.U)

    assert screen.changeScreen is False
    assert screen.confirmingMainMenu is False


def test_switch_methods_set_next_screen_and_request_change(resolve):
    cases = {
        "switchToWorldScreen": ScreenType.WORLD_SCREEN,
        "switchToStatsScreen": ScreenType.STATS_SCREEN,
        "switchToInventoryScreen": ScreenType.INVENTORY_SCREEN,
        "switchToMainMenuScreen": ScreenType.MAIN_MENU_SCREEN,
        "switchToConfigScreen": ScreenType.CONFIG_SCREEN,
        "switchToControlsScreen": ScreenType.CONTROLS_SCREEN,
        "switchToCodexScreen": ScreenType.CODEX_SCREEN,
    }
    for methodName, expectedScreen in cases.items():
        screen = resolve(OptionsScreen)
        getattr(screen, methodName)()
        assert screen.nextScreen == expectedScreen
        assert screen.changeScreen is True


def test_quit_application_targets_none(resolve):
    screen = resolve(OptionsScreen)

    screen.quitApplication()

    assert screen.nextScreen == ScreenType.NONE
    assert screen.changeScreen is True
