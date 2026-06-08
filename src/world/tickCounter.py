import json
import time

import jsonschema

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from schemaCache import loadSchema

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

        # On platforms with a coarse clock (e.g. Windows' ~15ms time.time()
        # resolution), two consecutive ticks can read the same timestamp,
        # making timeElapsed zero. Skip the rate update in that case to avoid
        # a ZeroDivisionError; the previously measured value is kept.
        if timeElapsed > 0:
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

        jsonschema.validate(jsonTick, loadSchema("tick.json"))

        path = self.config.pathToSaveDirectory + "/tick.json"
        with open(path, "w") as f:
            json.dump(jsonTick, f, indent=4)
        _logger.info("tick counter saved", path=path, tickCount=self.tick)

    def load(self):
        path = self.config.pathToSaveDirectory + "/tick.json"
        with open(path) as f:
            jsonTick = json.load(f)

        jsonschema.validate(jsonTick, loadSchema("tick.json"))

        self.tick = int(jsonTick["tick"])
        _logger.info("tick counter loaded", path=path, tickCount=self.tick)
