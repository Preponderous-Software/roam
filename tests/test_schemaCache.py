import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from unittest.mock import patch

from schemaCache import loadSchema


def test_loadSchema_returns_parsed_schema_dict():
    loadSchema.cache_clear()
    schema = loadSchema("tick.json")
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    assert "tick" in schema["properties"]


def test_loadSchema_returns_the_same_cached_object():
    loadSchema.cache_clear()
    first = loadSchema("stats.json")
    second = loadSchema("stats.json")
    assert first is second


def test_loadSchema_reads_each_file_from_disk_only_once():
    loadSchema.cache_clear()
    realOpen = open
    opened = []

    def countingOpen(path, *args, **kwargs):
        opened.append(path)
        return realOpen(path, *args, **kwargs)

    with patch("builtins.open", side_effect=countingOpen):
        loadSchema("codex.json")
        loadSchema("codex.json")
        loadSchema("codex.json")

    assert opened.count("schemas/codex.json") == 1
