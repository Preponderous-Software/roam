# @author Copilot
# @since April 20th, 2026
import json
import os

import jsonschema

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


@component
class StatsRepository:
    """Handles all persistence for game statistics."""

    def __init__(self, config: Config):
        self.config = config

    def save(self, stats):
        jsonStats = {
            "score": str(stats.getScore()),
            "roomsExplored": str(stats.getRoomsExplored()),
            "foodEaten": str(stats.getFoodEaten()),
            "numberOfDeaths": str(stats.getNumberOfDeaths()),
        }

        with open("schemas/stats.json") as f:
            statsSchema = json.load(f)
        jsonschema.validate(jsonStats, statsSchema)

        path = self.config.pathToSaveDirectory + "/stats.json"
        with open(path, "w") as f:
            json.dump(jsonStats, f, indent=4)
        _logger.info("stats saved", path=path)

    def load(self, stats):
        path = self.config.pathToSaveDirectory + "/stats.json"
        if not os.path.exists(path):
            return

        with open(path) as f:
            jsonStats = json.load(f)

        with open("schemas/stats.json") as f:
            statsSchema = json.load(f)
        jsonschema.validate(jsonStats, statsSchema)

        stats.setScore(int(jsonStats["score"]))
        stats.setRoomsExplored(int(jsonStats["roomsExplored"]))
        stats.setFoodEaten(int(jsonStats["foodEaten"]))
        stats.setNumberOfDeaths(int(jsonStats["numberOfDeaths"]))
        _logger.info("stats loaded", path=path)
