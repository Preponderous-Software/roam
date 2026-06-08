import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from jsonPersistence import readJsonFile
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
