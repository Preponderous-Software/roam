import sys
from pathlib import Path

import appPaths


def test_is_frozen_false_when_running_from_source():
    assert appPaths.isFrozen() is False


def test_bundle_directory_is_repo_root_from_source():
    expected = str(Path(appPaths.__file__).resolve().parents[1])
    assert appPaths.getBundleDirectory() == expected


def test_bundle_directory_uses_meipass_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert appPaths.isFrozen() is True
    assert appPaths.getBundleDirectory() == str(tmp_path)


def test_prepare_working_directory_noop_from_source(monkeypatch):
    calls = []
    monkeypatch.setattr(appPaths.os, "chdir", lambda path: calls.append(path))
    appPaths.prepareWorkingDirectory()
    assert calls == []


def test_prepare_working_directory_chdirs_to_bundle_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    calls = []
    monkeypatch.setattr(appPaths.os, "chdir", lambda path: calls.append(path))
    appPaths.prepareWorkingDirectory()
    assert calls == [str(tmp_path)]
