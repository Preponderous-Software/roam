import time
import tempfile
import os
import json
from src.world.tickCounter import TickCounter
from src.config.config import Config


def test_initialization():
    config = Config()
    tickCounter = TickCounter(config)
    
    assert tickCounter.getTick() == 0
    assert tickCounter.getMeasuredTicksPerSecond() == 0
    assert tickCounter.getHighestMeasuredTicksPerSecond() == 0


def test_increment_tick():
    config = Config()
    tickCounter = TickCounter(config)
    
    initial_tick = tickCounter.getTick()
    tickCounter.incrementTick()
    assert tickCounter.getTick() == initial_tick + 1
    
    tickCounter.incrementTick()
    assert tickCounter.getTick() == initial_tick + 2


def test_measured_ticks_per_second():
    config = Config()
    tickCounter = TickCounter(config)
    
    # Increment tick and check that measured TPS is calculated
    tickCounter.incrementTick()
    
    # Should have a measured TPS value now
    assert tickCounter.getMeasuredTicksPerSecond() > 0
    assert tickCounter.getHighestMeasuredTicksPerSecond() > 0


def test_save_and_load():
    config = Config()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config.pathToSaveDirectory = temp_dir
        
        # Create tick counter and set some ticks
        tickCounter = TickCounter(config)
        tickCounter.tick = 12345
        
        # Save the tick counter
        tickCounter.save()
        
        # Verify file was created
        tick_file = os.path.join(temp_dir, "tick.json")
        assert os.path.exists(tick_file)
        
        # Verify file contents
        with open(tick_file, 'r') as f:
            data = json.load(f)
            assert data["tick"] == 12345
        
        # Create new tick counter and load
        newTickCounter = TickCounter(config)
        assert newTickCounter.getTick() == 0  # Should start at 0
        
        newTickCounter.load()
        assert newTickCounter.getTick() == 12345  # Should load saved value


def test_warning_threshold(capsys):
    config = Config()
    tickCounter = TickCounter(config)
    
    # Manually set an old timestamp to trigger warning
    tickCounter.lastTimestamp = time.time() - 1.0  # 1 second ago
    
    # Increment tick should trigger a warning
    tickCounter.incrementTick()
    
    # Capture the output
    captured = capsys.readouterr()
    
    # Should have printed a warning
    assert "WARNING: Tick took" in captured.out
    assert "milliseconds to complete" in captured.out