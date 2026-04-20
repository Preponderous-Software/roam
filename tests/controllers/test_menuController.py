import pytest
from unittest.mock import MagicMock

from controllers.menuController import MenuController
from screen.screenType import ScreenType
import pygame


@pytest.fixture(autouse=True)
def init_pygame():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    yield
    pygame.quit()


def makeController():
    return MenuController()


def test_initial_state():
    c = makeController()
    assert not c.shouldChangeScreen()
    assert c.getNextScreen() == ScreenType.SAVE_SELECTION_SCREEN


def test_navigateTo_sets_next_screen():
    c = makeController()
    c.navigateTo(ScreenType.WORLD_SCREEN)
    assert c.getNextScreen() == ScreenType.WORLD_SCREEN
    assert c.shouldChangeScreen()


def test_resetChangeScreen():
    c = makeController()
    c.navigateTo(ScreenType.WORLD_SCREEN)
    c.resetChangeScreen()
    assert not c.shouldChangeScreen()


def test_handleKeyDownEvent_navigates_on_non_escape():
    c = makeController()
    c.handleKeyDownEvent(pygame.K_RETURN)
    assert c.shouldChangeScreen()
    assert c.getNextScreen() == ScreenType.SAVE_SELECTION_SCREEN
