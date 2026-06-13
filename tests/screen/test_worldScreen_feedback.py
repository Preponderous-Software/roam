import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

import pytest

from entity.apple import Apple
from inventory.inventory import Inventory
from screen.worldScreen import WorldScreen


def _worldScreen():
    ws = WorldScreen.__new__(WorldScreen)
    ws.status = MagicMock()
    ws.config = MagicMock()
    return ws


def _wheelEvent(y):
    event = MagicMock()
    event.y = y
    return event


# ---------------------------------------------------------------------------
# Scroll-wheel hotbar selection announces the new slot (parity with 1-0 keys)
# ---------------------------------------------------------------------------


def test_scroll_wheel_announces_selected_item():
    ws = _worldScreen()
    inventory = Inventory()
    inventory.placeIntoFirstAvailableInventorySlot(Apple())  # slot 0
    inventory.setSelectedInventorySlotIndex(1)
    player = MagicMock()
    player.getInventory.return_value = inventory
    ws.player = player

    ws.handleMouseWheelEvent(_wheelEvent(1))  # scroll up -> slot 0

    assert inventory.getSelectedInventorySlotIndex() == 0
    ws.status.set.assert_called_with("Selected Apple")


def test_scroll_wheel_announces_empty_slot():
    ws = _worldScreen()
    inventory = Inventory()
    inventory.setSelectedInventorySlotIndex(0)
    player = MagicMock()
    player.getInventory.return_value = inventory
    ws.player = player

    ws.handleMouseWheelEvent(_wheelEvent(-1))  # scroll down -> slot 1 (empty)

    assert inventory.getSelectedInventorySlotIndex() == 1
    ws.status.set.assert_called_with("Empty slot")


# ---------------------------------------------------------------------------
# Minimap zoom: floor at the default and report both limits
# ---------------------------------------------------------------------------


def _kb():
    kb = MagicMock()
    kb.getKey = lambda name: name
    return kb


def test_minimap_zoom_out_reduces_when_above_floor():
    ws = _worldScreen()
    ws.minimapScaleFactor = 0.5

    ws._handleUtilityKey("minimap_zoom_out", _kb())

    assert ws.minimapScaleFactor == pytest.approx(0.4)


def test_minimap_zoom_out_floors_and_warns_at_minimum():
    ws = _worldScreen()
    ws.minimapScaleFactor = 0.1

    ws._handleUtilityKey("minimap_zoom_out", _kb())

    assert ws.minimapScaleFactor == pytest.approx(0.1)
    ws.status.set.assert_called_with("Minimap at minimum size")


def test_minimap_zoom_in_warns_at_maximum():
    ws = _worldScreen()
    ws.minimapScaleFactor = 1.0

    ws._handleUtilityKey("minimap_zoom_in", _kb())

    assert ws.minimapScaleFactor == pytest.approx(1.0)
    ws.status.set.assert_called_with("Minimap at maximum size")
