from rendering.keyCode import KeyCode
from screen.mainMenuScreen import MainMenuScreen
from screen.screenType import ScreenType

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
