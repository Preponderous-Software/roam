import json
import pytest
from unittest.mock import MagicMock

from repositories.playerRepository import PlayerRepository
from config.config import Config
from player.player import Player


def makeRepo(tmp_path):
    config = MagicMock(spec=Config)
    config.pathToSaveDirectory = str(tmp_path)
    player = MagicMock(spec=Player)
    player.getLocationID.return_value = "0"
    player.getEnergy.return_value = 100
    return PlayerRepository(config, player), player


def makeRoom(x=0, y=0, grid=None):
    room = MagicMock()
    room.getX.return_value = x
    room.getY.return_value = y
    if grid is None:
        grid = MagicMock()
        location = MagicMock()
        grid.getLocation.return_value = location
    room.getGrid.return_value = grid
    return room


def test_saveLocation_creates_file(tmp_path):
    repo, player = makeRepo(tmp_path)
    room = makeRoom()
    repo.saveLocation(room)
    path = tmp_path / "playerLocation.json"
    assert path.exists()


def test_saveLocation_correct_values(tmp_path):
    repo, player = makeRepo(tmp_path)
    room = makeRoom(x=2, y=-3)
    repo.saveLocation(room)
    path = tmp_path / "playerLocation.json"
    with open(path) as f:
        data = json.load(f)
    assert data["roomX"] == 2
    assert data["roomY"] == -3


def test_saveAttributes_creates_file(tmp_path):
    repo, player = makeRepo(tmp_path)
    repo.saveAttributes()
    path = tmp_path / "playerAttributes.json"
    assert path.exists()


def test_saveAttributes_correct_energy(tmp_path):
    repo, player = makeRepo(tmp_path)
    player.getEnergy.return_value = 75
    repo.saveAttributes()
    path = tmp_path / "playerAttributes.json"
    with open(path) as f:
        data = json.load(f)
    assert data["energy"] == 75


def test_loadAttributes_no_file_does_nothing(tmp_path):
    repo, player = makeRepo(tmp_path)
    repo.loadAttributes()
    player.setEnergy.assert_not_called()


def test_loadAttributes_restores_energy(tmp_path):
    repo, player = makeRepo(tmp_path)
    player.getEnergy.return_value = 80
    repo.saveAttributes()
    repo.loadAttributes()
    player.setEnergy.assert_called_once_with(80)


def test_loadLocation_no_file_returns_none(tmp_path):
    repo, player = makeRepo(tmp_path)
    result = repo.loadLocation(MagicMock())
    assert result is None
