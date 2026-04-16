from unittest.mock import MagicMock, patch

import pytest

from src.world.tickCounter import TickCounter


def createTickCounter(tmp_path=None):
    config = MagicMock()
    config.pathToSaveDirectory = str(tmp_path) if tmp_path else "/tmp"
    return TickCounter(config)


def test_initialization(tmp_path):
    tickCounter = createTickCounter(tmp_path)

    assert tickCounter.getTick() == 0
    assert tickCounter.getHighestMeasuredTicksPerSecond() == 0


def test_get_tick(tmp_path):
    tickCounter = createTickCounter(tmp_path)

    assert tickCounter.getTick() == 0


def test_increment_tick(tmp_path):
    tickCounter = createTickCounter(tmp_path)

    tickCounter.incrementTick()

    assert tickCounter.getTick() == 1


def test_increment_tick_multiple(tmp_path):
    tickCounter = createTickCounter(tmp_path)

    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.incrementTick()

    assert tickCounter.getTick() == 3


def test_get_measured_ticks_per_second(tmp_path):
    tickCounter = createTickCounter(tmp_path)

    with patch("src.world.tickCounter.time") as mock_time:
        mock_time.time.side_effect = [100.1, 100.1]
        tickCounter.lastTimestamp = 100.0
        tickCounter.incrementTick()

    assert tickCounter.getMeasuredTicksPerSecond() == pytest.approx(10.0)


def test_get_highest_measured_ticks_per_second(tmp_path):
    tickCounter = createTickCounter(tmp_path)

    with patch("src.world.tickCounter.time") as mock_time:
        # First tick: 0.1s elapsed -> 10 TPS
        # Second tick: 0.1s elapsed -> 10 TPS
        mock_time.time.side_effect = [100.1, 100.1, 100.2, 100.2]
        tickCounter.lastTimestamp = 100.0
        tickCounter.incrementTick()
        tickCounter.incrementTick()

    assert tickCounter.getHighestMeasuredTicksPerSecond() == pytest.approx(10.0)


def test_save_and_load(tmp_path):
    tickCounter = createTickCounter(tmp_path)

    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.incrementTick()
    tickCounter.save()

    # load into a new tick counter
    tickCounter2 = createTickCounter(tmp_path)
    tickCounter2.load()

    assert tickCounter2.getTick() == 3
