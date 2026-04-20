import json
import os
import tempfile
from unittest.mock import MagicMock

from src.codex.codex import Codex
from src.codex.codexJsonReaderWriter import CodexJsonReaderWriter


def test_initialization():
    codex = Codex()
    assert codex.getDiscoveredEntities() == []
    assert codex.hasDiscovered("Bear") is False


def test_discover_new_entity():
    codex = Codex()
    result = codex.discover("Bear")
    assert result is True
    assert codex.hasDiscovered("Bear") is True


def test_discover_duplicate_entity():
    codex = Codex()
    codex.discover("Bear")
    result = codex.discover("Bear")
    assert result is False


def test_get_discovered_entities_sorted():
    codex = Codex()
    codex.discover("Chicken")
    codex.discover("Bear")
    assert codex.getDiscoveredEntities() == ["Bear", "Chicken"]


def test_has_discovered():
    codex = Codex()
    assert codex.hasDiscovered("Bear") is False
    codex.discover("Bear")
    assert codex.hasDiscovered("Bear") is True
    assert codex.hasDiscovered("Chicken") is False


def test_reset():
    codex = Codex()
    codex.discover("Bear")
    codex.reset()
    assert codex.getDiscoveredEntities() == []
    assert codex.hasDiscovered("Bear") is False


def test_set_discovered():
    codex = Codex()
    codex.setDiscovered(["Bear", "Chicken"])
    assert codex.hasDiscovered("Bear") is True
    assert codex.hasDiscovered("Chicken") is True
    assert codex.getDiscoveredEntities() == ["Bear", "Chicken"]


def test_persistence_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = MagicMock()
        config.pathToSaveDirectory = tmpdir

        # Save
        codex = Codex()
        codex.discover("Bear")
        codex.discover("Chicken")

        writer = CodexJsonReaderWriter(config)
        writer.save(codex.getDiscoveredEntities())

        # Verify file exists
        assert os.path.exists(os.path.join(tmpdir, "codex.json"))

        # Load
        entities = writer.load()
        assert entities is not None
        assert sorted(entities) == ["Bear", "Chicken"]


def test_load_nonexistent_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = MagicMock()
        config.pathToSaveDirectory = tmpdir

        reader = CodexJsonReaderWriter(config)
        result = reader.load()
        assert result is None


def test_persistence_validates_schema():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = MagicMock()
        config.pathToSaveDirectory = tmpdir

        writer = CodexJsonReaderWriter(config)
        writer.save(["Bear"])

        # Read the raw file and verify structure
        with open(os.path.join(tmpdir, "codex.json")) as f:
            data = json.load(f)

        assert "discoveredEntities" in data
        assert data["discoveredEntities"] == ["Bear"]
