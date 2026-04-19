# @author Daniel McCoy Stephenson
import json
import os
import jsonschema

from appContainer import component
from config.config import Config


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
        jsonStats = {}

        jsonStats["score"] = str(self.getScore())
        jsonStats["roomsExplored"] = str(self.getRoomsExplored())
        jsonStats["foodEaten"] = str(self.getFoodEaten())
        jsonStats["numberOfDeaths"] = str(self.getNumberOfDeaths())

        # validate
        statsSchema = json.load(open("schemas/stats.json"))
        jsonschema.validate(jsonStats, statsSchema)

        path = self.config.pathToSaveDirectory + "/stats.json"
        json.dump(jsonStats, open(path, "w"), indent=4)

    def load(self):
        path = self.config.pathToSaveDirectory + "/stats.json"
        if not os.path.exists(path):
            return
        jsonStats = json.load(open(path))

        # validate
        statsSchema = json.load(open("schemas/stats.json"))
        jsonschema.validate(jsonStats, statsSchema)

        self.setScore(int(jsonStats["score"]))
        self.setRoomsExplored(int(jsonStats["roomsExplored"]))
        self.setFoodEaten(int(jsonStats["foodEaten"]))
        self.setNumberOfDeaths(int(jsonStats["numberOfDeaths"]))
