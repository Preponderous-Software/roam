from unittest.mock import MagicMock

from controllers.inventoryController import InventoryController
from services.craftingService import CraftingService
from services.inventoryService import InventoryService
from player.player import Player
from inventory.inventory import Inventory


def makeController():
    inventory = Inventory()
    player = MagicMock(spec=Player)
    player.getInventory.return_value = inventory
    craftingService = MagicMock(spec=CraftingService)
    inventoryService = MagicMock(spec=InventoryService)
    controller = InventoryController(player, craftingService, inventoryService)
    return controller, player, inventory, craftingService, inventoryService


def test_craftRecipe_delegates_to_crafting_service():
    controller, _, inventory, craftingService, _ = makeController()
    recipe = MagicMock()
    controller.craftRecipe(recipe)
    craftingService.craftRecipe.assert_called_once_with(recipe, inventory)


def test_craftRecipe_returns_service_result():
    controller, _, inventory, craftingService, _ = makeController()
    craftingService.craftRecipe.return_value = True
    recipe = MagicMock()
    result = controller.craftRecipe(recipe)
    assert result is True


def test_changeSelectedSlot_delegates_to_inventory_service():
    controller, _, _, _, inventoryService = makeController()
    controller.changeSelectedSlot(3)
    inventoryService.changeSelectedInventorySlot.assert_called_once_with(3)


def test_no_ui_state():
    """Controller must not hold any UI state (cursor, panel flags, etc.)."""
    controller, _, _, _, _ = makeController()
    assert not hasattr(controller, "cursorSlot")
    assert not hasattr(controller, "craftPanelOpen")
    assert not hasattr(controller, "lastCraftToggleTime")


def test_no_pygame_or_graphik_dependency():
    """Controller must not reference pygame or Graphik."""
    import inspect
    import controllers.inventoryController as mod
    source = inspect.getsource(mod)
    assert "import pygame" not in source
    assert "from pygame" not in source
    assert "Graphik" not in source
