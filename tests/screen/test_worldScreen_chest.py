import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock

from entity.apple import Apple
from entity.chest import Chest
from inventory.inventorySlot import InventorySlot
from screen.screenType import ScreenType
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
    graphik = MagicMock()
    status = MagicMock()
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.graphik = graphik
    ws.status = status
    ws.cursorSlot = InventorySlot()
    ws.player = MagicMock()
    ws.activeChest = None
    ws.activeChestRoom = None
    ws.nextScreen = ScreenType.WORLD_SCREEN
    ws.changeScreen = False
    return ws


def createMockRoom(gridSize=3, x=0, y=0):
    graphik = MagicMock()
    return Room("test", gridSize, (0, 0, 0), x, y, graphik)


def test_open_chest_sets_active_chest_and_requests_chest_screen():
    ws = createWorldScreen()
    room = createMockRoom()
    chest = Chest()

    ws._openChest(chest, room)

    assert ws.getActiveChest() is chest
    assert ws.activeChestRoom is room
    assert ws.nextScreen == ScreenType.CHEST_SCREEN
    assert ws.changeScreen is True


def test_open_chest_returns_cursor_items_to_player_first():
    ws = createWorldScreen()
    from inventory.inventory import Inventory

    inventory = Inventory()
    ws.player.getInventory.return_value = inventory
    ws.cursorSlot.add(Apple())

    ws._openChest(Chest(), createMockRoom())

    assert ws.cursorSlot.isEmpty()
    assert inventory.getNumItems() == 1


def test_save_active_chest_room_persists_the_room_async():
    ws = createWorldScreen()
    room = createMockRoom()
    ws.activeChestRoom = room
    ws.saveRoomToFileAsync = MagicMock()

    ws.saveActiveChestRoom()

    ws.saveRoomToFileAsync.assert_called_once_with(room)


def test_save_active_chest_room_is_noop_when_no_chest_room():
    ws = createWorldScreen()
    ws.activeChestRoom = None
    ws.saveRoomToFileAsync = MagicMock()

    ws.saveActiveChestRoom()

    ws.saveRoomToFileAsync.assert_not_called()


def test_gather_on_non_empty_chest_advises_emptying_it_first():
    ws = createWorldScreen()
    room = createMockRoom()
    loc = room.getGrid().getLocationByCoordinates(1, 1)
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    room.addEntityToLocation(chest, loc)

    ws.getLocationAndRoomAtMousePosition = lambda: (loc, room)
    ws.isLocationTooFar = lambda location, targetRoom: False
    ws._tryHarvestCrop = lambda location, targetRoom: False

    ws.executeGatherAction()

    ws.status.set.assert_called_with("Empty the chest before picking it up")


def test_gather_on_empty_location_still_reports_nothing_to_pick_up():
    ws = createWorldScreen()
    room = createMockRoom()
    loc = room.getGrid().getLocationByCoordinates(1, 1)

    ws.getLocationAndRoomAtMousePosition = lambda: (loc, room)
    ws.isLocationTooFar = lambda location, targetRoom: False
    ws._tryHarvestCrop = lambda location, targetRoom: False

    ws.executeGatherAction()

    ws.status.set.assert_called_with("Nothing to pick up here")
