from unittest.mock import MagicMock

from src.config.keyBindings import KeyBindings
from src.inventory.inventory import Inventory
from src.entity.grass import Grass
from src.lib.graphik.src.graphik import Graphik
from src.screen.inventoryScreen import InventoryScreen


def createInventoryScreen():
    gameDisplay = MagicMock()
    gameDisplay.get_width.return_value = 800
    gameDisplay.get_height.return_value = 600
    gameDisplay.get_size.return_value = (800, 600)
    graphik = Graphik(gameDisplay)
    config = MagicMock()
    status = MagicMock()
    inventory = Inventory()
    keyBindings = KeyBindings()
    return InventoryScreen(graphik, config, status, inventory, keyBindings)


def createGrass():
    return Grass()


# --- isInsideInventoryPanel tests ---


def test_isInsideInventoryPanel_center():
    screen = createInventoryScreen()
    # center of an 800x600 display is (400, 300), which is inside the panel
    assert screen.isInsideInventoryPanel((400, 300))


def test_isInsideInventoryPanel_top_left_corner():
    screen = createInventoryScreen()
    # panel starts at (200, 150) for 800x600
    assert screen.isInsideInventoryPanel((200, 150))


def test_isInsideInventoryPanel_bottom_right_corner():
    screen = createInventoryScreen()
    # panel ends at (600, 450) for 800x600
    assert screen.isInsideInventoryPanel((600, 450))


def test_isInsideInventoryPanel_outside_top_left():
    screen = createInventoryScreen()
    assert not screen.isInsideInventoryPanel((10, 10))


def test_isInsideInventoryPanel_outside_bottom_right():
    screen = createInventoryScreen()
    assert not screen.isInsideInventoryPanel((790, 590))


# --- dropCursorSlot tests ---


def test_dropCursorSlot_clears_cursor():
    screen = createInventoryScreen()
    for i in range(5):
        screen.cursorSlot.add(createGrass())
    assert screen.cursorSlot.getNumItems() == 5

    screen.dropCursorSlot()

    assert screen.cursorSlot.isEmpty()
    assert screen.cursorSlot.getNumItems() == 0


def test_dropCursorSlot_empty_cursor():
    screen = createInventoryScreen()
    assert screen.cursorSlot.isEmpty()

    screen.dropCursorSlot()

    assert screen.cursorSlot.isEmpty()


def test_dropCursorSlot_does_not_affect_inventory():
    screen = createInventoryScreen()
    item = createGrass()
    screen.inventory.placeIntoFirstAvailableInventorySlot(item)
    for i in range(3):
        screen.cursorSlot.add(createGrass())

    screen.dropCursorSlot()

    assert screen.cursorSlot.isEmpty()
    assert screen.inventory.getNumItems() == 1


# --- dropOneFromCursorSlot tests ---


def test_dropOneFromCursorSlot_removes_one():
    screen = createInventoryScreen()
    for i in range(5):
        screen.cursorSlot.add(createGrass())
    assert screen.cursorSlot.getNumItems() == 5

    screen.dropOneFromCursorSlot()

    assert screen.cursorSlot.getNumItems() == 4


def test_dropOneFromCursorSlot_last_item():
    screen = createInventoryScreen()
    screen.cursorSlot.add(createGrass())

    screen.dropOneFromCursorSlot()

    assert screen.cursorSlot.isEmpty()


def test_dropOneFromCursorSlot_empty_cursor():
    screen = createInventoryScreen()
    assert screen.cursorSlot.isEmpty()

    screen.dropOneFromCursorSlot()

    assert screen.cursorSlot.isEmpty()


def test_dropOneFromCursorSlot_does_not_affect_inventory():
    screen = createInventoryScreen()
    item = createGrass()
    screen.inventory.placeIntoFirstAvailableInventorySlot(item)
    for i in range(3):
        screen.cursorSlot.add(createGrass())

    screen.dropOneFromCursorSlot()

    assert screen.cursorSlot.getNumItems() == 2
    assert screen.inventory.getNumItems() == 1


# --- handleMouseClickEvent integration tests ---


def test_handleMouseClickEvent_left_click_outside_drops_all():
    screen = createInventoryScreen()
    for i in range(5):
        screen.cursorSlot.add(createGrass())

    # (10, 10) is outside the inventory panel for 800x600
    screen.handleMouseClickEvent((10, 10), button=1)

    assert screen.cursorSlot.isEmpty()


def test_handleMouseClickEvent_middle_click_outside_drops_one():
    screen = createInventoryScreen()
    for i in range(5):
        screen.cursorSlot.add(createGrass())

    screen.handleMouseClickEvent((10, 10), button=2)

    assert screen.cursorSlot.getNumItems() == 4


def test_handleMouseClickEvent_right_click_outside_does_not_drop():
    screen = createInventoryScreen()
    for i in range(5):
        screen.cursorSlot.add(createGrass())

    screen.handleMouseClickEvent((10, 10), button=3)

    assert screen.cursorSlot.getNumItems() == 5


def test_handleMouseClickEvent_left_click_inside_panel_does_not_drop():
    screen = createInventoryScreen()
    for i in range(3):
        screen.cursorSlot.add(createGrass())

    # (400, 300) is inside the inventory panel
    screen.handleMouseClickEvent((400, 300), button=1)

    # items may have been swapped into a slot, but not discarded
    # cursor should not have been cleared by drop logic
    totalItems = screen.cursorSlot.getNumItems() + screen.inventory.getNumItems()
    assert totalItems == 3


def test_handleMouseClickEvent_left_click_on_back_button_does_not_drop():
    screen = createInventoryScreen()
    for i in range(5):
        screen.cursorSlot.add(createGrass())

    # back button is at (690, 540) to (790, 590) for 800x600
    screen.handleMouseClickEvent((750, 560), button=1)

    assert screen.cursorSlot.getNumItems() == 5


def test_handleMouseClickEvent_left_click_on_craft_button_does_not_drop():
    screen = createInventoryScreen()
    for i in range(5):
        screen.cursorSlot.add(createGrass())

    # craft button: backgroundX(200)+backgroundWidth(400)-buttonWidth(100)=500,
    # backgroundY(150)+backgroundHeight(300)+20=470, size 100x30
    screen.handleMouseClickEvent((550, 480), button=1)

    assert screen.cursorSlot.getNumItems() == 5


def test_handleMouseClickEvent_left_click_on_craft_panel_does_not_drop():
    screen = createInventoryScreen()
    screen.craftPanelOpen = True
    for i in range(5):
        screen.cursorSlot.add(createGrass())

    # craft panel: panelX=610, panelY=150, panelWidth=240, panelHeight=300
    screen.handleMouseClickEvent((700, 300), button=1)

    assert screen.cursorSlot.getNumItems() == 5


def test_handleMouseClickEvent_empty_cursor_left_click_outside_is_noop():
    screen = createInventoryScreen()
    assert screen.cursorSlot.isEmpty()

    screen.handleMouseClickEvent((10, 10), button=1)

    assert screen.cursorSlot.isEmpty()
    assert screen.inventory.getNumItems() == 0
