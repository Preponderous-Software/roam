"""Characterization tests for InventoryScreen's slot clicks and draw paths.

These lock in current behaviour: left-click merge / swap / pick-up on a slot,
handleEvent's dispatch, and what drawPlayerInventory, the hover tooltip,
drawCursorSlot, drawDropButton and draw() send to the renderer.
"""

from unittest.mock import MagicMock, call

import pytest

from config.keyBindings import KeyBindings
from entity.grass import Grass
from entity.stone import Stone
from inventory.inventory import Inventory
from rendering.inputEvent import EventType, InputEvent
from rendering.renderer import Renderer
from screen.inventoryScreen import InventoryScreen
from ui import palette

LOADED = object()
SCALED = object()

# For an 800x600 display the panel spans (200, 150)-(600, 450). Each slot is
# 70x50, so slot 0 covers (205, 155)-(275, 205) and slot 1 starts at x=285.
SLOT_0_CENTRE = (240, 180)
SLOT_1_CENTRE = (320, 180)
GAP_BETWEEN_SLOTS_0_AND_1 = (280, 180)


def _renderer(width=800, height=600):
    renderer = MagicMock(spec=Renderer)
    renderer.getDisplayWidth.return_value = width
    renderer.getDisplayHeight.return_value = height
    renderer.getDisplaySize.return_value = (width, height)
    renderer.supportsImageLoading.return_value = True
    renderer.loadImage.return_value = LOADED
    renderer.scaleImage.return_value = SCALED
    return renderer


def _screen(width=800, height=600, mouse=(0, 0)):
    inputSource = MagicMock()
    inputSource.getMousePosition.return_value = mouse
    return InventoryScreen(
        _renderer(width, height),
        inputSource,
        MagicMock(),
        MagicMock(),
        Inventory(),
        KeyBindings(),
    )


def _fill(slot, cls, count):
    for _ in range(count):
        slot.add(cls())


def _slot(screen, index):
    return screen.inventory.getInventorySlots()[index]


def _drawnTexts(screen):
    return [c.args[0] for c in screen.renderer.drawText.call_args_list]


# --- left-click on a slot ---------------------------------------------------


def test_left_click_with_empty_cursor_picks_up_the_slot_stack():
    screen = _screen()
    _fill(_slot(screen, 0), Grass, 3)

    screen.handleMouseClickEvent(SLOT_0_CENTRE, button=1)

    assert _slot(screen, 0).isEmpty()
    assert screen.cursorSlot.getNumItems() == 3
    assert screen.cursorSlot.getContents()[0].getName() == "Grass"


def test_left_click_held_stack_onto_empty_slot_puts_it_down():
    screen = _screen()
    _fill(screen.cursorSlot, Stone, 2)

    screen.handleMouseClickEvent(SLOT_1_CENTRE, button=1)

    assert screen.cursorSlot.isEmpty()
    assert _slot(screen, 1).getNumItems() == 2
    assert _slot(screen, 0).isEmpty()


def test_left_click_held_stack_onto_matching_slot_merges():
    screen = _screen()
    _fill(_slot(screen, 0), Grass, 4)
    _fill(screen.cursorSlot, Grass, 3)

    screen.handleMouseClickEvent(SLOT_0_CENTRE, button=1)

    assert _slot(screen, 0).getNumItems() == 7
    assert screen.cursorSlot.isEmpty()


def test_left_click_merge_fills_to_max_stack_and_keeps_the_rest_held():
    screen = _screen()
    maxStack = _slot(screen, 0).getMaxStackSize()
    _fill(_slot(screen, 0), Grass, maxStack - 2)
    _fill(screen.cursorSlot, Grass, 5)

    screen.handleMouseClickEvent(SLOT_0_CENTRE, button=1)

    assert _slot(screen, 0).getNumItems() == maxStack
    assert screen.cursorSlot.getNumItems() == 3


def test_left_click_held_stack_onto_different_item_swaps():
    screen = _screen()
    _fill(_slot(screen, 0), Stone, 2)
    _fill(screen.cursorSlot, Grass, 5)

    screen.handleMouseClickEvent(SLOT_0_CENTRE, button=1)

    assert _slot(screen, 0).getContents()[0].getName() == "Grass"
    assert _slot(screen, 0).getNumItems() == 5
    assert screen.cursorSlot.getContents()[0].getName() == "Stone"
    assert screen.cursorSlot.getNumItems() == 2


def test_click_in_the_gap_between_slots_changes_nothing():
    screen = _screen()
    _fill(_slot(screen, 0), Grass, 2)
    _fill(screen.cursorSlot, Stone, 1)

    screen.handleMouseClickEvent(GAP_BETWEEN_SLOTS_0_AND_1, button=1)

    assert _slot(screen, 0).getNumItems() == 2
    assert _slot(screen, 1).isEmpty()
    assert screen.cursorSlot.getContents()[0].getName() == "Stone"


# --- handleEvent ------------------------------------------------------------


@pytest.mark.parametrize(
    "eventType",
    [EventType.KEY_UP, EventType.MOUSE_UP, EventType.MOUSE_MOTION, EventType.QUIT],
)
def test_handle_event_ignores_other_event_types(eventType):
    screen = _screen()
    screen.handleKeyDownEvent = MagicMock()
    screen.handleMouseClickEvent = MagicMock()

    screen.handleEvent(InputEvent(eventType, position=SLOT_0_CENTRE, button=1))

    screen.handleKeyDownEvent.assert_not_called()
    screen.handleMouseClickEvent.assert_not_called()
    assert screen.changeScreen is False


# --- drawPlayerInventory ----------------------------------------------------


def test_filled_slot_draws_its_scaled_image_and_count():
    screen = _screen()
    _fill(_slot(screen, 0), Grass, 3)

    screen.drawPlayerInventory()

    screen.renderer.loadImage.assert_called_once_with(Grass().getImagePath())
    screen.renderer.scaleImage.assert_called_once_with(LOADED, (70.0, 50.0))
    screen.renderer.drawImage.assert_called_once_with(SCALED, (205.0, 155.0))
    assert call("3", 255.0, 185.0, 20, palette.WHITE) in (
        screen.renderer.drawText.call_args_list
    )


def test_hovering_a_filled_slot_draws_a_tooltip_below_right_of_the_pointer():
    screen = _screen(mouse=SLOT_0_CENTRE)
    _fill(_slot(screen, 0), Grass, 1)

    screen.drawPlayerInventory()

    # Width is len("Grass") * 8 + 12 = 52, offset 18 px from the pointer.
    screen.renderer.drawRectangle.assert_any_call(258, 198, 52, 22, palette.NEAR_BLACK)
    screen.renderer.drawText.assert_any_call("Grass", 284.0, 209, 14, palette.WHITE)


def test_hovering_an_empty_slot_draws_no_tooltip():
    screen = _screen(mouse=SLOT_0_CENTRE)

    screen.drawPlayerInventory()

    colours = [c.args[4] for c in screen.renderer.drawRectangle.call_args_list]
    assert palette.NEAR_BLACK not in colours


def test_tooltip_flips_left_and_up_near_the_bottom_right_edge():
    # On a 200x120 display slot 24 (last row, last column) covers
    # (135, 83)-(145, 85); a 52 px tooltip 18 px right of x=140 would end at
    # 210 > 200, and 18 px below y=84 would end at 124 > 120.
    screen = _screen(width=200, height=120, mouse=(140, 84))
    _fill(_slot(screen, 24), Grass, 1)

    screen.drawPlayerInventory()

    screen.renderer.drawRectangle.assert_any_call(80, 54, 52, 22, palette.NEAR_BLACK)


# --- drawCursorSlot ---------------------------------------------------------


def test_cursor_slot_draws_held_stack_at_the_pointer_with_its_count():
    screen = _screen(mouse=(300, 250))
    _fill(screen.cursorSlot, Grass, 3)

    screen.drawCursorSlot()

    screen.renderer.scaleImage.assert_called_once_with(LOADED, (50, 50))
    screen.renderer.drawImage.assert_called_once_with(SCALED, (300, 250))
    screen.renderer.drawText.assert_called_once_with("3", 340, 290, 18, palette.WHITE)


def test_cursor_slot_with_a_single_item_draws_no_count():
    screen = _screen(mouse=(300, 250))
    _fill(screen.cursorSlot, Grass, 1)

    screen.drawCursorSlot()

    screen.renderer.drawImage.assert_called_once()
    screen.renderer.drawText.assert_not_called()


def test_empty_cursor_slot_draws_nothing():
    screen = _screen()

    screen.drawCursorSlot()

    screen.renderer.loadImage.assert_not_called()
    screen.renderer.drawImage.assert_not_called()


# --- drawDropButton ---------------------------------------------------------


@pytest.mark.parametrize(
    "mouse, colour",
    [((60, 565), (200, 110, 110)), ((400, 300), (150, 80, 80))],
    ids=["hovered", "idle"],
)
def test_drop_button_brightens_on_hover(mouse, colour):
    screen = _screen(mouse=mouse)

    screen.drawDropButton()

    screen.renderer.drawRectangle.assert_called_once_with(10, 540, 100, 50, colour)
    screen.renderer.drawText.assert_called_once_with(
        "Drop", 60.0, 565.0, 24, palette.WHITE
    )


# --- draw -------------------------------------------------------------------


def test_draw_clears_then_draws_every_part():
    screen = _screen()
    screen.craftPanelOpen = True

    screen.draw()

    screen.renderer.clearScreen.assert_called_once_with(palette.BLACK)
    buttonLabels = [c.args[7] for c in screen.renderer.drawButton.call_args_list]
    assert "Craft" in buttonLabels
    assert "Back" in buttonLabels
    screen.renderer.drawButton.assert_any_call(
        690,
        540,
        100,
        50,
        palette.WHITE,
        palette.BLACK,
        30,
        "Back",
        (screen.switchToWorldScreen),
    )
    assert "Recipes" in _drawnTexts(screen)
    assert "Drop" in _drawnTexts(screen)
    screen.status.draw.assert_called_once_with()


def test_draw_skips_the_recipe_list_when_the_craft_panel_is_closed():
    screen = _screen()

    screen.draw()

    assert "Recipes" not in _drawnTexts(screen)
