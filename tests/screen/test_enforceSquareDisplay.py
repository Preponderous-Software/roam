import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from lib.graphik.src.graphik import Graphik


def test_enforceSquareDisplay_calls_set_mode_when_not_square():
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (800, 600)
    graphik = Graphik(gameDisplay)
    newDisplay = MagicMock()
    with patch.object(pygame.display, "set_mode", return_value=newDisplay) as mock_set_mode:
        graphik.enforceSquareDisplay()
        mock_set_mode.assert_called_once_with((600, 600), pygame.RESIZABLE)
        assert graphik.getGameDisplay() == newDisplay


def test_enforceSquareDisplay_uses_height_as_dimension():
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (1000, 600)
    graphik = Graphik(gameDisplay)
    newDisplay = MagicMock()
    with patch.object(pygame.display, "set_mode", return_value=newDisplay) as mock_set_mode:
        graphik.enforceSquareDisplay()
        mock_set_mode.assert_called_once_with((600, 600), pygame.RESIZABLE)
        assert graphik.getGameDisplay() == newDisplay


def test_enforceSquareDisplay_does_not_change_already_square_display():
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (500, 500)
    graphik = Graphik(gameDisplay)
    with patch.object(pygame.display, "set_mode") as mock_set_mode:
        graphik.enforceSquareDisplay()
        mock_set_mode.assert_not_called()
        assert graphik.getGameDisplay() == gameDisplay
