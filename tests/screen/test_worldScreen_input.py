import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from config.keyBindings import KeyBindings
from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.worldScreen import WorldScreen


# Characterization tests for the WorldScreen input seam (epic #433, Phase 4c):
# its game loop now reads InputEvents from an InputSource instead of pygame.
# The real-time loop itself still needs a maintainer smoke-run; these lock in
# the event-dispatch wiring that is testable headless.


class _FakeInputSource:
    def __init__(self, *events):
        self._events = list(events)

    def pollEvents(self):
        events, self._events = self._events, []
        return events


def _bareWorldScreen(*events):
    ws = WorldScreen.__new__(WorldScreen)
    ws.inputSource = _FakeInputSource(*events)
    ws.nextScreen = ScreenType.WORLD_SCREEN
    ws.changeScreen = False
    ws.showHelp = False
    ws.keyBindings = KeyBindings()
    return ws


def test_process_events_polls_the_input_source_and_quits_on_quit_event():
    ws = _bareWorldScreen(InputEvent(EventType.QUIT))
    ws.printStatsToConsole = lambda: None

    ws._processEvents()

    assert ws.nextScreen == ScreenType.NONE
    assert ws.changeScreen is True


def test_process_events_dispatches_key_down_to_handler():
    ws = _bareWorldScreen(InputEvent(EventType.KEY_DOWN, key=KeyCode.U))
    captured = {}
    ws.handleKeyDownEvent = lambda key: captured.setdefault("key", key)

    ws._processEvents()

    assert captured["key"] is KeyCode.U


def test_process_events_dispatches_mouse_wheel_with_scroll():
    ws = _bareWorldScreen(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    captured = {}
    ws.handleMouseWheelEvent = lambda event: captured.setdefault(
        "scrollY", event.scrollY
    )

    ws._processEvents()

    assert captured["scrollY"] == -1


def test_escape_key_opens_the_options_menu():
    ws = _bareWorldScreen()

    ws.handleKeyDownEvent(KeyCode.ESCAPE)

    assert ws.nextScreen == ScreenType.OPTIONS_SCREEN
    assert ws.changeScreen is True


def test_escape_key_dismisses_the_help_overlay_first():
    ws = _bareWorldScreen()
    ws.showHelp = True

    ws.handleKeyDownEvent(KeyCode.ESCAPE)

    # First Esc closes help; it does not also leave the world.
    assert ws.showHelp is False
    assert ws.changeScreen is False
