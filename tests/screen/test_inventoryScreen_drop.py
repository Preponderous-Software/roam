import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock

from src.config.config import Config
from src.inventory.inventory import Inventory
from src.inventory.inventorySlot import InventorySlot
from src.entity.grass import Grass
from src.lib.graphik.src.graphik import Graphik
from src.screen.inventoryScreen import InventoryScreen
from src.ui.status import Status
from src.world.tickCounter import TickCounter


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def createInventoryScreen():
    gameDisplay = MagicMock()
    gameDisplay.get_width.return_value = 800
    gameDisplay.get_height.return_value = 600
    gameDisplay.get_size.return_value = (800, 600)
    graphik = Graphik(gameDisplay)
    config = Config()
    tickCounter = TickCounter(config)
    status = Status(graphik, tickCounter)
    inventory = Inventory()
    return InventoryScreen(graphik, config, status, inventory)


def createGrass():
    return Grass()


# --- isInsideInventoryPanel tests ---


def test_isInsideInventoryPanel_center():
    screen = createInventoryScreen()
    # center of an 800x600 display is (400, 300), which is inside the panel
    assert screen.isInsideInventoryPanel((400, 300)) == True


def test_isInsideInventoryPanel_top_left_corner():
    screen = createInventoryScreen()
    # panel starts at (200, 150) for 800x600
    assert screen.isInsideInventoryPanel((200, 150)) == True


def test_isInsideInventoryPanel_bottom_right_corner():
    screen = createInventoryScreen()
    # panel ends at (600, 450) for 800x600
    assert screen.isInsideInventoryPanel((600, 450)) == True


def test_isInsideInventoryPanel_outside_top_left():
    screen = createInventoryScreen()
    assert screen.isInsideInventoryPanel((10, 10)) == False


def test_isInsideInventoryPanel_outside_bottom_right():
    screen = createInventoryScreen()
    assert screen.isInsideInventoryPanel((790, 590)) == False


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
