"""Tests for the 'rooms explored' statistic increment logic.

Covers the requirement that:
- Entering a brand-new room increments rooms explored by exactly 1
- Re-entering a previously visited room does not increment the count
- Rooms pre-loaded in the background (via RoomPreloader) still count
  when the player actually enters them, but not if never entered
"""
from unittest.mock import MagicMock

import pytest

from stats.stats import Stats
from world.map import Map
from world.roomPreloader import RoomPreloader


def _setup(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.gridSize = 3
    test_config.worldBorder = 0
    gameMap = resolve(Map)
    stats = resolve(Stats)
    status = MagicMock()
    return gameMap, stats, status


def _simulate_load_or_generate(gameMap, stats, status, x, y):
    """Mirrors WorldScreen._loadOrGenerateRoom logic for unit-testing purposes."""
    wasCached = gameMap.hasRoom(x, y)
    room = gameMap.getRoom(x, y)
    if room == -1:
        room = gameMap.generateNewRoom(x, y)
    if gameMap.consumeIsNewRoom(x, y):
        status.set("New area discovered")
        stats.incrementScore()
        stats.incrementRoomsExplored()
    elif not wasCached:
        status.set("Area loaded")
    return room


def test_entering_new_room_increments_rooms_explored(resolve, test_config, tmp_path):
    gameMap, stats, status = _setup(resolve, test_config, tmp_path)

    initial = stats.getRoomsExplored()
    _simulate_load_or_generate(gameMap, stats, status, 1, 0)

    assert stats.getRoomsExplored() == initial + 1


def test_reentering_visited_room_does_not_increment(resolve, test_config, tmp_path):
    gameMap, stats, status = _setup(resolve, test_config, tmp_path)

    # First visit — should increment
    _simulate_load_or_generate(gameMap, stats, status, 1, 0)
    after_first = stats.getRoomsExplored()

    # Second visit — should NOT increment
    _simulate_load_or_generate(gameMap, stats, status, 1, 0)

    assert stats.getRoomsExplored() == after_first


def test_preloaded_room_increments_when_player_enters(resolve, test_config, tmp_path):
    gameMap, stats, status = _setup(resolve, test_config, tmp_path)

    # Simulate RoomPreloader generating the room in the background
    gameMap.generateNewRoom(2, 0)

    initial = stats.getRoomsExplored()

    # Player transitions into the pre-loaded room
    _simulate_load_or_generate(gameMap, stats, status, 2, 0)

    assert stats.getRoomsExplored() == initial + 1


def test_preloaded_room_not_entered_does_not_increment(resolve, test_config, tmp_path):
    gameMap, stats, status = _setup(resolve, test_config, tmp_path)

    initial = stats.getRoomsExplored()

    # Simulate RoomPreloader generating adjacent rooms (player never enters them)
    preloader = resolve(RoomPreloader)
    try:
        gameMap.generateNewRoom(0, 0)
        preloader.preloadNearbyRooms(0, 0, gameMap)
        preloader.shutdown(wait=True)
    finally:
        preloader.shutdown(wait=True)

    # Stats must not have changed — no player transition occurred
    assert stats.getRoomsExplored() == initial


def test_multiple_new_rooms_each_increment_once(resolve, test_config, tmp_path):
    gameMap, stats, status = _setup(resolve, test_config, tmp_path)

    initial = stats.getRoomsExplored()
    for x in range(5):
        _simulate_load_or_generate(gameMap, stats, status, x, 0)

    assert stats.getRoomsExplored() == initial + 5


def test_loaded_from_disk_room_does_not_increment(resolve, test_config, tmp_path):
    """A room that already exists on disk should not count as explored."""
    import json
    import os

    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.gridSize = 3

    gameMap, stats, status = _setup(resolve, test_config, tmp_path)

    # Generate a room and save it to disk so it appears as a pre-existing save
    room = gameMap.generateNewRoom(3, 3)
    # Consume the new-room flag to simulate it having been visited before
    gameMap.consumeIsNewRoom(3, 3)

    # Write a minimal room JSON so getRoom() finds a file on disk
    rooms_dir = tmp_path / "rooms"
    rooms_dir.mkdir(parents=True, exist_ok=True)
    from world.roomJsonReaderWriter import RoomJsonReaderWriter

    rw = RoomJsonReaderWriter(test_config.gridSize, MagicMock(), MagicMock(), test_config)
    room_path = str(rooms_dir / "room_3_3.json")
    rw.saveRoom(room, room_path)

    # Remove from in-memory map to simulate a fresh load
    gameMap.rooms.remove(room)
    del gameMap._roomIndex[(3, 3)]

    initial = stats.getRoomsExplored()
    _simulate_load_or_generate(gameMap, stats, status, 3, 3)

    # Loading a room from disk is not a new discovery
    assert stats.getRoomsExplored() == initial
