import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

from config.keyBindings import KeyBindings
from inventory.inventory import Inventory
from rendering.keyCode import KeyCode
from screen.worldScreen import WorldScreen

# The world screen's hotbar-cycle and screenshot keys both resolve through
# KeyBindings rather than hardcoded KeyCodes, so a remap takes effect and the
# ASCII alt_screenshot binding reaches --text players (Print Screen cannot).


def _worldScreen():
    ws = WorldScreen.__new__(WorldScreen)
    ws.status = MagicMock()
    ws.renderer = MagicMock()
    ws.keyBindings = KeyBindings()
    player = MagicMock()
    player.getInventory.return_value = Inventory()
    ws.player = player
    return ws


def test_hotbar_cycle_right_advances_the_selected_slot():
    ws = _worldScreen()

    ws._handleUtilityKey(KeyCode.RIGHTBRACKET, ws.keyBindings)

    assert ws.player.getInventory().getSelectedInventorySlotIndex() == 1


def test_hotbar_cycle_left_wraps_around_from_the_first_slot():
    ws = _worldScreen()

    ws._handleUtilityKey(KeyCode.LEFTBRACKET, ws.keyBindings)

    assert ws.player.getInventory().getSelectedInventorySlotIndex() == 9


def test_hotbar_cycle_follows_a_remapped_binding():
    ws = _worldScreen()
    ws.keyBindings.setKey("hotbar_cycle_right", KeyCode.T)

    ws._handleUtilityKey(KeyCode.RIGHTBRACKET, ws.keyBindings)
    assert ws.player.getInventory().getSelectedInventorySlotIndex() == 0

    ws._handleUtilityKey(KeyCode.T, ws.keyBindings)
    assert ws.player.getInventory().getSelectedInventorySlotIndex() == 1


def test_alt_screenshot_key_captures_a_screenshot():
    ws = _worldScreen()
    ws.renderer.captureScreenshot.return_value = "/tmp/roam_20260101_000000.txt"

    ws.handleKeyDownEvent(KeyCode.P)

    ws.renderer.captureScreenshot.assert_called_once()
    ws.status.set.assert_called_with("Screenshot saved")


def test_primary_screenshot_key_still_captures_a_screenshot():
    ws = _worldScreen()
    ws.renderer.captureScreenshot.return_value = None

    ws.handleKeyDownEvent(KeyCode.PRINTSCREEN)

    ws.renderer.captureScreenshot.assert_called_once()
    ws.status.set.assert_called_with("Screenshots not supported in this mode")
