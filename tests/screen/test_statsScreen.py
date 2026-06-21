from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.statsScreen import StatsScreen

# Characterization tests for StatsScreen (previously no dedicated test file):
# the Esc/screenshot key handling and a headless smoke of the stats/goals draw
# path through the (mocked) renderer.


def test_escape_returns_to_options(resolve):
    screen = resolve(StatsScreen)

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    assert screen.nextScreen == ScreenType.OPTIONS_SCREEN
    assert screen.changeScreen is True


def test_switch_to_options_sets_transition(resolve):
    screen = resolve(StatsScreen)

    screen.switchToOptionsScreen()

    assert screen.nextScreen == ScreenType.OPTIONS_SCREEN
    assert screen.changeScreen is True


def test_screenshot_key_captures_a_screenshot(resolve):
    screen = resolve(StatsScreen)
    screenshotKey = screen.keyBindings.getKey("screenshot")

    screen.handleKeyDownEvent(screenshotKey)

    screen.renderer.captureScreenshot.assert_called_once()
    # Capturing a screenshot must not navigate away from the stats screen.
    assert screen.changeScreen is False


def test_draw_runs_through_the_stats_and_goals_path(resolve):
    # Headless smoke: the full stats/goals draw path must run without raising
    # against the renderer interface (drawStats + drawGoals + back button).
    screen = resolve(StatsScreen)

    screen.draw()

    screen.renderer.clearScreen.assert_called()
    assert screen.renderer.drawText.called
