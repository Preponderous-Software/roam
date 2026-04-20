# @author Daniel McCoy Stephenson
import json
import os
import jsonschema

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


@component
class Stats:
    def __init__(self, config: Config):
        self.config = config
        self.score = 0
        self.roomsExplored = 0
        self.foodEaten = 0
        self.numberOfDeaths = 0

    def getScore(self):
        return self.score

    def setScore(self, score):
        self.score = score

    def incrementScore(self):
        self.score += 1

    def getRoomsExplored(self):
        return self.roomsExplored

    def setRoomsExplored(self, roomsExplored):
        self.roomsExplored = roomsExplored

    def incrementRoomsExplored(self):
        self.roomsExplored += 1

    def getFoodEaten(self):
        return self.foodEaten

    def setFoodEaten(self, applesEaten):
        self.foodEaten = applesEaten

    def incrementFoodEaten(self):
        self.foodEaten += 1

    def getNumberOfDeaths(self):
        return self.numberOfDeaths

    def setNumberOfDeaths(self, numberOfDeaths):
        self.numberOfDeaths = numberOfDeaths

    def incrementNumberOfDeaths(self):
        self.numberOfDeaths += 1

    def save(self):
        jsonStats = {
            "score": str(self.getScore()),
            "roomsExplored": str(self.getRoomsExplored()),
            "foodEaten": str(self.getFoodEaten()),
            "numberOfDeaths": str(self.getNumberOfDeaths()),
        }

        with open("schemas/stats.json") as f:
            statsSchema = json.load(f)
        jsonschema.validate(jsonStats, statsSchema)

        path = self.config.pathToSaveDirectory + "/stats.json"
        with open(path, "w") as f:
            json.dump(jsonStats, f, indent=4)
        _logger.info("stats saved", path=path)

    def load(self):
        path = self.config.pathToSaveDirectory + "/stats.json"
        if not os.path.exists(path):
            return

        with open(path) as f:
            jsonStats = json.load(f)

        with open("schemas/stats.json") as f:
            statsSchema = json.load(f)
        jsonschema.validate(jsonStats, statsSchema)

        self.setScore(int(jsonStats["score"]))
        self.setRoomsExplored(int(jsonStats["roomsExplored"]))
        self.setFoodEaten(int(jsonStats["foodEaten"]))
        self.setNumberOfDeaths(int(jsonStats["numberOfDeaths"]))
        _logger.info("stats loaded", path=path)
