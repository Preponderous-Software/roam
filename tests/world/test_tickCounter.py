from unittest.mock import patch

import pytest

from world.tickCounter import TickCounter


def createTickCounter(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    return resolve(TickCounter)


def test_initialization(resolve, test_config, tmp_path):
    tickCounter = createTickCounter(resolve, test_config, tmp_path)

    assert tickCounter.getTick() == 0
    assert tickCounter.getHighestMeasuredTicksPerSecond() == 0


def test_get_tick(resolve, test_config, tmp_path):
    tickCounter = createTickCounter(resolve, test_config, tmp_path)

    assert tickCounter.getTick() == 0


def test_increment_tick(resolve, test_config, tmp_path):
    tickCounter = createTickCounter(resolve, test_config, tmp_path)

    tickCounter.incrementTick()

    assert tickCounter.getTick() == 1


def test_increment_tick_multiple(resolve, test_config, tmp_path):
    tickCounter = createTickCounter(resolve, test_config, tmp_path)

    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.incrementTick()

    assert tickCounter.getTick() == 3


def test_get_measured_ticks_per_second(resolve, test_config, tmp_path):
    tickCounter = createTickCounter(resolve, test_config, tmp_path)

    with patch("world.tickCounter.time") as mock_time:
        mock_time.time.side_effect = [100.1, 100.1]
        tickCounter.lastTimestamp = 100.0
        tickCounter.incrementTick()

    assert tickCounter.getMeasuredTicksPerSecond() == pytest.approx(10.0)


def test_get_highest_measured_ticks_per_second(resolve, test_config, tmp_path):
    tickCounter = createTickCounter(resolve, test_config, tmp_path)

    with patch("world.tickCounter.time") as mock_time:
        # First tick: 0.1s elapsed -> 10 TPS
        # Second tick: 0.1s elapsed -> 10 TPS
        mock_time.time.side_effect = [100.1, 100.1, 100.2, 100.2]
        tickCounter.lastTimestamp = 100.0
        tickCounter.incrementTick()
        tickCounter.incrementTick()

    assert tickCounter.getHighestMeasuredTicksPerSecond() == pytest.approx(10.0)


def test_save_and_load(resolve, di_container, test_config, tmp_path):
    tickCounter = createTickCounter(resolve, test_config, tmp_path)

    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.save()

    # load into a new tick counter
    di_container.resetSingletons()
    tickCounter2 = createTickCounter(resolve, test_config, tmp_path)
    tickCounter2.load()

    assert tickCounter2.getTick() == 3
