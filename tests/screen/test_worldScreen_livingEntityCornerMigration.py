import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock

from entity.living.chicken import Chicken
from lib.pyenvlib.grid import Grid
from world.room import Room


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def createWorldScreen(gridSize=3):
    from config.config import Config
    from screen.worldScreen import WorldScreen

    config = Config()
    config.gridSize = gridSize
    gameDisplay = pygame.display.set_mode((800, 600))
    graphik = MagicMock()
    graphik.getGameDisplay.return_value = gameDisplay
    status = MagicMock()
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.graphik = graphik
    ws.status = status
    return ws


def createRoom(gridSize, x=0, y=0):
    graphik = MagicMock()
    return Room("test", gridSize, (0, 0, 0), x, y, graphik)


def placeChickenAt(room, x, y):
    chicken = Chicken(tickCreated=0)
    location = room.getGrid().getLocationByCoordinates(x, y)
    location.addEntity(chicken)
    return chicken


@pytest.mark.parametrize(
    "cornerX,cornerY,expectedRoomX,expectedRoomY",
    [
        (0, 0, -1, 0),
        (2, 0, 1, 0),
        (0, 2, -1, 0),
        (2, 2, 1, 0),
    ],
)
def test_getCoordinatesForNewRoomBasedOnLivingEntityLocation_corner_does_not_raise(
    cornerX, cornerY, expectedRoomX, expectedRoomY
):
    ws = createWorldScreen(gridSize=3)
    room = createRoom(3, x=0, y=0)
    ws.currentRoom = room
    chicken = placeChickenAt(room, cornerX, cornerY)

    x, y = ws.getCoordinatesForNewRoomBasedOnLivingEntityLocation(chicken)

    assert (x, y) == (expectedRoomX, expectedRoomY)


@pytest.mark.parametrize(
    "cornerX,cornerY,expectedLocX,expectedLocY",
    [
        (0, 0, 2, 0),
        (2, 0, 0, 0),
        (0, 2, 2, 2),
        (2, 2, 0, 2),
    ],
)
def test_getNewLocationCoordinatesForLivingEntityBasedOnLocation_corner_does_not_raise(
    cornerX, cornerY, expectedLocX, expectedLocY
):
    ws = createWorldScreen(gridSize=3)
    room = createRoom(3, x=0, y=0)
    ws.currentRoom = room
    location = room.getGrid().getLocationByCoordinates(cornerX, cornerY)

    x, y = ws.getNewLocationCoordinatesForLivingEntityBasedOnLocation(location)

    assert (x, y) == (expectedLocX, expectedLocY)


def test_updateLivingEntities_migrates_entity_from_corner():
    ws = createWorldScreen(gridSize=3)
    ws.config.debug = False

    currentRoom = createRoom(3, x=0, y=0)
    adjacentRoom = createRoom(3, x=-1, y=0)
    ws.currentRoom = currentRoom

    chicken = placeChickenAt(currentRoom, 0, 0)
    currentRoom.addLivingEntity(chicken)

    currentRoom.moveLivingEntities = MagicMock(return_value=[chicken])
    ws._loadOrGenerateRoom = MagicMock(return_value=adjacentRoom)
    ws.saveRoomToFileAsync = MagicMock()
    ws.tickCounter = MagicMock()
    ws.tickCounter.getTick.return_value = 0

    ws._updateLivingEntities()

    ws._loadOrGenerateRoom.assert_called_once_with(-1, 0, updateStats=False)
    assert (
        not currentRoom.getGrid()
        .getLocationByCoordinates(0, 0)
        .isEntityPresent(chicken)
    )
    newLocation = adjacentRoom.getGrid().getLocationByCoordinates(2, 0)
    assert newLocation.isEntityPresent(chicken)
    assert chicken.getID() in adjacentRoom.getLivingEntities()
