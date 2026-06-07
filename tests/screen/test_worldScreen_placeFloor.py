import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock

from entity.woodFloor import WoodFloor
from entity.stoneFloor import StoneFloor
from inventory.inventory import Inventory
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
    pygame.display.set_mode((800, 600))
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.status = MagicMock()
    ws.tickCounter = MagicMock()
    ws.isLocationTooFar = MagicMock(return_value=False)
    return ws


def createRoom(gridSize=3):
    return Room("test", gridSize, (0, 0, 0), 0, 0, MagicMock())


def _floorCounts(location):
    counts = {"WoodFloor": 0, "StoneFloor": 0}
    for entityId in list(location.getEntities().keys()):
        name = type(location.getEntity(entityId)).__name__
        if name in counts:
            counts[name] += 1
    return counts


def _placeFloorAt(selectedFloor, location, room):
    ws = createWorldScreen()
    ws.currentRoom = room

    player = MagicMock()
    inventory = Inventory()
    inventory.placeIntoFirstAvailableInventorySlot(selectedFloor)
    player.getInventory.return_value = inventory
    ws.player = player

    ws.getLocationAndRoomAtMousePosition = MagicMock(return_value=(location, room))
    ws.executePlaceAction()
    return ws, inventory


def test_placing_floor_on_existing_floor_is_blocked():
    room = createRoom()
    location = room.getGrid().getLocationByCoordinates(1, 1)
    room.addEntityToLocation(WoodFloor(), location)  # a floor is already here

    ws, inventory = _placeFloorAt(StoneFloor(), location, room)

    # The StoneFloor was not added; only the original WoodFloor remains.
    assert _floorCounts(location) == {"WoodFloor": 1, "StoneFloor": 0}
    # The item was not consumed.
    assert inventory.getNumTakenInventorySlots() == 1
    ws.status.set.assert_called_with("A floor is already here")


def test_placing_floor_on_empty_location_succeeds():
    room = createRoom()
    location = room.getGrid().getLocationByCoordinates(1, 1)

    ws, inventory = _placeFloorAt(WoodFloor(), location, room)

    # The WoodFloor was placed and the item consumed.
    assert _floorCounts(location) == {"WoodFloor": 1, "StoneFloor": 0}
    assert inventory.getNumTakenInventorySlots() == 0
    ws.status.set.assert_called_with("Placed Wood Floor")
