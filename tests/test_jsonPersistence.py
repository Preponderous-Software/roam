import logging
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from jsonPersistence import (
    noteBrowserWorldRemoved,
    readJsonFile,
    writeJsonAtomically,
)
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


def test_writeJsonAtomically_syncs_browser_saves_when_available(monkeypatch, tmp_path):
    path = str(tmp_path / "out.json")
    syncSaves = MagicMock()
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(syncSaves=syncSaves))

    writeJsonAtomically(path, {"ok": True})

    syncSaves.assert_called_once_with()


# --- writeJsonAtomically: filesystems without fsync / rename (OPFS) ----------


def _tempLeftovers(directory):
    return [name for name in os.listdir(str(directory)) if name.endswith(".tmp")]


def test_writeJsonAtomically_tolerates_unsupported_fsync(monkeypatch, tmp_path):
    def noFsync(fd):
        raise OSError("fsync not supported")

    monkeypatch.setattr(os, "fsync", noFsync)
    path = str(tmp_path / "out.json")

    writeJsonAtomically(path, {"ok": True})

    assert readJsonFile(path) == {"ok": True}
    assert _tempLeftovers(tmp_path) == []


def test_writeJsonAtomically_falls_back_to_direct_write_when_rename_fails(
    monkeypatch, tmp_path
):
    path = str(tmp_path / "save.json")
    writeJsonAtomically(path, {"version": 1})

    def noReplace(src, dst):
        raise OSError("rename not supported")

    monkeypatch.setattr(os, "replace", noReplace)

    writeJsonAtomically(path, {"version": 2})

    # The new contents land in place, and the unused temp file is removed.
    assert readJsonFile(path) == {"version": 2}
    assert _tempLeftovers(tmp_path) == []


def test_writeJsonAtomically_direct_write_fallback_still_syncs_browser_saves(
    monkeypatch, tmp_path
):
    def noReplace(src, dst):
        raise OSError("rename not supported")

    monkeypatch.setattr(os, "replace", noReplace)
    syncSaves = MagicMock()
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(syncSaves=syncSaves))

    writeJsonAtomically(str(tmp_path / "out.json"), {"ok": True})

    syncSaves.assert_called_once_with()


def test_writeJsonAtomically_direct_write_survives_failed_temp_cleanup(
    monkeypatch, tmp_path
):
    def noReplace(src, dst):
        raise OSError("rename not supported")

    def noRemove(path):
        raise OSError("remove not supported")

    monkeypatch.setattr(os, "replace", noReplace)
    monkeypatch.setattr(os, "remove", noRemove)
    path = str(tmp_path / "out.json")

    writeJsonAtomically(path, {"ok": True})

    assert readJsonFile(path) == {"ok": True}


def test_writeJsonAtomically_reraises_serialization_error_when_temp_cleanup_fails(
    monkeypatch, tmp_path
):
    # A failed os.remove of the temp file must not mask the original error.
    path = str(tmp_path / "save.json")
    writeJsonAtomically(path, {"version": 1})

    def noRemove(path):
        raise OSError("remove not supported")

    monkeypatch.setattr(os, "remove", noRemove)

    with pytest.raises(TypeError):
        writeJsonAtomically(path, {"bad": {1, 2, 3}})

    assert readJsonFile(path) == {"version": 1}


# --- writeJsonAtomically: the browser sync hook -------------------------------


def test_writeJsonAtomically_without_sync_hook_writes_quietly(
    monkeypatch, tmp_path, caplog
):
    # Inside Pyodide before the Worker installs syncSaves, "js" has no hook.
    # That is expected, not a failure, so nothing is logged.
    caplog.set_level(logging.WARNING)
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace())
    path = str(tmp_path / "out.json")

    writeJsonAtomically(path, {"ok": True})

    assert readJsonFile(path) == {"ok": True}
    assert "could not sync browser saves" not in caplog.text


def test_writeJsonAtomically_survives_a_failing_sync_hook(
    monkeypatch, tmp_path, caplog
):
    def broken():
        raise RuntimeError("worker gone")

    caplog.set_level(logging.WARNING)
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(syncSaves=broken))
    path = str(tmp_path / "out.json")

    writeJsonAtomically(path, {"ok": True})  # must not raise

    assert readJsonFile(path) == {"ok": True}
    assert "could not sync browser saves" in caplog.text


# --- noteBrowserWorldRemoved: a deleted or renamed world, in the browser ------


def test_noteBrowserWorldRemoved_is_a_no_op_off_the_browser(monkeypatch):
    monkeypatch.delitem(sys.modules, "js", raising=False)
    noteBrowserWorldRemoved("/saves/old_world")  # must not raise


def test_noteBrowserWorldRemoved_names_the_world_then_syncs(monkeypatch):
    calls = []
    js = SimpleNamespace(
        noteSavedWorldRemoved=lambda name: calls.append(("note", name)),
        syncSaves=lambda: calls.append(("sync",)),
    )
    monkeypatch.setitem(sys.modules, "js", js)

    noteBrowserWorldRemoved("/saves/old_world/")

    # Named before the sync, so the sync carries the removal.
    assert calls == [("note", "old_world"), ("sync",)]


def test_noteBrowserWorldRemoved_without_the_hook_does_not_sync(monkeypatch):
    # After a failed restore the Worker installs neither hook.
    syncSaves = MagicMock()
    monkeypatch.setitem(sys.modules, "js", SimpleNamespace(syncSaves=syncSaves))
    noteBrowserWorldRemoved("/saves/old_world")
    syncSaves.assert_not_called()


def test_noteBrowserWorldRemoved_survives_a_failing_hook(monkeypatch):
    def broken(name):
        raise RuntimeError("worker gone")

    syncSaves = MagicMock()
    js = SimpleNamespace(noteSavedWorldRemoved=broken, syncSaves=syncSaves)
    monkeypatch.setitem(sys.modules, "js", js)
    noteBrowserWorldRemoved("/saves/old_world")  # must not raise
    syncSaves.assert_not_called()
