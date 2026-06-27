import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
from unittest.mock import MagicMock

from config.config import Config
from config.keyBindings import KeyBindings
from entity.apple import Apple
from entity.chest import Chest
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.worldScreen import WorldScreen
from world.room import Room


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    import pygame

    pygame.init()
    yield
    pygame.quit()


def _makeRoom(gridSize=5):
    return Room("test", gridSize, (0, 0, 0), 0, 0, MagicMock())


def _makeWorldScreen(room=None):
    if room is None:
        room = _makeRoom()
    config = Config()
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.status = MagicMock()
    ws.keyBindings = KeyBindings()
    ws.tickCounter = MagicMock()
    ws.tickCounter.getTick.return_value = 0
    ws.currentRoom = room
    ws.cursorSlot = InventorySlot()
    ws.activeChest = None
    ws.activeChestRoom = None
    ws.nextScreen = ScreenType.WORLD_SCREEN
    ws.changeScreen = False

    inventory = Inventory()
    player = MagicMock()
    player.getInventory.return_value = inventory
    player.getGatherSpeed.return_value = 1
    player.getPlaceSpeed.return_value = 1
    player.getTickLastGathered.return_value = -999
    player.getTickLastPlaced.return_value = -999
    ws.player = player
    return ws


# --- executeGatherAtFront ---


def test_gather_at_front_no_location_sets_status():
    ws = _makeWorldScreen()
    ws.getLocationInFrontOfPlayer = lambda: -1
    # Both the facing tile and the player's own tile are absent.
    ws.getLocationOfPlayer = lambda: -1

    ws.executeGatherAtFront()

    ws.status.set.assert_called_with("Nothing to pick up here")


def test_gather_at_front_picks_up_item_in_front():
    room = _makeRoom(gridSize=5)
    ws = _makeWorldScreen(room)

    apple = Apple()
    centerLoc = room.getGrid().getLocationByCoordinates(2, 2)
    room.addEntityToLocation(apple, centerLoc)

    ws.getLocationInFrontOfPlayer = lambda: centerLoc
    ws._tryHarvestCrop = lambda loc, r: False

    ws.executeGatherAtFront()

    assert ws.player.getInventory().getNumItems() == 1
    ws.status.set.assert_called_with("Picked up " + apple.getName())


def test_gather_at_front_sets_nothing_to_pick_up_when_empty():
    room = _makeRoom(gridSize=5)
    ws = _makeWorldScreen(room)

    emptyLoc = room.getGrid().getLocationByCoordinates(2, 2)
    playerLoc = room.getGrid().getLocationByCoordinates(1, 1)
    ws.getLocationInFrontOfPlayer = lambda: emptyLoc
    # Player's own tile is also empty — final fallback shows nothing message.
    ws.getLocationOfPlayer = lambda: playerLoc
    ws._tryHarvestCrop = lambda loc, r: False

    ws.executeGatherAtFront()

    ws.status.set.assert_called_with("Nothing to pick up here")


def test_gather_at_front_falls_back_to_player_tile_when_facing_empty():
    room = _makeRoom(gridSize=5)
    ws = _makeWorldScreen(room)

    apple = Apple()
    playerLoc = room.getGrid().getLocationByCoordinates(1, 1)
    room.addEntityToLocation(apple, playerLoc)

    emptyFacingLoc = room.getGrid().getLocationByCoordinates(2, 2)
    ws.getLocationInFrontOfPlayer = lambda: emptyFacingLoc
    ws.getLocationOfPlayer = lambda: playerLoc
    ws._tryHarvestCrop = lambda loc, r: False

    ws.executeGatherAtFront()

    assert ws.player.getInventory().getNumItems() == 1
    ws.status.set.assert_called_with("Picked up " + apple.getName())


def test_gather_at_front_full_inventory_sets_status():
    room = _makeRoom(gridSize=5)
    ws = _makeWorldScreen(room)

    apple = Apple()
    loc = room.getGrid().getLocationByCoordinates(2, 2)
    room.addEntityToLocation(apple, loc)
    ws.getLocationInFrontOfPlayer = lambda: loc
    ws._tryHarvestCrop = lambda lo, r: False

    # Fill every slot to its max stack so the inventory rejects the next item
    inv = ws.player.getInventory()
    for slot in inv.getInventorySlots():
        for _ in range(slot.getMaxStackSize()):
            slot.add(Apple())

    ws.executeGatherAtFront()

    ws.status.set.assert_called_with("Inventory full")


# --- executePlaceAtFront ---


def test_place_at_front_no_location_sets_status():
    ws = _makeWorldScreen()
    ws.getLocationInFrontOfPlayer = lambda: -1

    ws.executePlaceAtFront()

    ws.status.set.assert_called_with("Cannot place here")


def test_place_at_front_no_items_sets_status():
    room = _makeRoom(gridSize=5)
    ws = _makeWorldScreen(room)

    loc = room.getGrid().getLocationByCoordinates(2, 2)
    ws.getLocationInFrontOfPlayer = lambda: loc

    ws.executePlaceAtFront()

    ws.status.set.assert_called_with("No items to place")


def test_place_at_front_places_item_in_front():
    room = _makeRoom(gridSize=5)
    ws = _makeWorldScreen(room)

    apple = Apple()
    inv = ws.player.getInventory()
    inv.placeIntoFirstAvailableInventorySlot(apple)
    inv.setSelectedInventorySlotIndex(0)

    loc = room.getGrid().getLocationByCoordinates(2, 2)
    ws.getLocationInFrontOfPlayer = lambda: loc
    ws.player.getInventory.return_value = inv

    ws.executePlaceAtFront()

    ws.status.set.assert_called_with("Placed " + apple.getName())
    assert apple in [loc.getEntity(eid) for eid in loc.getEntities()]


def test_place_at_front_opens_chest_in_front():
    room = _makeRoom(gridSize=5)
    ws = _makeWorldScreen(room)

    chest = Chest()
    loc = room.getGrid().getLocationByCoordinates(2, 2)
    room.addEntityToLocation(chest, loc)
    ws.getLocationInFrontOfPlayer = lambda: loc
    ws._openChest = MagicMock()

    ws.executePlaceAtFront()

    ws._openChest.assert_called_once_with(chest, room)


# --- G/F key wiring in _handleUtilityKey ---


def test_g_key_calls_executeGatherAtFront_when_off_cooldown():
    ws = _makeWorldScreen()
    ws.executeGatherAtFront = MagicMock()
    ws.checkPlayerGatherCooldown = lambda tick: True
    ws.player.getTickLastGathered.return_value = 0

    ws._handleUtilityKey(KeyCode.G, ws.keyBindings)

    ws.executeGatherAtFront.assert_called_once()


def test_g_key_does_not_gather_when_on_cooldown():
    ws = _makeWorldScreen()
    ws.executeGatherAtFront = MagicMock()
    ws.checkPlayerGatherCooldown = lambda tick: False
    ws.player.getTickLastGathered.return_value = 0

    ws._handleUtilityKey(KeyCode.G, ws.keyBindings)

    ws.executeGatherAtFront.assert_not_called()


def test_f_key_calls_executePlaceAtFront_when_off_cooldown():
    ws = _makeWorldScreen()
    ws.executePlaceAtFront = MagicMock()
    ws.checkPlayerPlaceCooldown = lambda tick: True
    ws.player.getTickLastPlaced.return_value = 0

    ws._handleUtilityKey(KeyCode.F, ws.keyBindings)

    ws.executePlaceAtFront.assert_called_once()


def test_f_key_does_not_place_when_on_cooldown():
    ws = _makeWorldScreen()
    ws.executePlaceAtFront = MagicMock()
    ws.checkPlayerPlaceCooldown = lambda tick: False
    ws.player.getTickLastPlaced.return_value = 0

    ws._handleUtilityKey(KeyCode.F, ws.keyBindings)

    ws.executePlaceAtFront.assert_not_called()
