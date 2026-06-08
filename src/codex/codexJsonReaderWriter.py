# @author Copilot
# @since April 20th, 2026
import json
import os
import jsonschema

from config.config import Config
from gameLogging.logger import getLogger
from schemaCache import loadSchema

_logger = getLogger(__name__)


class CodexJsonReaderWriter:
    def __init__(self, config: Config):
        self.config = config

    def save(self, discoveredEntities):
        data = {"discoveredEntities": list(discoveredEntities)}

        try:
            jsonschema.validate(data, loadSchema("codex.json"))
        except jsonschema.exceptions.ValidationError as e:
            _logger.error(
                "codex validation failed; aborting save to preserve existing file",
                error=str(e),
            )
            return False

        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        path = self.config.pathToSaveDirectory + "/codex.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        _logger.info("codex saved", path=path)
        return True

    def load(self):
        path = self.config.pathToSaveDirectory + "/codex.json"
        if not os.path.exists(path):
            return None

        try:
            with open(path) as f:
                data = json.load(f)

            jsonschema.validate(data, loadSchema("codex.json"))
        except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
            _logger.error("codex validation error on load", error=str(e), path=path)
            return None

        _logger.info("codex loaded", path=path)
        return data["discoveredEntities"]
