import json
import os
import time
from unittest.mock import MagicMock

from src.world.tickCounter import TickCounter


def createTickCounter():
    config = MagicMock()
    config.pathToSaveDirectory = "/tmp/roam_test_saves"
    return TickCounter(config)


def test_initialization():
    tickCounter = createTickCounter()

    assert tickCounter.getTick() == 0
    assert tickCounter.getHighestMeasuredTicksPerSecond() == 0


def test_get_tick():
    tickCounter = createTickCounter()

    assert tickCounter.getTick() == 0


def test_increment_tick():
    tickCounter = createTickCounter()

    tickCounter.incrementTick()

    assert tickCounter.getTick() == 1


def test_increment_tick_multiple():
    tickCounter = createTickCounter()

    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.incrementTick()

    assert tickCounter.getTick() == 3


def test_measured_ticks_per_second():
    tickCounter = createTickCounter()

    tickCounter.incrementTick()

    assert tickCounter.getMeasuredTicksPerSecond() > 0


def test_highest_measured_ticks_per_second():
    tickCounter = createTickCounter()

    tickCounter.incrementTick()

    assert tickCounter.getHighestMeasuredTicksPerSecond() > 0


def test_save_and_load():
    tickCounter = createTickCounter()
    savePath = "/tmp/roam_test_saves"
    os.makedirs(savePath, exist_ok=True)

    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.save()

    # load into a new tick counter
    tickCounter2 = createTickCounter()
    tickCounter2.load()

    assert tickCounter2.getTick() == 3

    # cleanup
    tickPath = os.path.join(savePath, "tick.json")
    if os.path.exists(tickPath):
        os.remove(tickPath)
