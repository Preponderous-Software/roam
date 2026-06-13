import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

import pygame
import pytest

from entity.apple import Apple
from entity.chest import Chest
from entity.oakWood import OakWood
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from screen.chestScreen import ChestScreen
from screen.screenType import ScreenType


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()


def createChestScreen(playerInventory=None, chest=None):
    graphik = MagicMock()
    gameDisplay = MagicMock()
    gameDisplay.get_width.return_value = 800
    gameDisplay.get_height.return_value = 600
    gameDisplay.get_size.return_value = (800, 600)
    graphik.getGameDisplay.return_value = gameDisplay

    screen = ChestScreen.__new__(ChestScreen)
    screen.graphik = graphik
    screen.config = MagicMock()
    screen.status = MagicMock()
    screen.keyBindings = MagicMock()
    screen.inventory = playerInventory if playerInventory is not None else Inventory()
    screen.chest = chest if chest is not None else Chest()
    screen.onClose = None
    screen.nextScreen = ScreenType.WORLD_SCREEN
    screen.changeScreen = False
    screen.cursorSlot = InventorySlot()
    return screen


def test_swap_moves_item_from_slot_into_empty_cursor():
    screen = createChestScreen()
    slot = InventorySlot()
    slot.add(Apple())

    screen.swapCursorSlotWithSlot(slot)

    assert slot.isEmpty()
    assert screen.cursorSlot.getNumItems() == 1


def test_swap_moves_cursor_item_into_empty_slot():
    screen = createChestScreen()
    screen.cursorSlot.add(Apple())
    slot = InventorySlot()

    screen.swapCursorSlotWithSlot(slot)

    assert screen.cursorSlot.isEmpty()
    assert slot.getNumItems() == 1


def test_swap_merges_matching_items_into_slot():
    screen = createChestScreen()
    screen.cursorSlot.add(Apple())
    screen.cursorSlot.add(Apple())
    slot = InventorySlot()
    slot.add(Apple())

    screen.swapCursorSlotWithSlot(slot)

    assert slot.getNumItems() == 3
    assert screen.cursorSlot.isEmpty()


def test_swap_exchanges_differing_items():
    screen = createChestScreen()
    screen.cursorSlot.add(OakWood())
    slot = InventorySlot()
    slot.add(Apple())

    screen.swapCursorSlotWithSlot(slot)

    assert slot.getContents()[0].getName() == "Oak Wood"
    assert screen.cursorSlot.getContents()[0].getName() == "Apple"


def test_click_on_chest_slot_moves_item_to_cursor():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    screen = createChestScreen(chest=chest)

    # Derive the centre of the chest's first slot from the screen's own geometry.
    geometry = list(
        screen._slotGeometry(screen.getChestInventory(), screen.getChestPanelRect())
    )
    _, _, itemX, itemY, itemWidth, itemHeight = geometry[0]
    centre = (itemX + itemWidth / 2, itemY + itemHeight / 2)

    screen.handleMouseClickEvent(centre, button=1)

    assert chest.getStoredInventory().getNumItems() == 0
    assert screen.cursorSlot.getNumItems() == 1


def test_draw_panel_returns_hovered_item_name(monkeypatch):
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    screen = createChestScreen(chest=chest)

    geometry = list(
        screen._slotGeometry(screen.getChestInventory(), screen.getChestPanelRect())
    )
    _, _, itemX, itemY, itemWidth, itemHeight = geometry[0]
    centre = (int(itemX + itemWidth / 2), int(itemY + itemHeight / 2))
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: centre)

    hovered = screen._drawPanel(
        screen.getChestInventory(), screen.getChestPanelRect(), "Chest"
    )

    assert hovered == "Apple"


def test_draw_panel_returns_none_when_not_hovering_an_item(monkeypatch):
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    screen = createChestScreen(chest=chest)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (0, 0))

    hovered = screen._drawPanel(
        screen.getChestInventory(), screen.getChestPanelRect(), "Chest"
    )

    assert hovered is None


def test_chest_title_marks_an_empty_chest():
    screen = createChestScreen(chest=Chest())

    assert screen._chestTitle() == "Chest (empty)"


def test_chest_title_is_plain_when_chest_has_items():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    screen = createChestScreen(chest=chest)

    assert screen._chestTitle() == "Chest"


def test_back_button_geometry_is_bottom_right():
    screen = createChestScreen()

    # Bottom-right 100x50 button inset 10px (800x600 display).
    assert screen.isInsideBackButton((740, 560)) is True
    assert screen.isInsideBackButton((400, 300)) is False


def test_click_on_back_button_does_not_drop_cursor_stack():
    screen = createChestScreen()
    screen.cursorSlot.add(Apple())
    screen.cursorSlot.add(Apple())

    # Centre of the bottom-right Back button; the actual close is fired by
    # graphik.drawButton, so the click handler must simply not drop the stack.
    screen.handleMouseClickEvent((740, 560), button=1)

    assert screen.cursorSlot.getNumItems() == 2


def test_take_all_moves_chest_contents_to_player():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    player = Inventory()
    screen = createChestScreen(playerInventory=player, chest=chest)

    screen.takeAll()

    assert chest.getStoredInventory().getNumItems() == 0
    assert player.getNumItems() == 2
    screen.status.set.assert_called_with("Took all items")


def test_take_all_on_empty_chest_reports_empty():
    screen = createChestScreen(chest=Chest())

    screen.takeAll()

    screen.status.set.assert_called_with("Chest is empty")


def test_take_all_with_full_inventory_leaves_items_in_chest():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    player = Inventory()
    _fill_inventory(player)
    screen = createChestScreen(playerInventory=player, chest=chest)

    screen.takeAll()

    assert chest.getStoredInventory().getNumItems() == 1
    screen.status.set.assert_called_with("Inventory full")


def test_take_all_partial_reports_took_what_fit():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    # Player has exactly one free slot, already full of apples elsewhere so the
    # OakWood cannot stack anywhere — only the Apple fits.
    player = Inventory()
    _fill_inventory(player)
    player.getInventorySlots()[0].clear()
    screen = createChestScreen(playerInventory=player, chest=chest)

    screen.takeAll()

    assert chest.getStoredInventory().getNumItems() == 1
    screen.status.set.assert_called_with("Inventory full — took what fit")


def test_click_on_take_all_button_does_not_drop_cursor_stack():
    screen = createChestScreen()
    screen.cursorSlot.add(Apple())
    screen.cursorSlot.add(Apple())

    buttonX, buttonY, buttonWidth, buttonHeight = screen._takeAllButtonRect()
    centre = (buttonX + buttonWidth / 2, buttonY + buttonHeight / 2)
    screen.handleMouseClickEvent(centre, button=1)

    assert screen.cursorSlot.getNumItems() == 2


def test_left_click_outside_panels_keeps_cursor_items():
    # Clicking empty space must no longer discard cursor items — dropping is
    # now only possible via the explicit Drop button.
    screen = createChestScreen()
    screen.cursorSlot.add(Apple())
    screen.cursorSlot.add(Apple())

    # (0, 0) is above both panels and not on any button.
    screen.handleMouseClickEvent((0, 0), button=1)

    assert screen.cursorSlot.getNumItems() == 2


def test_left_click_on_drop_button_drops_stack():
    screen = createChestScreen()
    screen.cursorSlot.add(Apple())
    screen.cursorSlot.add(Apple())

    buttonX, buttonY, buttonWidth, buttonHeight = screen._dropButtonRect()
    centre = (buttonX + buttonWidth / 2, buttonY + buttonHeight / 2)
    screen.handleMouseClickEvent(centre, button=1)

    assert screen.cursorSlot.isEmpty()


def test_middle_click_on_drop_button_drops_single_item():
    screen = createChestScreen()
    screen.cursorSlot.add(Apple())
    screen.cursorSlot.add(Apple())

    buttonX, buttonY, buttonWidth, buttonHeight = screen._dropButtonRect()
    centre = (buttonX + buttonWidth / 2, buttonY + buttonHeight / 2)
    screen.handleMouseClickEvent(centre, button=2)

    assert screen.cursorSlot.getNumItems() == 1


def test_shift_click_chest_slot_transfers_stack_to_player():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    player = Inventory()
    screen = createChestScreen(playerInventory=player, chest=chest)

    geometry = list(
        screen._slotGeometry(screen.getChestInventory(), screen.getChestPanelRect())
    )
    _, _, itemX, itemY, itemWidth, itemHeight = geometry[0]
    centre = (itemX + itemWidth / 2, itemY + itemHeight / 2)

    screen.handleMouseClickEvent(centre, button=1, shift=True)

    assert chest.getStoredInventory().getNumItems() == 0
    assert player.getNumItems() == 2
    assert screen.cursorSlot.isEmpty()  # nothing picked onto the cursor


def test_shift_click_player_slot_transfers_stack_to_chest():
    chest = Chest()
    player = Inventory()
    player.placeIntoFirstAvailableInventorySlot(Apple())
    screen = createChestScreen(playerInventory=player, chest=chest)

    geometry = list(screen._slotGeometry(screen.inventory, screen.getPlayerPanelRect()))
    _, _, itemX, itemY, itemWidth, itemHeight = geometry[0]
    centre = (itemX + itemWidth / 2, itemY + itemHeight / 2)

    screen.handleMouseClickEvent(centre, button=1, shift=True)

    assert player.getNumItems() == 0
    assert chest.getStoredInventory().getNumItems() == 1


def test_shift_click_into_full_destination_keeps_items_and_warns():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    player = Inventory()
    _fill_inventory(player)
    screen = createChestScreen(playerInventory=player, chest=chest)

    geometry = list(
        screen._slotGeometry(screen.getChestInventory(), screen.getChestPanelRect())
    )
    _, _, itemX, itemY, itemWidth, itemHeight = geometry[0]
    centre = (itemX + itemWidth / 2, itemY + itemHeight / 2)

    screen.handleMouseClickEvent(centre, button=1, shift=True)

    assert chest.getStoredInventory().getNumItems() == 1
    screen.status.set.assert_called_with("No room to transfer")


def test_close_returns_cursor_items_to_player_and_calls_on_close():
    player = Inventory()
    screen = createChestScreen(playerInventory=player)
    screen.cursorSlot.add(Apple())
    onClose = MagicMock()
    screen.onClose = onClose
    screen.changeScreen = True  # cause run() to exit immediately

    # Avoid touching a real display: stub the per-frame draw entry points.
    screen._drawPanel = MagicMock()
    screen.drawInstructions = MagicMock()
    screen.drawCursorSlot = MagicMock()
    import pygame

    pygame.event.get = MagicMock(return_value=[])
    pygame.display.update = MagicMock()

    result = screen.run()

    assert result == ScreenType.WORLD_SCREEN
    assert screen.cursorSlot.isEmpty()
    assert player.getNumItems() == 1
    onClose.assert_called_once()


def _fill_inventory(inventory):
    for slot in inventory.getInventorySlots():
        while slot.getNumItems() < slot.getMaxStackSize():
            slot.add(Apple())


def test_close_falls_back_to_chest_when_player_inventory_is_full():
    player = Inventory()
    _fill_inventory(player)
    chest = Chest()
    screen = createChestScreen(playerInventory=player, chest=chest)
    screen.cursorSlot.add(OakWood())
    screen.changeScreen = True  # cause run() to exit immediately

    screen.run()

    # The held item could not fit in the full inventory, so it returns to the
    # chest rather than being silently destroyed.
    assert screen.cursorSlot.isEmpty()
    assert chest.getStoredInventory().getNumItems() == 1
    assert (
        chest.getStoredInventory().getInventorySlots()[0].getContents()[0].getName()
        == "Oak Wood"
    )
