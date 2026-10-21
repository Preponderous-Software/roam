import pytest

from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from screen.optionsScreen import OptionsScreen
from screen.screenType import ScreenType
from ui import palette

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


# Characterization tests for keyboard navigation, the confirmation overlay's
# keys, event dispatch and the draw path, which run against the
# PygameRenderer-spec mock registered by conftest (display 1280x720).

MENU_LABELS = ["Quit to Main Menu", "Stats", "Inventory", "Controls", "Codex", "Back"]


def _calls(renderer, method):
    return [c.args for c in getattr(renderer, method).call_args_list]


def test_menu_lists_its_items_in_order(resolve):
    screen = resolve(OptionsScreen)

    assert [label for label, _ in screen._MENU_ITEMS] == MENU_LABELS


@pytest.mark.parametrize("key", [KeyCode.DOWN, KeyCode.S])
def test_down_keys_advance_the_cursor_and_wrap_to_top(resolve, key):
    screen = resolve(OptionsScreen)

    screen.handleKeyDownEvent(key)
    assert screen._cursor == 1

    screen._cursor = len(MENU_LABELS) - 1
    screen.handleKeyDownEvent(key)
    assert screen._cursor == 0
    assert screen.changeScreen is False


@pytest.mark.parametrize("key", [KeyCode.UP, KeyCode.W])
def test_up_keys_retreat_the_cursor_and_wrap_to_bottom(resolve, key):
    screen = resolve(OptionsScreen)

    screen.handleKeyDownEvent(key)
    assert screen._cursor == len(MENU_LABELS) - 1

    screen.handleKeyDownEvent(key)
    assert screen._cursor == len(MENU_LABELS) - 2
    assert screen.changeScreen is False


@pytest.mark.parametrize(
    "cursor, expectedScreen",
    [
        (1, ScreenType.STATS_SCREEN),
        (2, ScreenType.INVENTORY_SCREEN),
        (3, ScreenType.CONTROLS_SCREEN),
        (4, ScreenType.CODEX_SCREEN),
        (5, ScreenType.WORLD_SCREEN),
    ],
)
def test_return_activates_the_item_under_the_cursor(resolve, cursor, expectedScreen):
    screen = resolve(OptionsScreen)
    screen._cursor = cursor

    screen.handleKeyDownEvent(KeyCode.RETURN)

    assert screen.nextScreen == expectedScreen
    assert screen.changeScreen is True


@pytest.mark.parametrize("key", [KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE])
def test_confirm_keys_on_quit_item_open_the_confirmation(resolve, key):
    screen = resolve(OptionsScreen)

    screen.handleKeyDownEvent(key)

    assert screen.confirmingMainMenu is True
    assert screen.changeScreen is False


@pytest.mark.parametrize("key", [KeyCode.RETURN, KeyCode.KP_ENTER])
def test_enter_while_confirming_goes_to_main_menu(resolve, key):
    screen = resolve(OptionsScreen)
    screen.requestMainMenuConfirmation()

    screen.handleKeyDownEvent(key)

    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN
    assert screen.changeScreen is True


@pytest.mark.parametrize("key", [KeyCode.SPACE, KeyCode.DOWN, KeyCode.UP, KeyCode.U])
def test_other_keys_while_confirming_are_ignored(resolve, key):
    # SPACE selects a menu item normally, but not inside the confirmation, and
    # navigation keys do not move the hidden cursor.
    screen = resolve(OptionsScreen)
    screen.requestMainMenuConfirmation()

    screen.handleKeyDownEvent(key)

    assert screen.confirmingMainMenu is True
    assert screen.changeScreen is False
    assert screen._cursor == 0


def test_handle_event_dispatches_only_key_down(resolve):
    screen = resolve(OptionsScreen)

    screen.handleEvent(InputEvent(EventType.KEY_DOWN, key=KeyCode.DOWN))
    assert screen._cursor == 1

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    screen.handleEvent(InputEvent(EventType.MOUSE_DOWN, position=(0, 0), button=1))
    assert screen._cursor == 1
    assert screen.changeScreen is False


def test_on_start_resets_the_cursor(resolve):
    screen = resolve(OptionsScreen)
    screen._cursor = 4

    screen.onStart()

    assert screen._cursor == 0


def test_on_exit_dismisses_the_confirmation(resolve):
    screen = resolve(OptionsScreen)
    screen.requestMainMenuConfirmation()

    screen.onExit()

    assert screen.confirmingMainMenu is False


def test_draw_title_centres_the_heading(resolve):
    screen = resolve(OptionsScreen)

    screen.drawTitle()

    screen.renderer.drawText.assert_called_once_with("Menu", 640, 25, 36, palette.WHITE)


def test_menu_buttons_show_labels_and_layout(resolve):
    screen = resolve(OptionsScreen)

    screen.drawMenuButtons()

    rows = _calls(screen.renderer, "drawButton")
    assert [args[7] for args in rows] == ["> Quit to Main Menu"] + MENU_LABELS[1:]
    # A third of the width, a tenth of the height, centred, 10px apart from y=70.
    for i, args in enumerate(rows):
        assert args[:4] == pytest.approx((1280 / 3, 70 + i * 82, 1280 / 3, 72))
        assert args[5:7] == (palette.BLACK, 30)
    assert rows[0][4] == palette.LIGHT_GRAY
    assert all(args[4] == palette.WHITE for args in rows[1:])
    screen.renderer.drawSelectionHighlight.assert_called_once()
    highlight = screen.renderer.drawSelectionHighlight.call_args.args
    assert highlight[:4] == pytest.approx((1280 / 3, 70, 1280 / 3, 72))
    assert highlight[4] == (255, 255, 0)
    screen.renderer.drawText.assert_called_once_with(
        "Up/Down: navigate  -  Enter: select  -  Esc: back",
        640,
        70 + 6 * 82 + 10,
        14,
        palette.DIM_GRAY,
    )


def test_highlight_follows_the_cursor(resolve):
    screen = resolve(OptionsScreen)
    screen._cursor = 3

    screen.drawMenuButtons()

    labels = [args[7] for args in _calls(screen.renderer, "drawButton")]
    assert labels[3] == "> Controls"
    assert labels[0] == "Quit to Main Menu"
    highlight = screen.renderer.drawSelectionHighlight.call_args.args
    assert highlight[1] == 70 + 3 * 82


def test_menu_button_callbacks_run_their_item(resolve):
    screen = resolve(OptionsScreen)

    screen.drawMenuButtons()
    callbacks = [args[8] for args in _calls(screen.renderer, "drawButton")]

    callbacks[0]()
    assert screen.confirmingMainMenu is True
    assert screen.changeScreen is False

    callbacks[4]()
    assert screen.nextScreen == ScreenType.CODEX_SCREEN
    assert screen.changeScreen is True


def test_confirmation_overlay_shows_prompt_and_two_buttons(resolve):
    screen = resolve(OptionsScreen)

    screen.drawMainMenuConfirmation()

    # A centred panel 60% wide and 35% tall.
    rectangle = screen.renderer.drawRectangle.call_args.args
    assert rectangle[:4] == pytest.approx((256, 234, 768, 252))
    assert rectangle[4] == palette.CHARCOAL
    texts = [args[0] for args in _calls(screen.renderer, "drawText")]
    assert texts == [
        "Return to main menu?",
        "Your current session will end.",
        "Your progress will be saved automatically.",
        "Enter: confirm  -  Esc: cancel",
    ]
    quitButton, cancelButton = _calls(screen.renderer, "drawButton")
    assert quitButton[4:8] == (palette.RED, palette.WHITE, 22, "Quit to Menu")
    assert cancelButton[4:8] == (palette.WHITE, palette.BLACK, 22, "Cancel")
    # Two buttons, 35% of the panel wide, 20px apart, centred on the screen.
    assert quitButton[:4] == pytest.approx((361.2, 405.36, 268.8, 55.44))
    assert cancelButton[:4] == pytest.approx((650.0, 405.36, 268.8, 55.44))


def test_confirmation_buttons_confirm_and_cancel(resolve):
    screen = resolve(OptionsScreen)
    screen.requestMainMenuConfirmation()

    screen.drawMainMenuConfirmation()
    quitButton, cancelButton = _calls(screen.renderer, "drawButton")

    cancelButton[8]()
    assert screen.confirmingMainMenu is False
    assert screen.changeScreen is False

    quitButton[8]()
    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN
    assert screen.changeScreen is True


def test_draw_shows_the_menu_when_not_confirming(resolve):
    screen = resolve(OptionsScreen)

    screen.draw()

    screen.renderer.clearScreen.assert_called_once_with(palette.BLACK)
    labels = [args[7] for args in _calls(screen.renderer, "drawButton")]
    assert len(labels) == len(MENU_LABELS)
    screen.renderer.drawRectangle.assert_not_called()


def test_draw_replaces_the_menu_with_the_confirmation(resolve):
    # The menu buttons are not drawn, so their click rects cannot fire
    # through the overlay.
    screen = resolve(OptionsScreen)
    screen.requestMainMenuConfirmation()

    screen.draw()

    screen.renderer.clearScreen.assert_called_once_with(palette.BLACK)
    labels = [args[7] for args in _calls(screen.renderer, "drawButton")]
    assert labels == ["Quit to Menu", "Cancel"]
    texts = [args[0] for args in _calls(screen.renderer, "drawText")]
    assert texts[0] == "Menu"
    screen.renderer.drawSelectionHighlight.assert_not_called()
