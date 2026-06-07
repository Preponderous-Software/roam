import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

from screen.inventoryScreen import InventoryScreen


def _screen():
    # Bypass the DI constructor; wire only what the hotbar dispatch needs.
    # getKey returns the binding name itself, so a "key" can be the name string.
    screen = InventoryScreen.__new__(InventoryScreen)
    screen.craftPanelOpen = False
    screen.keyBindings = MagicMock()
    screen.keyBindings.getKey = lambda name: name
    screen._swapCalls = []
    screen.swapCursorSlotWithInventorySlotByIndex = screen._swapCalls.append
    return screen


def test_hotbar_keys_map_to_correct_slots():
    screen = _screen()
    expected = {
        "hotbar_1": 0,
        "hotbar_2": 1,
        "hotbar_3": 2,
        "hotbar_4": 3,
        "hotbar_5": 4,
        "hotbar_6": 5,
        "hotbar_7": 6,
        "hotbar_8": 7,
        "hotbar_9": 8,
        # hotbar_0 wraps to slot 9 — the subtlety the refactor must preserve.
        "hotbar_0": 9,
    }
    for name, index in expected.items():
        screen._swapCalls.clear()
        screen._handleHotbarKey(name)
        assert screen._swapCalls == [index], name


def test_non_hotbar_key_is_ignored():
    screen = _screen()
    screen._handleHotbarKey("some_other_key")
    assert screen._swapCalls == []


def test_handle_key_down_routes_hotbar_key_to_slot():
    # The else-branch of handleKeyDownEvent dispatches to the hotbar handler.
    screen = _screen()
    screen._handleHotbarKey("hotbar_3")
    assert screen._swapCalls == [2]
    screen._swapCalls.clear()
    screen.handleKeyDownEvent("hotbar_5")
    assert screen._swapCalls == [4]
