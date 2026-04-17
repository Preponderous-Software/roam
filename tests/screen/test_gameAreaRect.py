import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from unittest.mock import MagicMock

from lib.graphik.src.graphik import Graphik


def test_getGameAreaRect_returns_centered_square_for_wide_display():
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (1000, 600)
    graphik = Graphik(gameDisplay)
    rect = graphik.getGameAreaRect()
    assert rect.width == 600
    assert rect.height == 600
    assert rect.x == 200
    assert rect.y == 0


def test_getGameAreaRect_returns_centered_square_for_tall_display():
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (600, 1000)
    graphik = Graphik(gameDisplay)
    rect = graphik.getGameAreaRect()
    assert rect.width == 600
    assert rect.height == 600
    assert rect.x == 0
    assert rect.y == 200


def test_getGameAreaRect_returns_full_area_for_square_display():
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (500, 500)
    graphik = Graphik(gameDisplay)
    rect = graphik.getGameAreaRect()
    assert rect.width == 500
    assert rect.height == 500
    assert rect.x == 0
    assert rect.y == 0
