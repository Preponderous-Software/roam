from src.crafting.recipe import Recipe
from src.entity.bed import Bed
from src.entity.jungleWood import JungleWood
from src.entity.oakWood import OakWood
from src.entity.stone import Stone
from src.entity.woodFloor import WoodFloor
from src.inventory.inventory import Inventory
from entity.wood import Wood  # import via the same path the production code uses


def createInventoryWithOakWood(count):
    inventory = Inventory()
    for i in range(count):
        inventory.placeIntoFirstAvailableInventorySlot(OakWood())
    return inventory


def createInventoryWithJungleWood(count):
    inventory = Inventory()
    for i in range(count):
        inventory.placeIntoFirstAvailableInventorySlot(JungleWood())
    return inventory


def createInventoryWithMixedWood(oakCount, jungleCount):
    inventory = Inventory()
    for i in range(oakCount):
        inventory.placeIntoFirstAvailableInventorySlot(OakWood())
    for i in range(jungleCount):
        inventory.placeIntoFirstAvailableInventorySlot(JungleWood())
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
    recipe = Recipe("Wood Floor", {Wood: 4}, WoodFloor, "assets/images/woodFloor.png")
    assert recipe.canCraft(inventory) is True


def test_canCraft_returns_false_when_materials_missing():
    inventory = createInventoryWithOakWood(2)
    recipe = Recipe("Wood Floor", {Wood: 4}, WoodFloor, "assets/images/woodFloor.png")
    assert recipe.canCraft(inventory) is False


def test_canCraft_jungle_wood_satisfies_wood_ingredient():
    inventory = createInventoryWithJungleWood(4)
    recipe = Recipe("Wood Floor", {Wood: 4}, WoodFloor, "assets/images/woodFloor.png")
    assert recipe.canCraft(inventory) is True


def test_canCraft_mixed_wood_satisfies_wood_ingredient():
    inventory = createInventoryWithMixedWood(2, 2)
    recipe = Recipe("Wood Floor", {Wood: 4}, WoodFloor, "assets/images/woodFloor.png")
    assert recipe.canCraft(inventory) is True


def test_craft_deducts_materials_and_returns_item():
    inventory = createInventoryWithOakWood(4)
    recipe = Recipe("Wood Floor", {Wood: 4}, WoodFloor, "assets/images/woodFloor.png")
    result = recipe.craft(inventory)
    assert result is not None
    assert len(result) == 1
    assert isinstance(result[0], WoodFloor)
    assert inventory.getNumItemsByType(Wood) == 0


def test_craft_jungle_wood_deducts_and_returns_item():
    inventory = createInventoryWithJungleWood(4)
    recipe = Recipe("Wood Floor", {Wood: 4}, WoodFloor, "assets/images/woodFloor.png")
    result = recipe.craft(inventory)
    assert result is not None
    assert isinstance(result[0], WoodFloor)
    assert inventory.getNumItemsByType(Wood) == 0


def test_craft_returns_none_when_materials_missing():
    inventory = createInventoryWithOakWood(2)
    recipe = Recipe("Wood Floor", {Wood: 4}, WoodFloor, "assets/images/woodFloor.png")
    result = recipe.craft(inventory)
    assert result is None
    assert inventory.getNumItemsByType(Wood) == 2


def test_craft_multi_ingredient_deducts_each_type():
    inventory = createInventoryWithOakWoodAndStone(3, 2)
    recipe = Recipe("Bed", {Wood: 3, Stone: 2}, Bed, "assets/images/bed.png")
    result = recipe.craft(inventory)
    assert result is not None
    assert len(result) == 1
    assert isinstance(result[0], Bed)
    assert inventory.getNumItemsByType(Wood) == 0
    assert inventory.getNumItemsByType(Stone) == 0


def test_craft_multi_ingredient_consumes_only_required_counts():
    inventory = createInventoryWithOakWoodAndStone(5, 4)
    recipe = Recipe("Bed", {Wood: 3, Stone: 2}, Bed, "assets/images/bed.png")
    result = recipe.craft(inventory)
    assert result is not None
    assert isinstance(result[0], Bed)
    assert inventory.getNumItemsByType(Wood) == 2
    assert inventory.getNumItemsByType(Stone) == 2
