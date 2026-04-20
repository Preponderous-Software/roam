from src.crafting.recipe import Recipe
from src.entity.oakWood import OakWood
from src.entity.stone import Stone
from src.entity.woodFloor import WoodFloor
from src.inventory.inventory import Inventory


def createInventoryWithOakWood(count):
    inventory = Inventory()
    for i in range(count):
        inventory.placeIntoFirstAvailableInventorySlot(OakWood())
    return inventory


def createInventoryWithOakWoodAndStone(oakCount, stoneCount):
    inventory = Inventory()
    for i in range(oakCount):
        inventory.placeIntoFirstAvailableInventorySlot(OakWood())
    for i in range(stoneCount):
        inventory.placeIntoFirstAvailableInventorySlot(Stone())
    return inventory


def test_canCraft_returns_true_when_materials_present():
    inventory = createInventoryWithOakWood(4)
    recipe = Recipe(
        "Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png"
    )
    assert recipe.canCraft(inventory) is True


def test_canCraft_returns_false_when_materials_missing():
    inventory = createInventoryWithOakWood(2)
    recipe = Recipe(
        "Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png"
    )
    assert recipe.canCraft(inventory) is False


def test_craft_deducts_materials_and_returns_item():
    inventory = createInventoryWithOakWood(4)
    recipe = Recipe(
        "Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png"
    )
    result = recipe.craft(inventory)
    assert result is not None
    assert len(result) == 1
    assert isinstance(result[0], WoodFloor)
    assert inventory.getNumItemsByType(OakWood) == 0


def test_craft_returns_none_when_materials_missing():
    inventory = createInventoryWithOakWood(2)
    recipe = Recipe(
        "Wood Floor", {OakWood: 4}, WoodFloor, "assets/images/woodFloor.png"
    )
    result = recipe.craft(inventory)
    assert result is None
    assert inventory.getNumItemsByType(OakWood) == 2
