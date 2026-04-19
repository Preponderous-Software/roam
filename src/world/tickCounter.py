import json
import time

import jsonschema

from appContainer import component
from config.config import Config


@component
class TickCounter:
    def __init__(self, config: Config):
        self.config = config
        self.tick = 0
        self.measuredTicksPerSecond = 0
        self.lastTimestamp = time.time()
        self.highestMeasuredTicksPerSecond = 0

    def getTick(self):
        return self.tick

    def incrementTick(self):
        self.tick += 1
        self.updateMeasuredTicksPerSecond()

    def updateMeasuredTicksPerSecond(self):
        millisecondsSinceLastTick = (time.time() - self.lastTimestamp) * 1000
        warningThreshold = 500
        if millisecondsSinceLastTick > warningThreshold:
            print(
                "WARNING: Tick took "
                + str(int(millisecondsSinceLastTick))
                + " milliseconds to complete. (tick="
                + str(self.tick)
                + ")"
            )
        currentTimestamp = time.time()
        timeElapsed = currentTimestamp - self.lastTimestamp
        self.lastTimestamp = currentTimestamp
        self.measuredTicksPerSecond = 1 / timeElapsed

        if self.measuredTicksPerSecond > self.highestMeasuredTicksPerSecond:
            self.highestMeasuredTicksPerSecond = self.measuredTicksPerSecond

    def getMeasuredTicksPerSecond(self):
        return self.measuredTicksPerSecond

    def getHighestMeasuredTicksPerSecond(self):
        return self.highestMeasuredTicksPerSecond

    def save(self):
        jsonTick = {}
        jsonTick["tick"] = self.getTick()

        # validate
        tickSchema = json.load(open("schemas/tick.json"))
        jsonschema.validate(jsonTick, tickSchema)

        path = self.config.pathToSaveDirectory + "/tick.json"
        json.dump(jsonTick, open(path, "w"), indent=4)

    def load(self):
        path = self.config.pathToSaveDirectory + "/tick.json"
        jsonTick = json.load(open(path))

        # validate
        tickSchema = json.load(open("schemas/tick.json"))
        jsonschema.validate(jsonTick, tickSchema)

        self.tick = int(jsonTick["tick"])
