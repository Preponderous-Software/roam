from unittest.mock import MagicMock

import pytest

from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from screen.mainMenuScreen import MainMenuScreen
from screen.screenType import ScreenType
from ui import palette
from update.updateChecker import UpdateChecker

# Coverage for MainMenuScreen's transitions, in particular the backend-neutral
# quit (epic #433 follow-up #463): quitting requests shutdown by returning NONE
# to the main loop rather than calling pygame.quit() directly.


def test_quit_application_requests_shutdown_via_none(resolve):
    screen = resolve(MainMenuScreen)

    screen.quitApplication()

    assert screen.nextScreen == ScreenType.NONE
    assert screen.changeScreen is True


def test_escape_quits(resolve):
    screen = resolve(MainMenuScreen)

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    assert screen.nextScreen == ScreenType.NONE
    assert screen.changeScreen is True


def test_enter_and_space_start_play(resolve):
    for key in (KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE):
        screen = resolve(MainMenuScreen)
        screen.handleKeyDownEvent(key)
        assert screen.nextScreen == ScreenType.SAVE_SELECTION_SCREEN
        assert screen.changeScreen is True


# Characterization tests for keyboard navigation, the update banner and U key,
# event dispatch and the draw path, which run against the PygameRenderer-spec
# mock registered by conftest (display 1280x720). The UpdateChecker is replaced
# by a spec mock so no test starts a network check.

MENU_LABELS = ["Play", "Settings", "Quit"]


@pytest.fixture
def update_checker(override_dependency):
    checker = MagicMock(spec=UpdateChecker)
    checker.isUpdateAvailable.return_value = False
    checker.getLatestVersion.return_value = None
    checker.getReleasesUrl.return_value = "https://example.invalid/releases"
    return override_dependency(UpdateChecker, checker)


@pytest.fixture
def make_screen(resolve, update_checker):
    def make():
        return resolve(MainMenuScreen)

    return make


def _calls(renderer, method):
    return [c.args for c in getattr(renderer, method).call_args_list]


def test_initial_state_selects_play_without_a_transition(make_screen):
    screen = make_screen()

    assert screen._selectedIndex == 0
    assert screen.nextScreen == ScreenType.SAVE_SELECTION_SCREEN
    assert screen.changeScreen is False
    assert screen.running is True


def test_menu_lists_its_items_in_order(make_screen):
    screen = make_screen()

    assert [label for label, _ in screen._MENU_ITEMS] == MENU_LABELS


def test_switch_to_config_screen(make_screen):
    screen = make_screen()

    screen.switchToConfigScreen()

    assert screen.nextScreen == ScreenType.CONFIG_SCREEN
    assert screen.changeScreen is True


def test_switch_to_save_selection_screen(make_screen):
    screen = make_screen()
    screen.nextScreen = ScreenType.CONFIG_SCREEN

    screen.switchToSaveSelectionScreen()

    assert screen.nextScreen == ScreenType.SAVE_SELECTION_SCREEN
    assert screen.changeScreen is True


@pytest.mark.parametrize("key", [KeyCode.DOWN, KeyCode.S])
def test_down_keys_advance_the_selection_and_wrap_to_top(make_screen, key):
    screen = make_screen()

    screen.handleKeyDownEvent(key)
    assert screen._selectedIndex == 1
    screen.handleKeyDownEvent(key)
    assert screen._selectedIndex == 2
    screen.handleKeyDownEvent(key)
    assert screen._selectedIndex == 0
    assert screen.changeScreen is False


@pytest.mark.parametrize("key", [KeyCode.UP, KeyCode.W])
def test_up_keys_retreat_the_selection_and_wrap_to_bottom(make_screen, key):
    screen = make_screen()

    screen.handleKeyDownEvent(key)
    assert screen._selectedIndex == 2
    screen.handleKeyDownEvent(key)
    assert screen._selectedIndex == 1
    assert screen.changeScreen is False


@pytest.mark.parametrize(
    "selectedIndex, expectedScreen",
    [
        (0, ScreenType.SAVE_SELECTION_SCREEN),
        (1, ScreenType.CONFIG_SCREEN),
        (2, ScreenType.NONE),
    ],
)
@pytest.mark.parametrize("key", [KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE])
def test_confirm_keys_activate_the_selected_item(
    make_screen, key, selectedIndex, expectedScreen
):
    screen = make_screen()
    screen._selectedIndex = selectedIndex

    screen.handleKeyDownEvent(key)

    assert screen.nextScreen == expectedScreen
    assert screen.changeScreen is True


def test_escape_quits_whatever_is_selected(make_screen):
    screen = make_screen()
    screen._selectedIndex = 1

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    assert screen.nextScreen == ScreenType.NONE
    assert screen.changeScreen is True


@pytest.mark.parametrize("key", [KeyCode.A, KeyCode.D, KeyCode.TAB, KeyCode.F1])
def test_unbound_keys_are_ignored(make_screen, key):
    screen = make_screen()

    screen.handleKeyDownEvent(key)

    assert screen._selectedIndex == 0
    assert screen.changeScreen is False


def test_u_opens_the_releases_page_when_an_update_is_available(
    make_screen, update_checker, monkeypatch
):
    opened = []
    monkeypatch.setattr("screen.mainMenuScreen.webbrowser.open", opened.append)
    update_checker.isUpdateAvailable.return_value = True
    screen = make_screen()

    screen.handleKeyDownEvent(KeyCode.U)

    assert opened == ["https://example.invalid/releases"]
    assert screen.changeScreen is False


def test_u_does_nothing_without_an_update(make_screen, update_checker, monkeypatch):
    opened = []
    monkeypatch.setattr("screen.mainMenuScreen.webbrowser.open", opened.append)
    screen = make_screen()

    screen.handleKeyDownEvent(KeyCode.U)

    assert opened == []
    update_checker.getReleasesUrl.assert_not_called()
    assert screen.changeScreen is False


def test_on_start_starts_the_update_check(make_screen, update_checker):
    screen = make_screen()

    screen.onStart()

    update_checker.checkForUpdatesAsync.assert_called_once_with()


def test_handle_event_dispatches_only_key_down(make_screen):
    screen = make_screen()

    screen.handleEvent(InputEvent(EventType.KEY_DOWN, key=KeyCode.DOWN))
    assert screen._selectedIndex == 1

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    screen.handleEvent(InputEvent(EventType.MOUSE_DOWN, position=(0, 0), button=1))
    # A released key is not a press, even when it carries a menu key.
    screen.handleEvent(InputEvent(EventType.KEY_UP, key=KeyCode.DOWN))
    assert screen._selectedIndex == 1
    assert screen.changeScreen is False


def test_draw_text_shows_title_and_tagline(make_screen):
    screen = make_screen()

    screen.drawText()

    assert _calls(screen.renderer, "drawText") == [
        ("Roam", 640, 72, 64, palette.WHITE),
        ("Explore a procedurally-generated world", 640, 240, 24, palette.GRAY),
    ]


def test_menu_buttons_show_labels_and_layout(make_screen):
    screen = make_screen()

    screen.drawMenuButtons()

    rows = _calls(screen.renderer, "drawButton")
    assert [args[7] for args in rows] == MENU_LABELS
    # A fifth of the width, a tenth of the height, centred, 10px apart.
    for i, args in enumerate(rows):
        assert args[:4] == pytest.approx((512, 324 + i * 82, 256, 72))
        assert args[4:7] == (palette.WHITE, palette.BLACK, 30)
    screen.renderer.drawSelectionHighlight.assert_called_once()
    highlight = screen.renderer.drawSelectionHighlight.call_args.args
    assert highlight[:4] == pytest.approx((512, 324, 256, 72))
    assert highlight[4] == (255, 255, 0)
    screen.renderer.drawText.assert_called_once_with(
        "W/S or Up/Down: navigate  -  Enter: Play  -  Esc: Quit",
        640,
        324 + 3 * 82 + 6,
        16,
        (160, 160, 160),
    )


def test_highlight_and_hint_follow_the_selection(make_screen):
    screen = make_screen()
    screen._selectedIndex = 2

    screen.drawMenuButtons()

    highlight = screen.renderer.drawSelectionHighlight.call_args.args
    assert highlight[1] == 324 + 2 * 82
    hint = screen.renderer.drawText.call_args.args[0]
    assert hint == "W/S or Up/Down: navigate  -  Enter: Quit  -  Esc: Quit"


def test_menu_button_callbacks_run_their_item(make_screen):
    screen = make_screen()

    screen.drawMenuButtons()
    callbacks = [args[8] for args in _calls(screen.renderer, "drawButton")]

    callbacks[1]()
    assert screen.nextScreen == ScreenType.CONFIG_SCREEN
    assert screen.changeScreen is True

    callbacks[2]()
    assert screen.nextScreen == ScreenType.NONE

    callbacks[0]()
    assert screen.nextScreen == ScreenType.SAVE_SELECTION_SCREEN


def test_draw_version_shows_and_caches_the_label(make_screen):
    screen = make_screen()
    screen.config.getVersion.return_value = "1.2.3"

    screen.drawVersion()
    screen.config.getVersion.return_value = "9.9.9"
    screen.drawVersion()

    # The label is read once and cached for later frames.
    assert _calls(screen.renderer, "drawText") == [
        ("Roam v1.2.3", 640, 710, 16, palette.WHITE),
        ("Roam v1.2.3", 640, 710, 16, palette.WHITE),
    ]
    screen.config.getVersion.assert_called_once_with()


@pytest.mark.parametrize("version", ["", None, "unknown"])
def test_draw_version_hides_a_missing_version(make_screen, version):
    screen = make_screen()
    screen.config.getVersion.return_value = version

    screen.drawVersion()
    screen.drawVersion()

    screen.renderer.drawText.assert_not_called()
    # Nothing is cached, so the version is read again on the next frame.
    assert screen.config.getVersion.call_count == 2


def test_update_banner_is_hidden_without_an_update(make_screen, update_checker):
    screen = make_screen()

    screen.drawUpdateBanner()

    screen.renderer.drawText.assert_not_called()
    update_checker.getLatestVersion.assert_not_called()


def test_update_banner_names_the_latest_version(make_screen, update_checker):
    update_checker.isUpdateAvailable.return_value = True
    update_checker.getLatestVersion.return_value = "0.13.0"
    screen = make_screen()

    screen.drawUpdateBanner()

    text, x, y, size, colour = screen.renderer.drawText.call_args.args
    assert text == "Update available: v0.13.0  -  press U to download"
    assert (x, size, colour) == (640, 18, (255, 220, 120))
    assert y == pytest.approx(720 * 0.42)


def test_draw_clears_then_draws_every_part(make_screen, update_checker):
    update_checker.isUpdateAvailable.return_value = True
    update_checker.getLatestVersion.return_value = "0.13.0"
    screen = make_screen()
    screen.config.getVersion.return_value = "0.12.0-SNAPSHOT"

    screen.draw()

    screen.renderer.clearScreen.assert_called_once_with(palette.BLACK)
    texts = [args[0] for args in _calls(screen.renderer, "drawText")]
    assert texts == [
        "Roam",
        "Explore a procedurally-generated world",
        "W/S or Up/Down: navigate  -  Enter: Play  -  Esc: Quit",
        "Update available: v0.13.0  -  press U to download",
        "Roam v0.12.0-SNAPSHOT",
    ]
    labels = [args[7] for args in _calls(screen.renderer, "drawButton")]
    assert labels == MENU_LABELS
