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
from world.room import Room


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


def createMockRoom(gridSize, x=0, y=0):
    graphik = MagicMock()
    room = Room("test", gridSize, (0, 0, 0), x, y, graphik)
    return room


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


def test_tryPushStone_cross_room_right():
    ws = createWorldScreen()
    ws.config.pushableStone = True
    ws.config.gridSize = 3
    ws.config.worldBorder = 0

    currentRoom = createMockRoom(3, x=0, y=0)
    adjacentRoom = createMockRoom(3, x=1, y=0)
    ws.currentRoom = currentRoom

    # mock getOrLoadRoom to return the adjacent room
    ws.getOrLoadRoom = MagicMock(return_value=adjacentRoom)

    # place stone at rightmost column (border)
    loc = currentRoom.getGrid().getLocationByCoordinates(2, 0)
    stone = Stone()
    loc.addEntity(stone)

    # push right (direction 3) - should cross into adjacent room
    result = ws.tryPushStone(loc, 3)

    assert result == True
    assert not loc.isEntityPresent(stone)
    ws.getOrLoadRoom.assert_called_once_with(1, 0)
    # stone should be at x=0 (left side) of adjacent room, same y
    targetLoc = adjacentRoom.getGrid().getLocationByCoordinates(0, 0)
    assert targetLoc.isEntityPresent(stone)


def test_tryPushStone_cross_room_left():
    ws = createWorldScreen()
    ws.config.pushableStone = True
    ws.config.gridSize = 3
    ws.config.worldBorder = 0

    currentRoom = createMockRoom(3, x=0, y=0)
    adjacentRoom = createMockRoom(3, x=-1, y=0)
    ws.currentRoom = currentRoom

    ws.getOrLoadRoom = MagicMock(return_value=adjacentRoom)

    loc = currentRoom.getGrid().getLocationByCoordinates(0, 1)
    stone = Stone()
    loc.addEntity(stone)

    # push left (direction 1)
    result = ws.tryPushStone(loc, 1)

    assert result == True
    assert not loc.isEntityPresent(stone)
    ws.getOrLoadRoom.assert_called_once_with(-1, 0)
    targetLoc = adjacentRoom.getGrid().getLocationByCoordinates(2, 1)
    assert targetLoc.isEntityPresent(stone)


def test_tryPushStone_cross_room_up():
    ws = createWorldScreen()
    ws.config.pushableStone = True
    ws.config.gridSize = 3
    ws.config.worldBorder = 0

    currentRoom = createMockRoom(3, x=0, y=0)
    adjacentRoom = createMockRoom(3, x=0, y=-1)
    ws.currentRoom = currentRoom

    ws.getOrLoadRoom = MagicMock(return_value=adjacentRoom)

    loc = currentRoom.getGrid().getLocationByCoordinates(1, 0)
    stone = Stone()
    loc.addEntity(stone)

    # push up (direction 0)
    result = ws.tryPushStone(loc, 0)

    assert result == True
    assert not loc.isEntityPresent(stone)
    ws.getOrLoadRoom.assert_called_once_with(0, -1)
    targetLoc = adjacentRoom.getGrid().getLocationByCoordinates(1, 2)
    assert targetLoc.isEntityPresent(stone)


def test_tryPushStone_cross_room_down():
    ws = createWorldScreen()
    ws.config.pushableStone = True
    ws.config.gridSize = 3
    ws.config.worldBorder = 0

    currentRoom = createMockRoom(3, x=0, y=0)
    adjacentRoom = createMockRoom(3, x=0, y=1)
    ws.currentRoom = currentRoom

    ws.getOrLoadRoom = MagicMock(return_value=adjacentRoom)

    loc = currentRoom.getGrid().getLocationByCoordinates(1, 2)
    stone = Stone()
    loc.addEntity(stone)

    # push down (direction 2)
    result = ws.tryPushStone(loc, 2)

    assert result == True
    assert not loc.isEntityPresent(stone)
    ws.getOrLoadRoom.assert_called_once_with(0, 1)
    targetLoc = adjacentRoom.getGrid().getLocationByCoordinates(1, 0)
    assert targetLoc.isEntityPresent(stone)


def test_tryPushStone_cross_room_blocked_by_solid():
    ws = createWorldScreen()
    ws.config.pushableStone = True
    ws.config.gridSize = 3
    ws.config.worldBorder = 0

    currentRoom = createMockRoom(3, x=0, y=0)
    adjacentRoom = createMockRoom(3, x=1, y=0)
    ws.currentRoom = currentRoom

    ws.getOrLoadRoom = MagicMock(return_value=adjacentRoom)

    loc = currentRoom.getGrid().getLocationByCoordinates(2, 0)
    stone = Stone()
    loc.addEntity(stone)

    # place a blocker in the adjacent room's entry location
    targetLoc = adjacentRoom.getGrid().getLocationByCoordinates(0, 0)
    blocker = OakWood()
    targetLoc.addEntity(blocker)

    # push right (direction 3) - should fail because destination is blocked
    result = ws.tryPushStone(loc, 3)

    assert result == False
    assert loc.isEntityPresent(stone)
    assert targetLoc.isEntityPresent(blocker)


def test_tryPushStone_cross_room_blocked_by_world_border():
    ws = createWorldScreen()
    ws.config.pushableStone = True
    ws.config.gridSize = 3
    ws.config.worldBorder = 1

    currentRoom = createMockRoom(3, x=1, y=0)
    ws.currentRoom = currentRoom

    loc = currentRoom.getGrid().getLocationByCoordinates(2, 0)
    stone = Stone()
    loc.addEntity(stone)

    # push right (direction 3) - adjacent room would be at x=2 which exceeds world border of 1
    result = ws.tryPushStone(loc, 3)

    assert result == False
    assert loc.isEntityPresent(stone)
