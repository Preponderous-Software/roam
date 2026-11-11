from unittest.mock import MagicMock

import pytest

import screen.inventoryScreen as inventoryScreenModule
from config.keyBindings import KeyBindings
from entity.grass import Grass
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.wheatSeed import WheatSeed
from entity.woodFloor import WoodFloor
from inventory.inventory import Inventory
from rendering.keyCode import KeyCode
from rendering.renderer import Renderer
from screen.inventoryScreen import InventoryScreen

# Characterization tests for InventoryScreen's crafting and keyboard cursor
# paths. Entities are imported through the `entity.*` root, the same one
# crafting/recipeRegistry.py uses, because Recipe.canCraft and
# Inventory.getNumItemsByType compare with isinstance.


def createScreen(supportsImageLoading=True):
    renderer = MagicMock(spec=Renderer)
    renderer.getDisplayWidth.return_value = 800
    renderer.getDisplayHeight.return_value = 600
    renderer.getDisplaySize.return_value = (800, 600)
    renderer.supportsImageLoading.return_value = supportsImageLoading
    inputSource = MagicMock()
    inputSource.getMousePosition.return_value = (0, 0)
    return InventoryScreen(
        renderer, inputSource, MagicMock(), MagicMock(), Inventory(), KeyBindings()
    )


def fillSlot(slot, entityClass, count):
    for _ in range(count):
        slot.add(entityClass())


def recipeNamed(screen, name):
    return next(r for r in screen.recipeRegistry.getRecipes() if r.getName() == name)


def drawnTexts(screen):
    return [c.args[0] for c in screen.renderer.drawText.call_args_list]


# --- craftRecipe ---


def test_craft_recipe_consumes_ingredients_and_adds_result():
    screen = createScreen()
    fillSlot(screen.inventory.getInventorySlots()[0], OakWood, 5)

    screen.craftRecipe(recipeNamed(screen, "Wood Floor"))

    assert screen.inventory.getNumItemsByType(OakWood) == 1
    assert screen.inventory.getNumItemsByType(WoodFloor) == 1
    screen.status.set.assert_called_with("Crafted Wood Floor")


def test_craft_recipe_without_materials_reports_and_changes_nothing():
    screen = createScreen()
    fillSlot(screen.inventory.getInventorySlots()[0], OakWood, 3)

    screen.craftRecipe(recipeNamed(screen, "Wood Floor"))

    assert screen.inventory.getNumItemsByType(OakWood) == 3
    assert screen.inventory.getNumItemsByType(WoodFloor) == 0
    screen.status.set.assert_called_with("Not enough materials")


def test_missing_materials_is_reported_before_a_full_inventory():
    screen = createScreen()
    for slot in screen.inventory.getInventorySlots():
        fillSlot(slot, Stone, 20)

    screen.craftRecipe(recipeNamed(screen, "Wood Floor"))

    screen.status.set.assert_called_once_with("Not enough materials")


def test_craft_recipe_with_multiple_results_adds_every_result():
    screen = createScreen()
    fillSlot(screen.inventory.getInventorySlots()[0], Grass, 2)

    screen.craftRecipe(recipeNamed(screen, "Wheat Seed"))

    assert screen.inventory.getNumItemsByType(Grass) == 1
    assert screen.inventory.getNumItemsByType(WheatSeed) == 3


def test_craft_recipe_refuses_when_no_room_for_the_result():
    screen = createScreen()
    slots = screen.inventory.getInventorySlots()
    fillSlot(slots[0], OakWood, 20)
    for slot in slots[1:]:
        fillSlot(slot, Stone, 20)

    screen.craftRecipe(recipeNamed(screen, "Wood Floor"))

    assert screen.inventory.getNumItemsByType(OakWood) == 20
    assert screen.inventory.getNumItemsByType(WoodFloor) == 0
    screen.status.set.assert_called_with("Inventory full")


def test_craft_recipe_counts_the_space_the_consumed_ingredients_free():
    # The only free slot comes from the stack the recipe consumes (#648).
    screen = createScreen()
    slots = screen.inventory.getInventorySlots()
    fillSlot(slots[0], OakWood, 4)
    for slot in slots[1:]:
        fillSlot(slot, Stone, 20)

    screen.craftRecipe(recipeNamed(screen, "Wood Floor"))

    assert screen.inventory.getNumItemsByType(OakWood) == 0
    assert screen.inventory.getNumItemsByType(WoodFloor) == 1
    screen.status.set.assert_called_with("Crafted Wood Floor")


def test_craft_recipe_that_cannot_place_every_result_restores_the_inventory():
    # Two of the three seeds fit on the partial stack and the third does not,
    # so the consumed grass and the placed seeds are both rolled back.
    screen = createScreen()
    slots = screen.inventory.getInventorySlots()
    fillSlot(slots[0], Grass, 20)
    fillSlot(slots[1], WheatSeed, 18)
    for slot in slots[2:]:
        fillSlot(slot, Stone, 20)

    screen.craftRecipe(recipeNamed(screen, "Wheat Seed"))

    assert slots[0].getNumItems() == 20
    assert slots[1].getNumItems() == 18
    assert screen.inventory.getNumItemsByType(Grass) == 20
    assert screen.inventory.getNumItemsByType(WheatSeed) == 18
    screen.status.set.assert_called_with("Inventory full")


def test_craft_recipe_stacks_result_onto_matching_full_inventory_slot():
    # Space on a partly filled stack of the result counts as room.
    screen = createScreen()
    slots = screen.inventory.getInventorySlots()
    fillSlot(slots[0], OakWood, 20)
    fillSlot(slots[1], WoodFloor, 19)
    for slot in slots[2:]:
        fillSlot(slot, Stone, 20)

    screen.craftRecipe(recipeNamed(screen, "Wood Floor"))

    assert slots[1].getNumItems() == 20
    screen.status.set.assert_called_with("Crafted Wood Floor")


# --- keyboard cursor: pick up, put down, merge, swap, discard ---


def test_enter_picks_up_the_selected_stack_and_puts_it_down_elsewhere():
    screen = createScreen()
    slots = screen.inventory.getInventorySlots()
    fillSlot(slots[0], Grass, 3)

    screen.handleKeyDownEvent(KeyCode.RETURN)
    assert slots[0].isEmpty()
    assert screen.cursorSlot.getNumItems() == 3

    screen.handleKeyDownEvent(KeyCode.RIGHT)
    screen.handleKeyDownEvent(KeyCode.SPACE)
    assert screen.cursorSlot.isEmpty()
    assert slots[1].getNumItems() == 3


def test_putting_down_onto_the_same_item_merges_up_to_the_stack_limit():
    screen = createScreen()
    slots = screen.inventory.getInventorySlots()
    fillSlot(slots[0], Grass, 18)
    fillSlot(screen.cursorSlot, Grass, 5)

    screen.handleKeyDownEvent(KeyCode.KP_ENTER)

    assert slots[0].getNumItems() == 20
    assert screen.cursorSlot.getNumItems() == 3


def test_putting_down_onto_a_different_item_swaps_them():
    screen = createScreen()
    slots = screen.inventory.getInventorySlots()
    fillSlot(slots[0], Stone, 2)
    fillSlot(screen.cursorSlot, Grass, 4)

    screen.handleKeyDownEvent(KeyCode.RETURN)

    assert slots[0].getContents()[0].getName() == "Grass"
    assert slots[0].getNumItems() == 4
    assert screen.cursorSlot.getContents()[0].getName() == "Stone"
    assert screen.cursorSlot.getNumItems() == 2


def test_d_discards_the_held_stack():
    screen = createScreen()
    fillSlot(screen.cursorSlot, Grass, 4)

    screen.handleKeyDownEvent(KeyCode.D)

    assert screen.cursorSlot.isEmpty()
    assert screen.inventory.getNumItems() == 0


@pytest.mark.parametrize(
    "count, expected",
    [(0, "Empty slot"), (1, "Grass"), (3, "Grass x3")],
)
def test_moving_the_selection_announces_the_slot(count, expected):
    screen = createScreen()
    fillSlot(screen.inventory.getInventorySlots()[1], Grass, count)

    screen.handleKeyDownEvent(KeyCode.RIGHT)

    screen.status.set.assert_called_with(expected)


# --- craft panel keys ---


def test_escape_closes_the_craft_panel_before_the_screen():
    screen = createScreen()
    screen.craftPanelOpen = True

    screen.handleKeyDownEvent(KeyCode.ESCAPE)
    assert screen.craftPanelOpen is False
    assert screen.changeScreen is False

    screen.handleKeyDownEvent(KeyCode.ESCAPE)
    assert screen.changeScreen is True


def test_craft_panel_cursor_is_clamped_to_the_recipe_list():
    screen = createScreen()
    screen.craftPanelOpen = True
    numRecipes = len(screen.recipeRegistry.getRecipes())

    screen.handleKeyDownEvent(KeyCode.UP)
    assert screen._craftCursor == 0

    for _ in range(numRecipes + 3):
        screen.handleKeyDownEvent(KeyCode.DOWN)
    assert screen._craftCursor == numRecipes - 1


def test_enter_in_the_craft_panel_crafts_the_highlighted_recipe():
    screen = createScreen()
    screen.craftPanelOpen = True
    fillSlot(screen.inventory.getInventorySlots()[0], OakWood, 4)
    selectedBefore = screen.inventory.getSelectedInventorySlotIndex()

    screen.handleKeyDownEvent(KeyCode.RETURN)  # recipe 0 is Wood Floor

    assert screen.inventory.getNumItemsByType(WoodFloor) == 1
    assert screen.cursorSlot.isEmpty()
    assert screen.inventory.getSelectedInventorySlotIndex() == selectedBefore


def test_toggle_craft_panel_ignores_a_second_toggle_within_one_second(monkeypatch):
    screen = createScreen()
    now = [1000.0]
    monkeypatch.setattr(inventoryScreenModule.time, "time", lambda: now[0])
    screen._craftCursor = 4

    screen.handleKeyDownEvent(KeyCode.C)
    assert screen.craftPanelOpen is True
    assert screen._craftCursor == 0

    now[0] += 0.5
    screen.toggleCraftPanel()
    assert screen.craftPanelOpen is True

    now[0] += 1.0
    screen.toggleCraftPanel()
    assert screen.craftPanelOpen is False


# --- craft panel labels ---


def test_ingredient_label_splits_camel_case_class_names():
    assert InventoryScreen._ingredientLabel(OakWood) == "Oak Wood"
    assert InventoryScreen._ingredientLabel(Stone) == "Stone"


def test_closed_craft_panel_draws_nothing():
    screen = createScreen()

    screen.drawCraftPanel()

    screen.renderer.drawRectangle.assert_not_called()
    screen.renderer.drawText.assert_not_called()


def test_craft_panel_labels_craftable_and_missing_recipes():
    screen = createScreen()
    screen.craftPanelOpen = True
    fillSlot(screen.inventory.getInventorySlots()[0], Grass, 1)
    fillSlot(screen.inventory.getInventorySlots()[1], OakWood, 1)
    numRecipes = len(screen.recipeRegistry.getRecipes())

    screen.drawCraftPanel()

    buttonLabels = [c.args[7] for c in screen.renderer.drawButton.call_args_list]
    assert buttonLabels == ["3x Wheat Seed (1x Grass)"]
    texts = drawnTexts(screen)
    assert "1 / %d craftable" % numRecipes in texts[1]
    assert "Wood Floor — need 3 Wood" in texts
    assert "Bed — need 2 Wood, 2 Stone" in texts


# --- inventory panel text ---


def test_mouse_hint_is_drawn_only_when_images_are_supported():
    pygameScreen = createScreen(supportsImageLoading=True)
    textScreen = createScreen(supportsImageLoading=False)

    pygameScreen.drawPlayerInventory()
    textScreen.drawPlayerInventory()

    def hasMouseHint(screen):
        return any(t.startswith("Left-click") for t in drawnTexts(screen))

    assert hasMouseHint(pygameScreen)
    assert not hasMouseHint(textScreen)


def test_held_stack_is_named_above_the_inventory_panel():
    screen = createScreen()
    fillSlot(screen.cursorSlot, Grass, 2)

    screen.drawPlayerInventory()

    assert "Holding: Grass x2" in drawnTexts(screen)


def test_set_inventory_replaces_the_inventory_the_screen_edits():
    screen = createScreen()
    replacement = Inventory()
    fillSlot(replacement.getInventorySlots()[0], Grass, 1)

    screen.setInventory(replacement)
    screen.handleKeyDownEvent(KeyCode.RETURN)

    assert replacement.getInventorySlots()[0].isEmpty()
    assert screen.cursorSlot.getNumItems() == 1
