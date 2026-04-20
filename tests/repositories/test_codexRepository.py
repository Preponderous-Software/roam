import json
import os
import pytest
from unittest.mock import MagicMock

from config.config import Config
from repositories.codexRepository import CodexRepository


def makeRepo(tmp_path):
    config = MagicMock(spec=Config)
    config.pathToSaveDirectory = str(tmp_path)
    return CodexRepository(config)


def makeCodex(entities=None):
    codex = MagicMock()
    codex.getDiscoveredEntities.return_value = entities or []
    return codex


def test_save_creates_json_file(tmp_path):
    repo = makeRepo(tmp_path)
    codex = makeCodex(["Chicken", "Bear"])
    repo.save(codex)
    path = tmp_path / "codex.json"
    assert path.exists()


def test_save_correct_entities(tmp_path):
    repo = makeRepo(tmp_path)
    codex = makeCodex(["Chicken", "Bear"])
    repo.save(codex)
    path = tmp_path / "codex.json"
    with open(path) as f:
        data = json.load(f)
    assert "Chicken" in data["discoveredEntities"]
    assert "Bear" in data["discoveredEntities"]


def test_load_returns_entities(tmp_path):
    repo = makeRepo(tmp_path)
    codex = makeCodex(["Chicken"])
    repo.save(codex)
    result = repo.load()
    assert result == ["Chicken"]


def test_load_no_file_returns_none(tmp_path):
    repo = makeRepo(tmp_path)
    result = repo.load()
    assert result is None


def test_save_empty_entities(tmp_path):
    repo = makeRepo(tmp_path)
    codex = makeCodex([])
    repo.save(codex)
    result = repo.load()
    assert result == []
