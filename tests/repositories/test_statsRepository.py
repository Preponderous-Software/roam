import json
import os
import pytest
from unittest.mock import MagicMock

from config.config import Config
from repositories.statsRepository import StatsRepository


def makeStats(score=10, roomsExplored=5, foodEaten=3, numberOfDeaths=1):
    stats = MagicMock()
    stats.getScore.return_value = score
    stats.getRoomsExplored.return_value = roomsExplored
    stats.getFoodEaten.return_value = foodEaten
    stats.getNumberOfDeaths.return_value = numberOfDeaths
    return stats


def makeRepo(tmp_path):
    config = MagicMock(spec=Config)
    config.pathToSaveDirectory = str(tmp_path)
    return StatsRepository(config)


def test_save_creates_json_file(tmp_path):
    repo = makeRepo(tmp_path)
    stats = makeStats()
    repo.save(stats)
    path = tmp_path / "stats.json"
    assert path.exists()


def test_save_correct_values(tmp_path):
    repo = makeRepo(tmp_path)
    stats = makeStats(score=42, roomsExplored=7, foodEaten=2, numberOfDeaths=3)
    repo.save(stats)
    path = tmp_path / "stats.json"
    with open(path) as f:
        data = json.load(f)
    assert data["score"] == "42"
    assert data["roomsExplored"] == "7"
    assert data["foodEaten"] == "2"
    assert data["numberOfDeaths"] == "3"


def test_load_restores_values(tmp_path):
    repo = makeRepo(tmp_path)
    stats = makeStats(score=99, roomsExplored=11, foodEaten=6, numberOfDeaths=2)
    repo.save(stats)

    target = MagicMock()
    repo.load(target)

    target.setScore.assert_called_once_with(99)
    target.setRoomsExplored.assert_called_once_with(11)
    target.setFoodEaten.assert_called_once_with(6)
    target.setNumberOfDeaths.assert_called_once_with(2)


def test_load_no_file_does_nothing(tmp_path):
    repo = makeRepo(tmp_path)
    target = MagicMock()
    repo.load(target)
    target.setScore.assert_not_called()


def test_roundtrip(tmp_path, resolve):
    from stats.stats import Stats
    stats = resolve(Stats)
    stats.setScore(55)
    stats.setRoomsExplored(3)
    stats.setFoodEaten(8)
    stats.setNumberOfDeaths(1)
    stats.save()
    stats.setScore(0)
    stats.load()
    assert stats.getScore() == 55
    assert stats.getRoomsExplored() == 3
    assert stats.getFoodEaten() == 8
    assert stats.getNumberOfDeaths() == 1
