import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock, patch

from entity.apple import Apple
from entity.gravestone import Gravestone
from entity.oakWood import OakWood
from inventory.inventory import Inventory
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


def createMockRoom(gridSize=3, x=0, y=0):
    graphik = MagicMock()
    return Room("test", gridSize, (0, 0, 0), x, y, graphik)


# ---------------------------------------------------------------------------
# respawnPlayer — gravestone spawning on death
# ---------------------------------------------------------------------------


def test_respawnPlayer_spawns_gravestone_with_items():
    ws = createWorldScreen()
    room = createMockRoom()
    ws.currentRoom = room

    # Give player an item
    player = MagicMock()
    inventory = Inventory()
    inventory.placeIntoFirstAvailableInventorySlot(Apple())
    player.getInventory.return_value = inventory
    ws.player = player

    # Locate player at grid position (1, 1)
    loc = room.getGrid().getLocationByCoordinates(1, 1)
    player.getLocationID.return_value = loc.getID()

    respawn_room = createMockRoom()
    ws.map = MagicMock()
    ws.map.getRoom.return_value = respawn_room
    ws.tickCounter = MagicMock()
    ws.tickCounter.getTick.return_value = 0
    ws.save = MagicMock()

    ws.respawnPlayer()

    # Gravestone should be at player's original location
    gravestones = [
        room.getGrid().getLocation(lid).getEntity(eid)
        for lid in room.getGrid().getLocations()
        for eid in room.getGrid().getLocation(lid).getEntities()
    ]
    gravestone_entities = [e for e in gravestones if isinstance(e, Gravestone)]
    assert len(gravestone_entities) == 1
    assert gravestone_entities[0].getStoredInventory().getNumItems() == 1


def test_respawnPlayer_clears_player_inventory():
    ws = createWorldScreen()
    room = createMockRoom()
    ws.currentRoom = room

    player = MagicMock()
    inventory = Inventory()
    inventory.placeIntoFirstAvailableInventorySlot(Apple())
    player.getInventory.return_value = inventory
    ws.player = player

    loc = room.getGrid().getLocationByCoordinates(1, 1)
    player.getLocationID.return_value = loc.getID()

    respawn_room = createMockRoom()
    ws.map = MagicMock()
    ws.map.getRoom.return_value = respawn_room
    ws.tickCounter = MagicMock()
    ws.tickCounter.getTick.return_value = 0
    ws.save = MagicMock()

    ws.respawnPlayer()

    assert inventory.getNumItems() == 0


def test_respawnPlayer_no_gravestone_when_inventory_empty():
    ws = createWorldScreen()
    room = createMockRoom()
    ws.currentRoom = room

    player = MagicMock()
    inventory = Inventory()  # empty
    player.getInventory.return_value = inventory
    ws.player = player

    loc = room.getGrid().getLocationByCoordinates(1, 1)
    player.getLocationID.return_value = loc.getID()

    respawn_room = createMockRoom()
    ws.map = MagicMock()
    ws.map.getRoom.return_value = respawn_room
    ws.tickCounter = MagicMock()
    ws.tickCounter.getTick.return_value = 0
    ws.save = MagicMock()

    ws.respawnPlayer()

    all_entities = [
        room.getGrid().getLocation(lid).getEntity(eid)
        for lid in room.getGrid().getLocations()
        for eid in room.getGrid().getLocation(lid).getEntities()
    ]
    gravestone_entities = [e for e in all_entities if isinstance(e, Gravestone)]
    assert len(gravestone_entities) == 0


# ---------------------------------------------------------------------------
# _interactWithGravestone — item retrieval
# ---------------------------------------------------------------------------


def test_interact_with_gravestone_transfers_items_to_player():
    ws = createWorldScreen()
    room = createMockRoom()
    ws.currentRoom = room

    player = MagicMock()
    inventory = Inventory()
    player.getInventory.return_value = inventory
    ws.player = player

    gravestone = Gravestone()
    apple = Apple()
    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(apple)

    loc = room.getGrid().getLocationByCoordinates(1, 1)
    room.addEntityToLocation(gravestone, loc)

    ws._interactWithGravestone(gravestone, room, loc)

    assert inventory.getNumItems() == 1
    assert not loc.isEntityPresent(gravestone)
    ws.status.set.assert_called_with("Retrieved items from Gravestone")


def test_interact_with_gravestone_full_inventory_leaves_gravestone():
    ws = createWorldScreen()
    room = createMockRoom()
    ws.currentRoom = room

    player = MagicMock()
    # Fill the inventory completely
    inventory = Inventory()
    for _ in range(inventory.getNumInventorySlots()):
        slot_apple = Apple()
        for slot in inventory.getInventorySlots():
            if slot.isEmpty():
                slot.add(slot_apple)
                break
    # Set all slots to max stack so nothing can be added
    for slot in inventory.getInventorySlots():
        while slot.getNumItems() < slot.getMaxStackSize():
            slot.add(Apple())
    player.getInventory.return_value = inventory
    ws.player = player

    gravestone = Gravestone()
    oak = OakWood()
    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(oak)

    loc = room.getGrid().getLocationByCoordinates(1, 1)
    room.addEntityToLocation(gravestone, loc)

    ws._interactWithGravestone(gravestone, room, loc)

    # Gravestone should still be in place
    assert loc.isEntityPresent(gravestone)
    ws.status.set.assert_called_with("Inventory full")
