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
from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from screen.chestScreen import ChestScreen
from screen.screenType import ScreenType
from ui import palette


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()


def createChestScreen(playerInventory=None, chest=None):
    renderer = MagicMock()
    renderer.getDisplayWidth.return_value = 800
    renderer.getDisplayHeight.return_value = 600
    renderer.getDisplaySize.return_value = (800, 600)

    inputSource = MagicMock()
    inputSource.getMousePosition.return_value = (0, 0)
    inputSource.getMouseButtons.return_value = (False, False, False)
    inputSource.isPressed.return_value = False

    screen = ChestScreen.__new__(ChestScreen)
    screen.renderer = renderer
    screen.inputSource = inputSource
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
    screen.inputSource.getMousePosition.return_value = centre

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


def test_on_exit_returns_cursor_items_and_fires_on_close():
    # onExit (extracted from run() in Phase 3b-2) must return held items and
    # fire the on-close callback so the chest's room is saved.
    fired = []
    screen = createChestScreen()
    screen.onClose = lambda: fired.append(True)
    screen.cursorSlot.add(Apple())
    assert not screen.cursorSlot.isEmpty()

    screen.onExit()

    assert screen.cursorSlot.isEmpty()
    assert fired == [True]


# Characterization tests for keyboard navigation, event dispatch and the draw
# path, resolved through the shared DI container (PygameRenderer-spec mock,
# 1280x720). They assert the screen's current behavior — no behavior change
# intended.


@pytest.fixture
def make_chest_screen(resolve, override_dependency):
    def makeChestScreen(chest=None, playerInventory=None):
        override_dependency(
            Inventory, playerInventory if playerInventory is not None else Inventory()
        )
        screen = resolve(ChestScreen)
        screen.setChest(chest if chest is not None else Chest())
        screen.status = MagicMock()
        return screen

    return makeChestScreen


def _cursor(screen):
    return screen._focusPanel, screen._cursorRow, screen._cursorCol


def _press(screen, *keys):
    for key in keys:
        screen.handleKeyDownEvent(key)


def _chestGeometry(screen):
    return list(
        screen._slotGeometry(screen.getChestInventory(), screen.getChestPanelRect())
    )


def _playerGeometry(screen):
    return list(screen._slotGeometry(screen.inventory, screen.getPlayerPanelRect()))


def _centre(geometryEntry):
    _, _, itemX, itemY, itemWidth, itemHeight = geometryEntry
    return int(itemX + itemWidth / 2), int(itemY + itemHeight / 2)


def test_cursor_starts_on_first_chest_slot(make_chest_screen):
    screen = make_chest_screen()

    assert _cursor(screen) == (0, 0, 0)


def test_right_moves_cursor_and_wraps_at_row_end(make_chest_screen):
    screen = make_chest_screen()

    _press(screen, KeyCode.RIGHT, KeyCode.RIGHT, KeyCode.RIGHT, KeyCode.RIGHT)
    assert _cursor(screen) == (0, 0, 4)

    _press(screen, KeyCode.RIGHT)
    assert _cursor(screen) == (0, 0, 0)


def test_left_and_a_move_cursor_left_with_wrap(make_chest_screen):
    screen = make_chest_screen()

    _press(screen, KeyCode.LEFT)
    assert _cursor(screen) == (0, 0, 4)

    _press(screen, KeyCode.A)
    assert _cursor(screen) == (0, 0, 3)


def test_down_and_s_move_cursor_down_chest_rows(make_chest_screen):
    screen = make_chest_screen()

    _press(screen, KeyCode.DOWN)
    assert _cursor(screen) == (0, 1, 0)

    _press(screen, KeyCode.S)
    assert _cursor(screen) == (0, 2, 0)


def test_down_from_last_chest_row_moves_to_player_panel(make_chest_screen):
    screen = make_chest_screen()
    _press(screen, KeyCode.RIGHT, KeyCode.RIGHT, KeyCode.RIGHT)
    _press(screen, KeyCode.DOWN, KeyCode.DOWN, KeyCode.DOWN, KeyCode.DOWN)
    assert _cursor(screen) == (0, 4, 3)

    _press(screen, KeyCode.DOWN)

    # Focus passes to the first row of the player's inventory; column is kept.
    assert _cursor(screen) == (1, 0, 3)


def test_down_on_last_player_row_stays_put(make_chest_screen):
    screen = make_chest_screen()
    screen._focusPanel = 1
    screen._cursorRow = 4
    screen._cursorCol = 2

    _press(screen, KeyCode.DOWN)

    assert _cursor(screen) == (1, 4, 2)


def test_up_and_w_move_cursor_up_rows(make_chest_screen):
    screen = make_chest_screen()
    screen._cursorRow = 3

    _press(screen, KeyCode.UP)
    assert _cursor(screen) == (0, 2, 0)

    _press(screen, KeyCode.W)
    assert _cursor(screen) == (0, 1, 0)


def test_up_from_first_player_row_moves_to_last_chest_row(make_chest_screen):
    screen = make_chest_screen()
    screen._focusPanel = 1
    screen._cursorCol = 2

    _press(screen, KeyCode.UP)

    assert _cursor(screen) == (0, 4, 2)


def test_up_on_first_chest_row_stays_put(make_chest_screen):
    screen = make_chest_screen()
    screen._cursorCol = 1

    _press(screen, KeyCode.UP)

    assert _cursor(screen) == (0, 0, 1)


def test_short_last_row_clamps_column_and_narrows_wrap(make_chest_screen):
    chest = Chest()
    del chest.getStoredInventory().getInventorySlots()[7:]
    screen = make_chest_screen(chest=chest)
    _press(screen, KeyCode.RIGHT, KeyCode.RIGHT, KeyCode.RIGHT, KeyCode.RIGHT)

    # Row 1 holds only slots 5 and 6, so the column is clamped to 1.
    _press(screen, KeyCode.DOWN)
    assert _cursor(screen) == (0, 1, 1)

    # Left/right then wrap over those two slots only.
    _press(screen, KeyCode.RIGHT)
    assert _cursor(screen) == (0, 1, 0)
    _press(screen, KeyCode.LEFT)
    assert _cursor(screen) == (0, 1, 1)


def test_navigation_in_a_slotless_panel_is_ignored(make_chest_screen):
    chest = Chest()
    del chest.getStoredInventory().getInventorySlots()[:]
    screen = make_chest_screen(chest=chest)

    _press(screen, KeyCode.RIGHT, KeyCode.DOWN)

    assert _cursor(screen) == (0, 0, 0)
    screen.status.set.assert_not_called()


def test_tab_switches_panel_and_clamps_cursor(make_chest_screen):
    chest = Chest()
    del chest.getStoredInventory().getInventorySlots()[7:]
    screen = make_chest_screen(chest=chest)
    screen._focusPanel = 1
    screen._cursorRow = 4
    screen._cursorCol = 4

    _press(screen, KeyCode.TAB)
    assert _cursor(screen) == (0, 1, 1)

    _press(screen, KeyCode.TAB)
    assert _cursor(screen) == (1, 1, 1)


def test_navigation_announces_an_empty_slot(make_chest_screen):
    screen = make_chest_screen()

    _press(screen, KeyCode.RIGHT)

    screen.status.set.assert_called_once_with("Empty slot")


def test_navigation_announces_a_single_item_by_name(make_chest_screen):
    chest = Chest()
    chest.getStoredInventory().getInventorySlots()[1].add(Apple())
    screen = make_chest_screen(chest=chest)

    _press(screen, KeyCode.RIGHT)

    screen.status.set.assert_called_once_with("Apple")


def test_navigation_announces_a_stack_with_its_count(make_chest_screen):
    chest = Chest()
    slot = chest.getStoredInventory().getInventorySlots()[5]
    for _ in range(3):
        slot.add(Apple())
    screen = make_chest_screen(chest=chest)

    _press(screen, KeyCode.DOWN)

    screen.status.set.assert_called_once_with("Apple x3")


@pytest.mark.parametrize("key", [KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE])
def test_confirm_keys_pick_up_the_chest_slot_under_the_cursor(make_chest_screen, key):
    chest = Chest()
    slots = chest.getStoredInventory().getInventorySlots()
    slots[6].add(OakWood())
    screen = make_chest_screen(chest=chest)
    screen._cursorRow = 1
    screen._cursorCol = 1

    _press(screen, key)

    assert slots[6].isEmpty()
    assert screen.cursorSlot.getContents()[0].getName() == "Oak Wood"


def test_confirm_in_player_panel_uses_the_player_slot(make_chest_screen):
    player = Inventory()
    player.getInventorySlots()[2].add(Apple())
    screen = make_chest_screen(playerInventory=player)
    screen._focusPanel = 1
    screen._cursorCol = 2

    _press(screen, KeyCode.RETURN)

    assert player.getNumItems() == 0
    assert screen.cursorSlot.getContents()[0].getName() == "Apple"


def test_confirm_places_the_held_stack_into_the_slot_under_the_cursor(
    make_chest_screen,
):
    chest = Chest()
    screen = make_chest_screen(chest=chest)
    screen.cursorSlot.add(Apple())
    screen._cursorCol = 3

    _press(screen, KeyCode.SPACE)

    assert screen.cursorSlot.isEmpty()
    assert chest.getStoredInventory().getInventorySlots()[3].getNumItems() == 1


def test_confirm_in_a_slotless_panel_does_nothing(make_chest_screen):
    chest = Chest()
    del chest.getStoredInventory().getInventorySlots()[:]
    screen = make_chest_screen(chest=chest)
    screen.cursorSlot.add(Apple())

    _press(screen, KeyCode.RETURN)

    assert screen.cursorSlot.getNumItems() == 1


def test_d_discards_the_held_stack(make_chest_screen):
    screen = make_chest_screen()
    screen.cursorSlot.add(Apple())
    screen.cursorSlot.add(Apple())

    _press(screen, KeyCode.D)

    assert screen.cursorSlot.isEmpty()


def test_t_takes_all_items_from_the_chest(make_chest_screen):
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    player = Inventory()
    screen = make_chest_screen(chest=chest, playerInventory=player)

    _press(screen, KeyCode.T)

    assert chest.getStoredInventory().getNumItems() == 0
    assert player.getNumItems() == 1
    screen.status.set.assert_called_with("Took all items")


def test_inventory_key_returns_to_world(make_chest_screen):
    screen = make_chest_screen()
    screen.nextScreen = None

    _press(screen, screen.keyBindings.getKey("inventory"))

    assert screen.nextScreen == ScreenType.WORLD_SCREEN
    assert screen.changeScreen is True


def test_escape_returns_to_world(make_chest_screen):
    screen = make_chest_screen()
    screen.nextScreen = None

    _press(screen, KeyCode.ESCAPE)

    assert screen.nextScreen == ScreenType.WORLD_SCREEN
    assert screen.changeScreen is True


@pytest.mark.parametrize("action", ["screenshot", "alt_screenshot"])
def test_screenshot_keys_capture_a_screenshot(make_chest_screen, action):
    screen = make_chest_screen()

    _press(screen, screen.keyBindings.getKey(action))

    screen.renderer.captureScreenshot.assert_called_once_with()
    assert screen.changeScreen is False


def test_unbound_key_is_ignored(make_chest_screen):
    screen = make_chest_screen()
    screen.cursorSlot.add(Apple())

    _press(screen, KeyCode.U)

    assert screen.changeScreen is False
    assert _cursor(screen) == (0, 0, 0)
    assert screen.cursorSlot.getNumItems() == 1
    screen.renderer.captureScreenshot.assert_not_called()
    screen.status.set.assert_not_called()


def test_handle_event_dispatches_key_down(make_chest_screen):
    screen = make_chest_screen()

    screen.handleEvent(InputEvent(EventType.KEY_DOWN, key=KeyCode.ESCAPE))

    assert screen.changeScreen is True


def test_handle_event_mouse_down_without_shift_picks_up_the_stack(make_chest_screen):
    chest = Chest()
    slot = chest.getStoredInventory().getInventorySlots()[0]
    slot.add(Apple())
    slot.add(Apple())
    screen = make_chest_screen(chest=chest)

    screen.handleEvent(
        InputEvent(
            EventType.MOUSE_DOWN, position=_centre(_chestGeometry(screen)[0]), button=1
        )
    )

    assert slot.isEmpty()
    assert screen.cursorSlot.getNumItems() == 2


@pytest.mark.parametrize("shiftKey", [KeyCode.LSHIFT, KeyCode.RSHIFT])
def test_handle_event_mouse_down_with_shift_transfers_the_stack(
    make_chest_screen, shiftKey
):
    chest = Chest()
    slot = chest.getStoredInventory().getInventorySlots()[0]
    slot.add(Apple())
    slot.add(Apple())
    player = Inventory()
    screen = make_chest_screen(chest=chest, playerInventory=player)
    screen.inputSource.isPressed.side_effect = lambda key: key == shiftKey

    screen.handleEvent(
        InputEvent(
            EventType.MOUSE_DOWN, position=_centre(_chestGeometry(screen)[0]), button=1
        )
    )

    assert slot.isEmpty()
    assert player.getNumItems() == 2
    assert screen.cursorSlot.isEmpty()
    screen.status.set.assert_called_with("Transferred items")


@pytest.mark.parametrize(
    "event",
    [
        InputEvent(EventType.KEY_UP, key=KeyCode.ESCAPE),
        # (384, 95) is the centre of the first chest slot at 1280x720, so a
        # release there would pick the apple up if it were treated as a click.
        InputEvent(EventType.MOUSE_UP, position=(384, 95), button=1),
        InputEvent(EventType.MOUSE_MOTION, position=(384, 95)),
        InputEvent(EventType.MOUSE_WHEEL, scrollY=1),
    ],
)
def test_handle_event_ignores_other_event_types(make_chest_screen, event):
    chest = Chest()
    chest.getStoredInventory().getInventorySlots()[0].add(Apple())
    screen = make_chest_screen(chest=chest)
    assert _centre(_chestGeometry(screen)[0]) == (384, 95)

    screen.handleEvent(event)

    assert screen.changeScreen is False
    assert screen.cursorSlot.isEmpty()
    assert chest.getStoredInventory().getNumItems() == 1


def test_draw_clears_the_screen_and_titles_both_panels(make_chest_screen):
    screen = make_chest_screen()
    renderer = screen.renderer

    screen.draw()

    renderer.clearScreen.assert_called_once_with(palette.BLACK)
    chestX, chestY, chestWidth, chestHeight = screen.getChestPanelRect()
    playerX, playerY, playerWidth, playerHeight = screen.getPlayerPanelRect()
    renderer.drawText.assert_any_call(
        "Chest (empty)", chestX + chestWidth / 2, chestY - 15, 20, palette.WHITE
    )
    renderer.drawText.assert_any_call(
        "Inventory", playerX + playerWidth / 2, playerY - 15, 20, palette.WHITE
    )
    renderer.drawRectangle.assert_any_call(
        chestX, chestY, chestWidth, chestHeight, palette.BLACK
    )
    renderer.drawRectangle.assert_any_call(
        playerX, playerY, playerWidth, playerHeight, palette.BLACK
    )


def test_panel_rects_scale_with_the_display(make_chest_screen):
    screen = make_chest_screen()

    assert screen.getChestPanelRect() == (320, 72, 640, 720 * 0.32)
    assert screen.getPlayerPanelRect() == (320, 720 * 0.52, 640, 720 * 0.36)


def test_draw_fills_empty_slots_white_and_draws_items_with_counts(make_chest_screen):
    chest = Chest()
    slot = chest.getStoredInventory().getInventorySlots()[0]
    slot.add(Apple())
    slot.add(Apple())
    screen = make_chest_screen(chest=chest)
    renderer = screen.renderer
    loaded = MagicMock(name="loaded")
    scaled = MagicMock(name="scaled")
    renderer.loadImage.return_value = loaded
    renderer.scaleImage.return_value = scaled

    screen.draw()

    geometry = _chestGeometry(screen)
    _, _, itemX, itemY, itemWidth, itemHeight = geometry[0]
    renderer.loadImage.assert_any_call(Apple().getImagePath())
    renderer.scaleImage.assert_any_call(loaded, (itemWidth, itemHeight))
    renderer.drawImage.assert_any_call(scaled, (itemX, itemY))
    renderer.drawText.assert_any_call(
        "2", itemX + itemWidth - 20, itemY + itemHeight - 20, 20, palette.WHITE
    )
    _, _, emptyX, emptyY, emptyWidth, emptyHeight = geometry[1]
    renderer.drawRectangle.assert_any_call(
        emptyX, emptyY, emptyWidth, emptyHeight, palette.WHITE
    )
    # One image per filled slot: 24 chest and 25 player slots are empty.
    assert renderer.drawImage.call_count == 1


def test_draw_highlights_the_cursor_slot_in_the_focused_panel_only(make_chest_screen):
    screen = make_chest_screen()
    renderer = screen.renderer
    screen._cursorRow = 1
    screen._cursorCol = 2

    screen.draw()

    _, _, itemX, itemY, itemWidth, itemHeight = _chestGeometry(screen)[7]
    renderer.drawSelectionHighlight.assert_called_once_with(
        itemX, itemY, itemWidth, itemHeight, (255, 255, 0)
    )

    renderer.drawSelectionHighlight.reset_mock()
    screen._focusPanel = 1
    screen.draw()

    _, _, itemX, itemY, itemWidth, itemHeight = _playerGeometry(screen)[7]
    renderer.drawSelectionHighlight.assert_called_once_with(
        itemX, itemY, itemWidth, itemHeight, (255, 255, 0)
    )


def test_draw_shows_instructions_along_the_top(make_chest_screen):
    screen = make_chest_screen()
    renderer = screen.renderer

    screen.draw()

    renderer.drawText.assert_any_call(
        "Arrows / W A S: navigate  -  Enter/Space: swap  -  D: discard held  -  Tab: switch panel  -  T: take all",
        640,
        14,
        16,
        palette.MEDIUM_GRAY,
    )
    closeKeyName = screen.keyBindings.getKeyName("inventory").upper()
    renderer.drawText.assert_any_call(
        "press [" + closeKeyName + "] or [Esc] to close",
        640,
        32,
        14,
        palette.MEDIUM_GRAY,
    )


def test_draw_places_back_and_take_all_buttons_with_their_callbacks(make_chest_screen):
    screen = make_chest_screen()
    renderer = screen.renderer

    screen.draw()

    renderer.drawButton.assert_any_call(
        1170,
        660,
        100,
        50,
        palette.WHITE,
        palette.BLACK,
        30,
        "Back",
        screen.switchToWorldScreen,
    )
    renderer.drawButton.assert_any_call(
        10,
        660,
        120,
        50,
        palette.WHITE,
        palette.BLACK,
        24,
        "Take All",
        screen.takeAll,
    )
    assert renderer.drawButton.call_count == 2


def test_drop_button_is_muted_red_and_brightens_on_hover(make_chest_screen):
    screen = make_chest_screen()
    renderer = screen.renderer

    screen.drawDropButton()
    renderer.drawRectangle.assert_called_once_with(580, 660, 120, 50, (150, 80, 80))
    renderer.drawText.assert_called_once_with("Drop", 640, 685, 24, palette.WHITE)

    renderer.drawRectangle.reset_mock()
    screen.inputSource.getMousePosition.return_value = (640, 685)
    screen.drawDropButton()
    renderer.drawRectangle.assert_called_once_with(580, 660, 120, 50, (200, 110, 110))


def test_draw_shows_a_tooltip_for_the_hovered_item(make_chest_screen):
    chest = Chest()
    chest.getStoredInventory().getInventorySlots()[0].add(Apple())
    screen = make_chest_screen(chest=chest)
    renderer = screen.renderer
    mouseX, mouseY = _centre(_chestGeometry(screen)[0])
    screen.inputSource.getMousePosition.return_value = (mouseX, mouseY)

    screen.draw()

    textWidth = len("Apple") * 8 + 12
    renderer.drawRectangle.assert_any_call(
        mouseX + 18, mouseY + 18, textWidth, 22, palette.NEAR_BLACK
    )
    renderer.drawText.assert_any_call(
        "Apple",
        mouseX + 18 + textWidth / 2,
        mouseY + 18 + 11,
        14,
        palette.WHITE,
    )


def test_draw_shows_a_tooltip_for_a_hovered_player_item(make_chest_screen):
    player = Inventory()
    player.getInventorySlots()[0].add(OakWood())
    screen = make_chest_screen(playerInventory=player)
    mouseX, mouseY = _centre(_playerGeometry(screen)[0])
    screen.inputSource.getMousePosition.return_value = (mouseX, mouseY)

    screen.draw()

    textWidth = len("Oak Wood") * 8 + 12
    screen.renderer.drawRectangle.assert_any_call(
        mouseX + 18, mouseY + 18, textWidth, 22, palette.NEAR_BLACK
    )


def test_draw_suppresses_the_tooltip_while_an_item_is_held(make_chest_screen):
    chest = Chest()
    chest.getStoredInventory().getInventorySlots()[0].add(Apple())
    screen = make_chest_screen(chest=chest)
    screen.cursorSlot.add(OakWood())
    screen.inputSource.getMousePosition.return_value = _centre(
        _chestGeometry(screen)[0]
    )

    screen.draw()

    colours = [c.args[4] for c in screen.renderer.drawRectangle.call_args_list]
    assert palette.NEAR_BLACK not in colours


def test_tooltip_flips_to_stay_on_screen_near_the_bottom_right(make_chest_screen):
    screen = make_chest_screen()
    screen.inputSource.getMousePosition.return_value = (1270, 715)

    screen._drawTooltip("Apple")

    # 52px wide: flipped left of the cursor (1270 - 52 - 8) and above it.
    screen.renderer.drawRectangle.assert_called_once_with(
        1210, 685, 52, 22, palette.NEAR_BLACK
    )
    screen.renderer.drawText.assert_called_once_with(
        "Apple", 1236, 696, 14, palette.WHITE
    )


def test_cursor_slot_draws_the_held_stack_at_the_mouse_with_a_count(make_chest_screen):
    screen = make_chest_screen()
    renderer = screen.renderer
    loaded = MagicMock(name="loaded")
    scaled = MagicMock(name="scaled")
    renderer.loadImage.return_value = loaded
    renderer.scaleImage.return_value = scaled
    screen.inputSource.getMousePosition.return_value = (100, 200)
    for _ in range(3):
        screen.cursorSlot.add(Apple())

    screen.drawCursorSlot()

    renderer.loadImage.assert_called_once_with(Apple().getImagePath())
    renderer.scaleImage.assert_called_once_with(loaded, (50, 50))
    renderer.drawImage.assert_called_once_with(scaled, (100, 200))
    renderer.drawText.assert_called_once_with("3", 140, 240, 18, palette.WHITE)


def test_cursor_slot_with_one_item_draws_no_count(make_chest_screen):
    screen = make_chest_screen()
    screen.cursorSlot.add(Apple())

    screen.drawCursorSlot()

    screen.renderer.drawImage.assert_called_once()
    screen.renderer.drawText.assert_not_called()


def test_empty_cursor_slot_draws_nothing(make_chest_screen):
    screen = make_chest_screen()

    screen.drawCursorSlot()

    screen.renderer.loadImage.assert_not_called()
    screen.renderer.drawImage.assert_not_called()


def test_set_inventory_and_set_on_close_are_used_by_the_screen(make_chest_screen):
    # roam.py hands the player's inventory and the save callback to the screen
    # each time a chest is opened.
    screen = make_chest_screen()
    player = Inventory()
    player.getInventorySlots()[0].add(Apple())
    fired = []
    screen.setInventory(player)
    screen.setOnClose(lambda: fired.append(True))

    _press(screen, KeyCode.TAB, KeyCode.RETURN)
    screen.onExit()

    assert fired == [True]
    assert player.getNumItems() == 1  # held apple returned on close


def test_shift_click_on_an_empty_slot_does_nothing(make_chest_screen):
    player = Inventory()
    screen = make_chest_screen(playerInventory=player)

    screen.handleMouseClickEvent(
        _centre(_chestGeometry(screen)[0]), button=1, shift=True
    )

    assert player.getNumItems() == 0
    screen.status.set.assert_not_called()


def test_draw_finishes_with_the_status_line(make_chest_screen):
    screen = make_chest_screen()

    screen.draw()

    screen.status.draw.assert_called_once_with()
