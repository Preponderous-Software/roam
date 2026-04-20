import pytest
from unittest.mock import MagicMock

from services.worldService import WorldService
from config.config import Config
from stats.stats import Stats
from ui.status import Status


def makeService():
    config = MagicMock(spec=Config)
    stats = MagicMock(spec=Stats)
    status = MagicMock(spec=Status)
    return WorldService(config, stats, status), stats, status


def makeMap(hasRoom=False, room=None):
    mapMock = MagicMock()
    if room is None:
        room = MagicMock()
    mapMock.hasRoom.return_value = hasRoom
    mapMock.getRoom.return_value = room if hasRoom else -1
    mapMock.generateNewRoom.return_value = room
    return mapMock, room


def test_getOrLoadRoom_existing(tmp_path):
    service, _, _ = makeService()
    room = MagicMock()
    mapMock, _ = makeMap(hasRoom=True, room=room)
    result = service.getOrLoadRoom(0, 0, mapMock)
    assert result is room


def test_getOrLoadRoom_generates_new(tmp_path):
    service, _, _ = makeService()
    room = MagicMock()
    mapMock, _ = makeMap(hasRoom=False, room=room)
    result = service.getOrLoadRoom(0, 0, mapMock)
    assert result is room
    mapMock.generateNewRoom.assert_called_once_with(0, 0)


def test_loadOrGenerateRoom_existing_cached():
    service, stats, status = makeService()
    room = MagicMock()
    mapMock = MagicMock()
    mapMock.hasRoom.return_value = True
    mapMock.getRoom.return_value = room
    result = service.loadOrGenerateRoom(1, 1, mapMock)
    assert result is room
    stats.incrementRoomsExplored.assert_not_called()


def test_loadOrGenerateRoom_existing_uncached_sets_status():
    service, stats, status = makeService()
    room = MagicMock()
    mapMock = MagicMock()
    mapMock.hasRoom.return_value = False
    mapMock.getRoom.return_value = room
    result = service.loadOrGenerateRoom(1, 1, mapMock)
    assert result is room
    status.set.assert_called_with("Area loaded")


def test_loadOrGenerateRoom_new_increments_stats():
    service, stats, status = makeService()
    room = MagicMock()
    mapMock = MagicMock()
    mapMock.hasRoom.return_value = False
    mapMock.getRoom.return_value = -1
    mapMock.generateNewRoom.return_value = room
    result = service.loadOrGenerateRoom(2, 2, mapMock)
    assert result is room
    stats.incrementScore.assert_called_once()
    stats.incrementRoomsExplored.assert_called_once()
    status.set.assert_called_with("New area discovered")
