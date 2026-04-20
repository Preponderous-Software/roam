# @author Copilot
# @since April 20th, 2026
import json
import os
import jsonschema

from config.config import Config
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


class CodexJsonReaderWriter:
    def __init__(self, config: Config):
        self.config = config

    def save(self, discoveredEntities):
        data = {"discoveredEntities": list(discoveredEntities)}

        with open("schemas/codex.json") as f:
            schema = json.load(f)
        try:
            jsonschema.validate(data, schema)
        except jsonschema.exceptions.ValidationError as e:
            _logger.error("codex validation error on save", error=str(e))

        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        path = self.config.pathToSaveDirectory + "/codex.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        _logger.info("codex saved", path=path)

    def load(self):
        path = self.config.pathToSaveDirectory + "/codex.json"
        if not os.path.exists(path):
            return None

        try:
            with open(path) as f:
                data = json.load(f)

            with open("schemas/codex.json") as f:
                schema = json.load(f)
            jsonschema.validate(data, schema)
        except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
            _logger.error("codex validation error on load", error=str(e), path=path)
            return None

        _logger.info("codex loaded", path=path)
        return data["discoveredEntities"]
