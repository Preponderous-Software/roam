"""WorldScreen reports Roam's arcade achievements: the play events reach the
tracker, a loaded world is checked at once, and nothing changes off arcade."""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
from unittest.mock import MagicMock

from achievements import arcadeBridge
from achievements.achievementRegistry import (
    EVENT_HARVESTED_WHEAT,
    EVENT_PLACED_CAMPFIRE,
    EVENT_RECOVERED_GRAVESTONE,
)
from achievements.achievements import Achievements
from codex.codex import Codex
from config.config import Config
from config.keyBindings import KeyBindings
from entity.apple import Apple
from entity.campfire import Campfire
from entity.goldenLantern import GoldenLantern
from entity.gravestone import Gravestone
from entity.matureCrop import MatureCrop
from inventory.inventory import Inventory
from screen.worldScreen import DEEPEST_Z, WorldScreen
from stats.stats import Stats
from world.room import Room
from world.tickCounter import TickCounter


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    import pygame

    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _fresh_bridge():
    arcadeBridge.reset()
    yield
    arcadeBridge.reset()


@pytest.fixture
def sent():
    messages = []
    arcadeBridge.install(messages.append)
    return messages


def _makeRoom(gridSize=5):
    return Room("test", gridSize, (0, 0, 0), 0, 0, MagicMock())


def _makeWorldScreen(room=None):
    config = Config()
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.status = MagicMock()
    ws.keyBindings = KeyBindings()
    ws.currentRoom = room or _makeRoom()
    ws.currentZ = 0
    ws.tickCounter = TickCounter(config)
    ws.stats = Stats(config)
    ws.codex = Codex()
    ws.achievements = Achievements()
    player = MagicMock()
    player.getInventory.return_value = Inventory()
    ws.player = player
    return ws


def _unlocked(messages):
    return [m["achievement"] for m in messages if m["kind"] == "unlock"]


def test_harvesting_wheat_is_noted():
    room = _makeRoom()
    ws = _makeWorldScreen(room)
    location = room.getGrid().getLocationByCoordinates(1, 1)
    room.addEntityToLocation(MatureCrop(0), location)

    assert ws._tryHarvestCrop(location, room)

    assert EVENT_HARVESTED_WHEAT in ws.achievements.getEvents()


def test_placing_a_campfire_is_noted():
    room = _makeRoom()
    ws = _makeWorldScreen(room)
    inventory = ws.player.getInventory()
    inventory.placeIntoFirstAvailableInventorySlot(Campfire())
    inventory.setSelectedInventorySlotIndex(0)
    location = room.getGrid().getLocationByCoordinates(2, 2)

    ws._executePlaceAt(location, room)

    assert any(isinstance(e, Campfire) for e in location.getEntities().values())
    assert EVENT_PLACED_CAMPFIRE in ws.achievements.getEvents()


def test_emptying_a_gravestone_is_noted():
    room = _makeRoom()
    ws = _makeWorldScreen(room)
    gravestone = Gravestone()
    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    location = room.getGrid().getLocationByCoordinates(1, 1)
    room.addEntityToLocation(gravestone, location)

    ws._interactWithGravestone(gravestone, room, location)

    assert EVENT_RECOVERED_GRAVESTONE in ws.achievements.getEvents()


def test_a_world_screen_built_without_a_tracker_still_plays():
    # Older tests (and anything else) that build a WorldScreen by hand get no
    # tracking rather than an AttributeError.
    room = _makeRoom()
    ws = _makeWorldScreen(room)
    del ws.achievements
    location = room.getGrid().getLocationByCoordinates(1, 1)
    room.addEntityToLocation(MatureCrop(0), location)
    assert ws._tryHarvestCrop(location, room)
    ws._updateAchievements(force=True)


def test_the_world_state_reaches_the_conditions(sent):
    ws = _makeWorldScreen()
    ws.tickCounter.tick = ws.config.dayNightCycleLengthTicks * 3
    ws.stats.setRoomsExplored(26)
    ws.codex.discover("GoldOre")
    ws.player.getInventory().placeIntoFirstAvailableInventorySlot(GoldenLantern())
    ws.currentZ = DEEPEST_Z

    ws._updateAchievements(force=True)

    assert set(_unlocked(sent)) == {
        "nightfall",
        "first-light",
        "one-full-day",
        "wanderer",
        "into-the-dark",
        "rock-bottom",
        "struck-gold",
        "lamplighter",
    }
    assert {"kind": "score", "board": "most-days", "value": 3} in sent
    assert {"kind": "score", "board": "most-rooms", "value": 26} in sent


def test_off_arcade_the_world_is_not_even_read():
    ws = _makeWorldScreen()
    ws._buildAchievementContext = MagicMock()
    ws._updateAchievements(force=True)
    ws._buildAchievementContext.assert_not_called()


def test_a_reporting_failure_does_not_reach_play():
    def broken(message):
        raise RuntimeError("the page is gone")

    arcadeBridge.install(broken)
    ws = _makeWorldScreen()
    ws.stats.setRoomsExplored(100)
    ws._updateAchievements(force=True)  # must not raise


def test_a_tracker_error_does_not_reach_play(sent):
    ws = _makeWorldScreen()
    ws.codex = None  # getDiscoveredEntities() now fails inside the check
    ws._updateAchievements(force=True)
    assert sent == []


def test_loading_an_existing_save_credits_it(tmp_path, sent):
    # Write a world's stats, tick and codex with the real persistence, then
    # load them the way WorldScreen.initialize does and check at once.
    config = Config()
    config.pathToSaveDirectory = str(tmp_path)
    stats = Stats(config)
    stats.setRoomsExplored(120)
    stats.setFoodEaten(55)
    stats.save()
    ticks = TickCounter(config)
    ticks.tick = config.dayNightCycleLengthTicks * 8
    ticks.save()

    ws = _makeWorldScreen()
    ws.config = config
    ws.stats = Stats(config)
    ws.stats.load()
    ws.tickCounter = TickCounter(config)
    ws.tickCounter.load()

    ws._updateAchievements(force=True)

    assert set(_unlocked(sent)) == {
        "nightfall",
        "first-light",
        "one-full-day",
        "a-week-out",
        "wanderer",
        "far-roamer",
        "well-fed",
    }
    assert {"kind": "score", "board": "most-days", "value": 8} in sent
    assert {"kind": "score", "board": "most-rooms", "value": 120} in sent
