# @author Daniel McCoy Stephenson
from appContainer import component

import json
import os
import jsonschema

from config.config import Config
from gameLogging.logger import getLogger
from schemaCache import loadSchema

_logger = getLogger(__name__)


@component
class GoalsJsonReaderWriter:
    def __init__(self, config: Config):
        self.config = config

    def save(self, completedIdentifiers):
        data = {"completedGoals": list(completedIdentifiers)}

        try:
            jsonschema.validate(data, loadSchema("goals.json"))
        except jsonschema.exceptions.ValidationError as e:
            _logger.error("goals validation error on save", error=str(e))

        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        path = self.config.pathToSaveDirectory + "/goals.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        _logger.info("goals saved", path=path)

    def load(self):
        path = self.config.pathToSaveDirectory + "/goals.json"
        if not os.path.exists(path):
            return []

        try:
            with open(path) as f:
                data = json.load(f)

            jsonschema.validate(data, loadSchema("goals.json"))
        except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
            _logger.error("goals validation error on load", error=str(e), path=path)
            return []

        _logger.info("goals loaded", path=path)
        return data["completedGoals"]
