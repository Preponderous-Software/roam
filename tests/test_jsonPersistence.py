import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest

from jsonPersistence import readJsonFile, writeJsonAtomically
from stats.stats import Stats
from world.tickCounter import TickCounter


def test_readJsonFile_returns_parsed_data(tmp_path):
    path = str(tmp_path / "data.json")
    with open(path, "w") as f:
        f.write('{"a": 1, "b": [2, 3]}')
    assert readJsonFile(path) == {"a": 1, "b": [2, 3]}


def test_readJsonFile_missing_returns_default(tmp_path):
    path = str(tmp_path / "does-not-exist.json")
    assert readJsonFile(path) is None
    assert readJsonFile(path, default={}) == {}


def test_readJsonFile_corrupt_returns_default(tmp_path):
    path = str(tmp_path / "corrupt.json")
    with open(path, "w") as f:
        f.write("this is not json {{{")
    assert readJsonFile(path) is None
    assert readJsonFile(path, default=[]) == []


def test_readJsonFile_truncated_returns_default(tmp_path):
    # A save interrupted mid-write leaves a partial document on disk.
    path = str(tmp_path / "truncated.json")
    with open(path, "w") as f:
        f.write('{"score": "10", "roomsExpl')
    assert readJsonFile(path) is None


def test_stats_load_tolerates_corrupt_file(test_config, tmp_path):
    # Regression for #370: a corrupt stats.json must not crash on load.
    test_config.pathToSaveDirectory = str(tmp_path)
    with open(str(tmp_path / "stats.json"), "w") as f:
        f.write("{ truncated")

    stats = Stats(test_config)
    stats.load()  # would raise json.JSONDecodeError before the fix

    assert stats.getScore() == 0
    assert stats.getNumberOfDeaths() == 0


def test_tickCounter_load_tolerates_corrupt_file(test_config, tmp_path):
    # Regression for #370: a corrupt tick.json must not crash on load.
    test_config.pathToSaveDirectory = str(tmp_path)
    with open(str(tmp_path / "tick.json"), "w") as f:
        f.write("not json")

    tickCounter = TickCounter(test_config)
    before = tickCounter.getTick()
    tickCounter.load()  # would raise json.JSONDecodeError before the fix

    assert tickCounter.getTick() == before


def test_stats_load_still_reads_a_valid_file(test_config, tmp_path):
    # The tolerant read must not break the happy path: a good file still loads.
    test_config.pathToSaveDirectory = str(tmp_path)
    stats = Stats(test_config)
    stats.setScore(7)
    stats.setNumberOfDeaths(2)
    stats.save()

    reloaded = Stats(test_config)
    reloaded.load()
    assert reloaded.getScore() == 7
    assert reloaded.getNumberOfDeaths() == 2


def test_writeJsonAtomically_round_trips(tmp_path):
    path = str(tmp_path / "out.json")
    writeJsonAtomically(path, {"x": 1, "y": [2, 3]})
    assert readJsonFile(path) == {"x": 1, "y": [2, 3]}


def test_writeJsonAtomically_creates_missing_directory(tmp_path):
    path = str(tmp_path / "nested" / "dir" / "out.json")
    writeJsonAtomically(path, {"ok": True})
    assert readJsonFile(path) == {"ok": True}


def test_writeJsonAtomically_leaves_no_temp_file_on_success(tmp_path):
    path = str(tmp_path / "out.json")
    writeJsonAtomically(path, {"ok": True})
    leftovers = [name for name in os.listdir(str(tmp_path)) if name.endswith(".tmp")]
    assert leftovers == []


def test_writeJsonAtomically_preserves_good_file_when_serialization_fails(tmp_path):
    # The core #370 guarantee: a failed save must not destroy the previous file.
    path = str(tmp_path / "save.json")
    writeJsonAtomically(path, {"version": 1})

    with pytest.raises(TypeError):
        writeJsonAtomically(path, {"bad": {1, 2, 3}})  # a set isn't JSON-serializable

    # Old contents intact, and the aborted write left no temp file behind.
    assert readJsonFile(path) == {"version": 1}
    leftovers = [name for name in os.listdir(str(tmp_path)) if name.endswith(".tmp")]
    assert leftovers == []
