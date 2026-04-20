import pytest
from unittest.mock import MagicMock

from controllers.inventoryController import InventoryController
from services.craftingService import CraftingService
from config.config import Config
from config.keyBindings import KeyBindings
from player.player import Player
from ui.status import Status
from lib.graphik.src.graphik import Graphik
from inventory.inventory import Inventory
from entity.oakWood import OakWood


def makeController():
    graphik = MagicMock(spec=Graphik)
    display = MagicMock()
    display.get_width.return_value = 800
    display.get_height.return_value = 600
    display.get_size.return_value = (800, 600)
    graphik.getGameDisplay.return_value = display
    config = MagicMock(spec=Config)
    inventory = Inventory()
    player = MagicMock(spec=Player)
    player.getInventory.return_value = inventory
    status = MagicMock(spec=Status)
    keyBindings = KeyBindings()
    craftingService = MagicMock(spec=CraftingService)
    controller = InventoryController(graphik, config, player, status, keyBindings, craftingService)
    return controller, player, inventory, craftingService


def test_getInventory_returns_player_inventory():
    controller, player, inventory, _ = makeController()
    assert controller.getInventory() is inventory


def test_swapCursorSlotWithInventorySlotByIndex_moves_item():
    controller, _, inventory, _ = makeController()
    item = OakWood()
    inventory.placeIntoFirstAvailableInventorySlot(item)
    # swap cursor (empty) with slot 0 (has item)
    controller.swapCursorSlotWithInventorySlotByIndex(0)
    assert not controller.cursorSlot.isEmpty()
    assert inventory.getInventorySlots()[0].isEmpty()


def test_toggleCraftPanel_toggles():
    controller, _, _, _ = makeController()
    assert not controller.craftPanelOpen
    controller.lastCraftToggleTime = 0  # reset debounce
    controller.toggleCraftPanel()
    assert controller.craftPanelOpen


def test_craftRecipe_delegates_to_service():
    controller, _, inventory, craftingService = makeController()
    recipe = MagicMock()
    controller.craftRecipe(recipe)
    craftingService.craftRecipe.assert_called_once_with(recipe, inventory)


def test_handleMouseClickEvent_outside_clears_cursor():
    controller, _, inventory, _ = makeController()
    item = OakWood()
    controller.cursorSlot.add(item)
    # click outside at (10, 10) with left button
    controller.handleMouseClickEvent((10, 10), button=1)
    assert controller.cursorSlot.isEmpty()
