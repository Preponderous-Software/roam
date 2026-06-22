import pygame
import pytest

from codex.codex import ALL_ENTITY_TYPES, ALL_LIVING_ENTITY_TYPES
from rendering.inputEvent import EventType, InputEvent
from screen.codexScreen import CodexScreen


@pytest.fixture
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


def createCodexScreen(pygame_init, resolve, test_graphik):
    display = pygame.Surface((800, 600))
    test_graphik.getGameDisplay.return_value = display
    return resolve(CodexScreen)


def test_initialization(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    assert screen.scrollOffset == 0
    assert screen.changeScreen is False


def test_switch_to_world_screen(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.switchToReturnScreen()
    assert screen.changeScreen is True
    assert screen.nextScreen == "world_screen"


def test_set_return_screen(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.setReturnScreen("options_screen")
    screen.switchToReturnScreen()
    assert screen.changeScreen is True
    assert screen.nextScreen == "options_screen"


def test_handle_escape_key(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.handleKeyDownEvent(pygame.K_ESCAPE)
    assert screen.changeScreen is True


def test_handle_scroll_event_down(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.handleScrollEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    assert screen.scrollOffset == 1


def test_handle_scroll_event_up(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.scrollOffset = 1
    screen.handleScrollEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=1))
    assert screen.scrollOffset == 0


def test_scroll_does_not_go_below_zero(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.handleScrollEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=1))
    assert screen.scrollOffset == 0


def test_all_living_entity_types_defined():
    assert "Bear" in ALL_LIVING_ENTITY_TYPES
    assert "Chicken" in ALL_LIVING_ENTITY_TYPES


def test_all_entity_types_includes_non_living():
    assert "Apple" in ALL_ENTITY_TYPES
    assert "Grass" in ALL_ENTITY_TYPES
    assert "Campfire" in ALL_ENTITY_TYPES
    assert len(ALL_ENTITY_TYPES) > len(ALL_LIVING_ENTITY_TYPES)


def test_codex_screen_shows_discovered(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.codex.discover("Bear")
    assert screen.codex.hasDiscovered("Bear") is True
    assert screen.codex.hasDiscovered("Chicken") is False
