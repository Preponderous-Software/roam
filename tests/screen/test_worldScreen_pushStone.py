import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock

from entity.stone import Stone
from entity.oakWood import OakWood
from lib.pyenvlib.location import Location
from lib.pyenvlib.grid import Grid


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def createWorldScreen():
    from config.config import Config
    from screen.worldScreen import WorldScreen

    config = Config()
    gameDisplay = pygame.display.set_mode((800, 600))
    graphik = MagicMock()
    graphik.getGameDisplay.return_value = gameDisplay
    status = MagicMock()
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.graphik = graphik
    ws.status = status
    return ws


def test_tryPushStone_success():
    ws = createWorldScreen()
    ws.config.pushableStone = True

    grid = Grid(3, 1)
    loc0 = grid.getLocationByCoordinates(0, 0)
    loc1 = grid.getLocationByCoordinates(1, 0)
    loc2 = grid.getLocationByCoordinates(2, 0)

    stone = Stone()
    loc1.addEntity(stone)

    room = MagicMock()
    room.getGrid.return_value = grid
    ws.currentRoom = room

    # push stone to the right (direction 3)
    result = ws.tryPushStone(loc1, 3)

    assert result == True
    assert not loc1.isEntityPresent(stone)
    assert loc2.isEntityPresent(stone)


def test_tryPushStone_blocked_by_solid():
    ws = createWorldScreen()
    ws.config.pushableStone = True

    grid = Grid(3, 1)
    loc1 = grid.getLocationByCoordinates(1, 0)
    loc2 = grid.getLocationByCoordinates(2, 0)

    stone = Stone()
    loc1.addEntity(stone)

    blocker = OakWood()
    loc2.addEntity(blocker)

    room = MagicMock()
    room.getGrid.return_value = grid
    ws.currentRoom = room

    # push stone to the right but destination is blocked
    result = ws.tryPushStone(loc1, 3)

    assert result == False
    assert loc1.isEntityPresent(stone)
    assert loc2.isEntityPresent(blocker)


def test_tryPushStone_at_border():
    ws = createWorldScreen()
    ws.config.pushableStone = True

    grid = Grid(2, 1)
    loc1 = grid.getLocationByCoordinates(1, 0)

    stone = Stone()
    loc1.addEntity(stone)

    room = MagicMock()
    room.getGrid.return_value = grid
    ws.currentRoom = room

    # push stone to the right but it's at the border
    result = ws.tryPushStone(loc1, 3)

    assert result == False
    assert loc1.isEntityPresent(stone)


def test_tryPushStone_no_stone():
    ws = createWorldScreen()
    ws.config.pushableStone = True

    grid = Grid(3, 1)
    loc1 = grid.getLocationByCoordinates(1, 0)

    # add a non-stone solid entity
    wood = OakWood()
    loc1.addEntity(wood)

    room = MagicMock()
    room.getGrid.return_value = grid
    ws.currentRoom = room

    # tryPushStone should fail because there's no Stone
    result = ws.tryPushStone(loc1, 3)

    assert result == False
    assert loc1.isEntityPresent(wood)
