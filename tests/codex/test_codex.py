import json
import os

from codex.codex import Codex
from codex.codexJsonReaderWriter import CodexJsonReaderWriter


def test_initialization(resolve):
    codex = resolve(Codex)
    assert codex.getDiscoveredEntities() == []
    assert codex.hasDiscovered("Bear") is False


def test_discover_new_entity(resolve):
    codex = resolve(Codex)
    result = codex.discover("Bear")
    assert result is True
    assert codex.hasDiscovered("Bear") is True


def test_discover_duplicate_entity(resolve):
    codex = resolve(Codex)
    codex.discover("Bear")
    result = codex.discover("Bear")
    assert result is False


def test_get_discovered_entities_sorted(resolve):
    codex = resolve(Codex)
    codex.discover("Chicken")
    codex.discover("Bear")
    assert codex.getDiscoveredEntities() == ["Bear", "Chicken"]


def test_has_discovered(resolve):
    codex = resolve(Codex)
    assert codex.hasDiscovered("Bear") is False
    codex.discover("Bear")
    assert codex.hasDiscovered("Bear") is True
    assert codex.hasDiscovered("Chicken") is False


def test_reset(resolve):
    codex = resolve(Codex)
    codex.discover("Bear")
    codex.reset()
    assert codex.getDiscoveredEntities() == []
    assert codex.hasDiscovered("Bear") is False


def test_set_discovered(resolve):
    codex = resolve(Codex)
    codex.setDiscovered(["Bear", "Chicken"])
    assert codex.hasDiscovered("Bear") is True
    assert codex.hasDiscovered("Chicken") is True
    assert codex.getDiscoveredEntities() == ["Bear", "Chicken"]


def test_persistence_round_trip(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)

    codex = resolve(Codex)
    codex.discover("Bear")
    codex.discover("Chicken")

    writer = resolve(CodexJsonReaderWriter)
    writer.save(codex.getDiscoveredEntities())

    assert os.path.exists(os.path.join(str(tmp_path), "codex.json"))

    entities = writer.load()
    assert entities is not None
    assert sorted(entities) == ["Bear", "Chicken"]


def test_load_nonexistent_file(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    reader = resolve(CodexJsonReaderWriter)
    result = reader.load()
    assert result is None


def test_persistence_validates_schema(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)

    writer = resolve(CodexJsonReaderWriter)
    writer.save(["Bear"])

    with open(os.path.join(str(tmp_path), "codex.json")) as f:
        data = json.load(f)

    assert "discoveredEntities" in data
    assert data["discoveredEntities"] == ["Bear"]
