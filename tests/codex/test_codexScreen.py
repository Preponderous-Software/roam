import pygame
import pytest
from unittest.mock import MagicMock

from src.codex.codex import Codex, ALL_LIVING_ENTITY_TYPES
from src.screen.codexScreen import CodexScreen


@pytest.fixture
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


def createCodexScreen(pygame_init):
    display = pygame.Surface((800, 600))
    graphik = MagicMock()
    graphik.getGameDisplay.return_value = display
    config = MagicMock()
    codex = Codex()
    screen = CodexScreen(graphik, config, codex)
    return screen


def test_initialization(pygame_init):
    screen = createCodexScreen(pygame_init)
    assert screen.scrollOffset == 0
    assert screen.changeScreen is False


def test_switch_to_world_screen(pygame_init):
    screen = createCodexScreen(pygame_init)
    screen.switchToWorldScreen()
    assert screen.changeScreen is True
    assert screen.nextScreen == "world_screen"


def test_handle_escape_key(pygame_init):
    screen = createCodexScreen(pygame_init)
    screen.handleKeyDownEvent(pygame.K_ESCAPE)
    assert screen.changeScreen is True


def test_handle_scroll_event_down(pygame_init):
    screen = createCodexScreen(pygame_init)
    event = MagicMock()
    event.y = -1
    screen.handleScrollEvent(event)
    assert screen.scrollOffset == 1


def test_handle_scroll_event_up(pygame_init):
    screen = createCodexScreen(pygame_init)
    screen.scrollOffset = 1
    event = MagicMock()
    event.y = 1
    screen.handleScrollEvent(event)
    assert screen.scrollOffset == 0


def test_scroll_does_not_go_below_zero(pygame_init):
    screen = createCodexScreen(pygame_init)
    event = MagicMock()
    event.y = 1
    screen.handleScrollEvent(event)
    assert screen.scrollOffset == 0


def test_all_living_entity_types_defined():
    assert "Bear" in ALL_LIVING_ENTITY_TYPES
    assert "Chicken" in ALL_LIVING_ENTITY_TYPES


def test_codex_screen_shows_discovered(pygame_init):
    screen = createCodexScreen(pygame_init)
    screen.codex.discover("Bear")
    assert screen.codex.hasDiscovered("Bear") is True
    assert screen.codex.hasDiscovered("Chicken") is False
