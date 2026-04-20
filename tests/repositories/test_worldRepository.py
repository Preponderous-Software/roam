import pytest
from unittest.mock import MagicMock, patch

from repositories.worldRepository import WorldRepository
from config.config import Config
from world.roomJsonReaderWriter import RoomJsonReaderWriter


def makeRepo(tmp_path):
    config = MagicMock(spec=Config)
    config.pathToSaveDirectory = str(tmp_path)
    rjrw = MagicMock(spec=RoomJsonReaderWriter)
    rjrw.generateJsonForRoom.return_value = {"entities": [], "name": "Room_0_0", "x": 0, "y": 0}
    return WorldRepository(config, rjrw), rjrw


def makeRoom(x=0, y=0):
    room = MagicMock()
    room.getX.return_value = x
    room.getY.return_value = y
    return room


def test_buildRoomPath(tmp_path):
    repo, _ = makeRepo(tmp_path)
    path = repo.buildRoomPath(3, -2)
    assert "room_3_-2.json" in path


def test_saveRoom_creates_file(tmp_path):
    repo, _ = makeRepo(tmp_path)
    room = makeRoom(0, 0)
    repo.saveRoom(room)
    path = tmp_path / "rooms" / "room_0_0.json"
    assert path.exists()


def test_saveRoomJson_creates_file(tmp_path):
    repo, _ = makeRepo(tmp_path)
    repo.saveRoomJson({"entities": []}, str(tmp_path / "rooms" / "room_1_1.json"))
    path = tmp_path / "rooms" / "room_1_1.json"
    assert path.exists()
