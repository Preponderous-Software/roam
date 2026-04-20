import pytest
from unittest.mock import MagicMock

from services.inventoryService import InventoryService
from config.config import Config
from player.player import Player
from stats.stats import Stats
from ui.status import Status
from world.tickCounter import TickCounter
from inventory.inventory import Inventory
from entity.apple import Apple


def makeService():
    config = MagicMock(spec=Config)
    player = MagicMock(spec=Player)
    inventory = Inventory()
    player.getInventory.return_value = inventory
    player.needsEnergy.return_value = True
    player.canEat.side_effect = lambda e: isinstance(e, Apple)
    stats = MagicMock(spec=Stats)
    status = MagicMock(spec=Status)
    tickCounter = MagicMock(spec=TickCounter)
    tickCounter.getTick.return_value = 100
    service = InventoryService(config, player, stats, status, tickCounter)
    return service, player, inventory, stats, status


def test_eatFoodInInventory_eats_apple():
    service, player, inventory, stats, status = makeService()
    apple = Apple()
    inventory.placeIntoFirstAvailableInventorySlot(apple)
    service.eatFoodInInventory()
    player.addEnergy.assert_called_once_with(apple.getEnergy())
    stats.incrementFoodEaten.assert_called_once()
    stats.incrementScore.assert_called_once()


def test_eatFoodInInventory_empty_inventory():
    service, player, inventory, stats, status = makeService()
    service.eatFoodInInventory()
    player.addEnergy.assert_not_called()


def test_changeSelectedInventorySlot_updates_index():
    service, player, inventory, stats, status = makeService()
    service.changeSelectedInventorySlot(3)
    assert inventory.getSelectedInventorySlotIndex() == 3


def test_changeSelectedInventorySlot_empty_slot_sets_status():
    service, player, inventory, stats, status = makeService()
    service.changeSelectedInventorySlot(0)
    status.set.assert_called_with("Empty slot")


def test_changeSelectedInventorySlot_nonempty_slot_sets_status():
    service, player, inventory, stats, status = makeService()
    apple = Apple()
    inventory.placeIntoFirstAvailableInventorySlot(apple)
    service.changeSelectedInventorySlot(0)
    status.set.assert_called_with("Selected Apple")
