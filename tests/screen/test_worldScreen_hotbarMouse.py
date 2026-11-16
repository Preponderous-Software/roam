import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

from entity.apple import Apple
from entity.banana import Banana
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from rendering.inputEvent import EventType, InputEvent
from screen.worldScreen import MIDDLE_MOUSE_BUTTON, WorldScreen

# Characterization tests for the WorldScreen's hotbar and world mouse
# handling: hit-testing a hotbar slot, left/right clicks on a slot with and
# without a held cursor item, returning the cursor item to the inventory,
# the mouse-down/up/motion dispatch (including the middle-button HUD drag),
# and drawing the held cursor item. They assert current behaviour only.

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600

# With an 800x600 display and no HUD offset, the hotbar's first slot starts
# at x = 800/2 - 50*5 - 50/2 = 125 and y = 600 - 150 = 450. Slots are 50 px
# wide with a 5 px gap, so slot i spans [125 + 55*i, 175 + 55*i).
SLOT_0_POINT = (130, 460)
SLOT_1_POINT = (185, 460)
SLOT_9_POINT = (125 + 55 * 9 + 49, 499)
GAP_POINT = (177, 460)
BELOW_HOTBAR_POINT = (130, 500)
WORLD_POINT = (400, 100)

LEFT = (True, False, False)
RIGHT = (False, False, True)
NONE = (False, False, False)


def _worldScreen(mousePosition=WORLD_POINT, buttons=NONE):
    ws = WorldScreen.__new__(WorldScreen)
    ws.status = MagicMock()
    ws.renderer = MagicMock()
    ws.renderer.getDisplayWidth.return_value = DISPLAY_WIDTH
    ws.renderer.getDisplayHeight.return_value = DISPLAY_HEIGHT
    ws.inputSource = MagicMock()
    ws.inputSource.getMousePosition.return_value = mousePosition
    ws.inputSource.getMouseButtons.return_value = buttons
    ws.hudDragManager = MagicMock()
    ws.hudDragManager.getOffset.return_value = (0, 0)
    ws.hudDragManager.isDragging.return_value = False
    ws.keyBindings = MagicMock()
    ws.keyBindings.getKeyName.return_value = "i"
    ws.cursorSlot = InventorySlot()
    ws.showInventory = False
    inventory = Inventory()
    ws.player = MagicMock()
    ws.player.getInventory.return_value = inventory
    return ws


def _inventory(ws):
    return ws.player.getInventory()


def _slot(ws, index):
    return _inventory(ws).getInventorySlots()[index]


def _mouseEvent(eventType, button):
    return InputEvent(eventType, button=button)


# --- getHotbarSlotAtMousePosition --------------------------------------------


def test_hotbar_hit_test_finds_the_first_slot():
    ws = _worldScreen(mousePosition=SLOT_0_POINT)

    assert ws.getHotbarSlotAtMousePosition() == 0


def test_hotbar_hit_test_finds_the_second_slot_past_the_gap():
    ws = _worldScreen(mousePosition=SLOT_1_POINT)

    assert ws.getHotbarSlotAtMousePosition() == 1


def test_hotbar_hit_test_finds_the_last_slot_at_its_inner_corner():
    ws = _worldScreen(mousePosition=SLOT_9_POINT)

    assert ws.getHotbarSlotAtMousePosition() == 9


def test_hotbar_hit_test_misses_the_gap_between_slots():
    ws = _worldScreen(mousePosition=GAP_POINT)

    assert ws.getHotbarSlotAtMousePosition() == -1


def test_hotbar_hit_test_misses_below_the_slots():
    ws = _worldScreen(mousePosition=BELOW_HOTBAR_POINT)

    assert ws.getHotbarSlotAtMousePosition() == -1


def test_hotbar_hit_test_follows_the_dragged_hud_offset():
    ws = _worldScreen(mousePosition=(130 + 100, 460 - 40))
    ws.hudDragManager.getOffset.return_value = (100, -40)

    assert ws.getHotbarSlotAtMousePosition() == 0
    ws.hudDragManager.getOffset.assert_called_with("hotbar")


# --- returnCursorSlotToInventory ---------------------------------------------


def test_return_cursor_slot_does_nothing_when_empty():
    ws = _worldScreen()

    ws.returnCursorSlotToInventory()

    assert _inventory(ws).getNumItems() == 0
    ws.status.set.assert_not_called()


def test_return_cursor_slot_moves_every_item_into_the_inventory():
    ws = _worldScreen()
    ws.cursorSlot.setContents([Apple(), Apple()])

    ws.returnCursorSlotToInventory()

    assert ws.cursorSlot.isEmpty()
    assert _slot(ws, 0).getNumItems() == 2
    ws.status.set.assert_not_called()


def test_return_cursor_slot_keeps_the_overflow_and_reports_a_full_inventory():
    ws = _worldScreen()
    for slot in _inventory(ws).getInventorySlots():
        slot.setContents([Banana()])
    ws.cursorSlot.setContents([Apple(), Apple()])

    ws.returnCursorSlotToInventory()

    assert ws.cursorSlot.getNumItems() == 2
    ws.status.set.assert_called_once_with("Inventory full", duration=150)


# --- _handleHotbarClick: left click ------------------------------------------


def test_left_click_on_a_filled_slot_picks_it_up_into_the_cursor():
    ws = _worldScreen(buttons=LEFT)
    apple = Apple()
    _slot(ws, 3).setContents([apple])

    ws._handleHotbarClick(3)

    assert ws.cursorSlot.getContents() == [apple]
    assert _slot(ws, 3).isEmpty()


def test_left_click_on_an_empty_slot_with_an_empty_cursor_changes_nothing():
    ws = _worldScreen(buttons=LEFT)

    ws._handleHotbarClick(3)

    assert ws.cursorSlot.isEmpty()
    assert _slot(ws, 3).isEmpty()


def test_left_click_with_a_matching_cursor_item_merges_into_the_slot():
    ws = _worldScreen(buttons=LEFT)
    _slot(ws, 2).setContents([Apple() for _ in range(19)])
    ws.cursorSlot.setContents([Apple(), Apple(), Apple()])

    ws._handleHotbarClick(2)

    # The slot fills to its 20-item cap; the rest stays on the cursor.
    assert _slot(ws, 2).getNumItems() == 20
    assert ws.cursorSlot.getNumItems() == 2


def test_left_click_with_a_different_cursor_item_swaps_them():
    ws = _worldScreen(buttons=LEFT)
    apple = Apple()
    banana = Banana()
    _slot(ws, 2).setContents([apple])
    ws.cursorSlot.setContents([banana])

    ws._handleHotbarClick(2)

    assert _slot(ws, 2).getContents() == [banana]
    assert ws.cursorSlot.getContents() == [apple]


def test_left_click_with_a_cursor_item_on_an_empty_slot_places_it():
    ws = _worldScreen(buttons=LEFT)
    banana = Banana()
    ws.cursorSlot.setContents([banana])

    ws._handleHotbarClick(4)

    assert _slot(ws, 4).getContents() == [banana]
    assert ws.cursorSlot.isEmpty()


# --- _handleHotbarClick: right click -----------------------------------------


def test_right_click_with_a_cursor_item_on_an_empty_slot_places_it():
    ws = _worldScreen(buttons=RIGHT)
    banana = Banana()
    ws.cursorSlot.setContents([banana])

    ws._handleHotbarClick(1)

    assert _slot(ws, 1).getContents() == [banana]
    assert ws.cursorSlot.isEmpty()


def test_right_click_with_a_matching_cursor_item_merges_into_the_slot():
    ws = _worldScreen(buttons=RIGHT)
    _slot(ws, 1).setContents([Apple()])
    ws.cursorSlot.setContents([Apple(), Apple()])

    ws._handleHotbarClick(1)

    assert _slot(ws, 1).getNumItems() == 3
    assert ws.cursorSlot.isEmpty()


def test_right_click_with_a_different_cursor_item_swaps_them():
    ws = _worldScreen(buttons=RIGHT)
    apple = Apple()
    banana = Banana()
    _slot(ws, 1).setContents([apple])
    ws.cursorSlot.setContents([banana])

    ws._handleHotbarClick(1)

    assert _slot(ws, 1).getContents() == [banana]
    assert ws.cursorSlot.getContents() == [apple]


def test_right_click_moves_a_hotbar_stack_into_the_backpack():
    ws = _worldScreen(buttons=RIGHT)
    _slot(ws, 0).setContents([Apple(), Apple()])

    ws._handleHotbarClick(0)

    assert _slot(ws, 0).isEmpty()
    assert _slot(ws, 10).getNumItems() == 2
    ws.status.set.assert_called_once_with("Moved to inventory")


def test_right_click_keeps_what_does_not_fit_and_reports_a_full_inventory():
    ws = _worldScreen(buttons=RIGHT)
    for slot in _inventory(ws).getInventorySlots()[10:]:
        slot.setContents([Banana()])
    apple = Apple()
    _slot(ws, 0).setContents([apple])

    ws._handleHotbarClick(0)

    assert _slot(ws, 0).getContents() == [apple]
    ws.status.set.assert_called_once_with("Inventory full", duration=150)


def test_right_click_on_an_empty_slot_with_an_empty_cursor_changes_nothing():
    ws = _worldScreen(buttons=RIGHT)

    ws._handleHotbarClick(0)

    assert ws.cursorSlot.isEmpty()
    assert _inventory(ws).getNumItems() == 0
    ws.status.set.assert_not_called()


# --- handleMouseDownEvent ----------------------------------------------------


def test_middle_mouse_down_starts_a_hud_drag_and_does_nothing_else():
    ws = _worldScreen(mousePosition=SLOT_0_POINT, buttons=LEFT)
    _slot(ws, 0).setContents([Apple()])

    ws.handleMouseDownEvent(_mouseEvent(EventType.MOUSE_DOWN, MIDDLE_MOUSE_BUTTON))

    ws.hudDragManager.handleMouseDown.assert_called_once_with(*SLOT_0_POINT)
    assert _slot(ws, 0).getNumItems() == 1
    ws.player.setGathering.assert_not_called()


def test_mouse_down_with_the_inventory_open_asks_to_close_it_first():
    ws = _worldScreen(mousePosition=WORLD_POINT, buttons=LEFT)
    ws.showInventory = True

    ws.handleMouseDownEvent(_mouseEvent(EventType.MOUSE_DOWN, 1))

    ws.status.set.assert_called_once_with("Close inventory first (I)")
    ws.player.setGathering.assert_not_called()


def test_mouse_down_on_the_hotbar_routes_to_the_hotbar_click():
    ws = _worldScreen(mousePosition=SLOT_1_POINT, buttons=LEFT)
    apple = Apple()
    _slot(ws, 1).setContents([apple])

    ws.handleMouseDownEvent(_mouseEvent(EventType.MOUSE_DOWN, 1))

    assert ws.cursorSlot.getContents() == [apple]
    ws.player.setGathering.assert_not_called()


def test_mouse_down_in_the_world_while_holding_an_item_returns_it():
    ws = _worldScreen(mousePosition=WORLD_POINT, buttons=LEFT)
    ws.cursorSlot.setContents([Apple()])

    ws.handleMouseDownEvent(_mouseEvent(EventType.MOUSE_DOWN, 1))

    assert ws.cursorSlot.isEmpty()
    assert _slot(ws, 0).getNumItems() == 1
    ws.player.setGathering.assert_not_called()


def test_left_mouse_down_in_the_world_starts_gathering():
    ws = _worldScreen(mousePosition=WORLD_POINT, buttons=LEFT)

    ws.handleMouseDownEvent(_mouseEvent(EventType.MOUSE_DOWN, 1))

    ws.player.setGathering.assert_called_once_with(True)
    ws.player.setPlacing.assert_not_called()


def test_right_mouse_down_in_the_world_starts_placing():
    ws = _worldScreen(mousePosition=WORLD_POINT, buttons=RIGHT)

    ws.handleMouseDownEvent(_mouseEvent(EventType.MOUSE_DOWN, 3))

    ws.player.setPlacing.assert_called_once_with(True)
    ws.player.setGathering.assert_not_called()


# --- handleMouseUpEvent / handleMouseMotionEvent -----------------------------


def test_middle_mouse_up_finishes_an_active_hud_drag():
    ws = _worldScreen(mousePosition=(300, 200))
    ws.hudDragManager.isDragging.return_value = True

    ws.handleMouseUpEvent(_mouseEvent(EventType.MOUSE_UP, MIDDLE_MOUSE_BUTTON))

    ws.hudDragManager.handleMouseUp.assert_called_once_with(
        300, 200, DISPLAY_WIDTH, DISPLAY_HEIGHT
    )
    ws.player.setGathering.assert_not_called()
    ws.player.setPlacing.assert_not_called()


def test_middle_mouse_up_without_a_drag_falls_through_to_releasing_actions():
    ws = _worldScreen(buttons=NONE)

    ws.handleMouseUpEvent(_mouseEvent(EventType.MOUSE_UP, MIDDLE_MOUSE_BUTTON))

    ws.hudDragManager.handleMouseUp.assert_not_called()
    ws.player.setGathering.assert_called_once_with(False)
    ws.player.setPlacing.assert_called_once_with(False)


def test_mouse_up_stops_only_the_actions_whose_button_was_released():
    ws = _worldScreen(buttons=RIGHT)  # right still held, left released

    ws.handleMouseUpEvent(_mouseEvent(EventType.MOUSE_UP, 1))

    ws.player.setGathering.assert_called_once_with(False)
    ws.player.setPlacing.assert_not_called()


def test_mouse_motion_moves_an_active_hud_drag():
    ws = _worldScreen(mousePosition=(320, 240))
    ws.hudDragManager.isDragging.return_value = True

    ws.handleMouseMotionEvent()

    ws.hudDragManager.handleMouseMotion.assert_called_once_with(
        320, 240, DISPLAY_WIDTH, DISPLAY_HEIGHT
    )


def test_mouse_motion_without_a_drag_does_nothing():
    ws = _worldScreen()

    ws.handleMouseMotionEvent()

    ws.hudDragManager.handleMouseMotion.assert_not_called()


# --- drawCursorSlot ----------------------------------------------------------


def test_draw_cursor_slot_draws_nothing_when_empty():
    ws = _worldScreen()

    ws.drawCursorSlot()

    ws.renderer.drawImage.assert_not_called()
    ws.renderer.drawText.assert_not_called()


def test_draw_cursor_slot_draws_a_single_item_at_the_mouse_without_a_count():
    ws = _worldScreen(mousePosition=(210, 330))
    apple = Apple()
    ws.cursorSlot.setContents([apple])

    ws.drawCursorSlot()

    ws.renderer.loadImage.assert_called_once_with(apple.getImagePath())
    ws.renderer.scaleImage.assert_called_once_with(
        ws.renderer.loadImage.return_value, (50, 50)
    )
    ws.renderer.drawImage.assert_called_once_with(
        ws.renderer.scaleImage.return_value, (210, 330)
    )
    ws.renderer.drawText.assert_not_called()


def test_draw_cursor_slot_draws_the_stack_count_offset_from_the_mouse():
    ws = _worldScreen(mousePosition=(210, 330))
    ws.cursorSlot.setContents([Apple(), Apple(), Apple()])

    ws.drawCursorSlot()

    args = ws.renderer.drawText.call_args[0]
    assert args[:4] == ("3", 240, 360, 20)
