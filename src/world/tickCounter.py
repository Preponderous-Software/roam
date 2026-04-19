import json
import time

import jsonschema

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


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
            _logger.warning(
                "tick took too long",
                durationMs=int(millisecondsSinceLastTick),
                tickCount=self.tick,
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

        with open("schemas/tick.json") as f:
            tickSchema = json.load(f)
        jsonschema.validate(jsonTick, tickSchema)

        path = self.config.pathToSaveDirectory + "/tick.json"
        with open(path, "w") as f:
            json.dump(jsonTick, f, indent=4)
        _logger.info("tick counter saved", path=path, tickCount=self.tick)

    def load(self):
        path = self.config.pathToSaveDirectory + "/tick.json"
        with open(path) as f:
            jsonTick = json.load(f)

        with open("schemas/tick.json") as f:
            tickSchema = json.load(f)
        jsonschema.validate(jsonTick, tickSchema)

        self.tick = int(jsonTick["tick"])
        _logger.info("tick counter loaded", path=path, tickCount=self.tick)
