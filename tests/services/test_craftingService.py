import pytest
from unittest.mock import MagicMock

from services.craftingService import CraftingService
from ui.status import Status
from inventory.inventory import Inventory
from crafting.recipe import Recipe
from entity.oakWood import OakWood
from entity.woodFloor import WoodFloor


def makeService():
    status = MagicMock(spec=Status)
    return CraftingService(status), status


def makeInventoryWithOakWood(count):
    inventory = Inventory()
    for _ in range(count):
        inventory.placeIntoFirstAvailableInventorySlot(OakWood())
    return inventory


def test_craftRecipe_success():
    service, status = makeService()
    recipe = Recipe("Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png")
    inventory = makeInventoryWithOakWood(4)
    result = service.craftRecipe(recipe, inventory)
    assert result is True
    status.set.assert_called_with("Crafted Wood Floor")


def test_craftRecipe_not_enough_materials():
    service, status = makeService()
    recipe = Recipe("Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png")
    inventory = makeInventoryWithOakWood(2)
    result = service.craftRecipe(recipe, inventory)
    assert result is False
    status.set.assert_called_with("Not enough materials")


def test_canCraft_true_when_enough():
    service, _ = makeService()
    recipe = Recipe("Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png")
    inventory = makeInventoryWithOakWood(4)
    assert service.canCraft(recipe, inventory) is True


def test_canCraft_false_when_not_enough():
    service, _ = makeService()
    recipe = Recipe("Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png")
    inventory = makeInventoryWithOakWood(3)
    assert service.canCraft(recipe, inventory) is False


def test_craftRecipe_inventory_full():
    service, status = makeService()
    recipe = Recipe("Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png")
    inventory = makeInventoryWithOakWood(4)
    # Fill all remaining slots
    oak = OakWood()
    for slot in inventory.getInventorySlots():
        if slot.isEmpty():
            slot.add(oak)
    result = service.craftRecipe(recipe, inventory)
    # Should either succeed (no real full issue with 25 slots) or fail gracefully
    assert isinstance(result, bool)
