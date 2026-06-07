import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from unittest.mock import MagicMock

import jsonschema


def _raiseValidationError(*args, **kwargs):
    raise jsonschema.exceptions.ValidationError("forced validation failure")


def _makeWorldScreen(test_config, tmp_path):
    from screen.worldScreen import WorldScreen

    test_config.pathToSaveDirectory = str(tmp_path)
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = test_config
    ws.status = MagicMock()
    ws.codex = MagicMock()
    ws.codex.getDiscoveredEntities.return_value = ["Chicken"]
    return ws


def test_saveCodexToFile_surfaces_status_on_validation_failure(
    test_config, tmp_path, monkeypatch
):
    ws = _makeWorldScreen(test_config, tmp_path)

    monkeypatch.setattr(jsonschema, "validate", _raiseValidationError)
    ws.saveCodexToFile()

    ws.status.set.assert_called_once_with("Could not save codex (invalid data)")


def test_saveCodexToFile_does_not_surface_on_success(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path)

    ws.saveCodexToFile()

    ws.status.set.assert_not_called()
