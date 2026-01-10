from unittest.mock import Mock
from src.mapimage.mapImageUpdater import MapImageUpdater
from src.world.tickCounter import TickCounter
from src.config.config import Config


def test_initialization():
    config = Config()
    tickCounter = TickCounter(config)
    
    # Mock the MapImageGenerator to avoid file operations
    updater = MapImageUpdater(tickCounter, config)
    
    assert updater.tickCounter == tickCounter
    assert updater.config == config
    assert updater.tickLastUpdated == tickCounter.getTick()
    assert updater.updateCooldownInTicks == 300


def test_update_if_cooldown_over_not_ready():
    config = Config()
    tickCounter = TickCounter(config)
    
    updater = MapImageUpdater(tickCounter, config)
    
    # Mock the updateMapImage method to track if it's called
    updater.updateMapImage = Mock()
    
    # Should not update if cooldown hasn't passed
    updater.updateIfCooldownOver()
    updater.updateMapImage.assert_not_called()


def test_update_if_cooldown_over_ready():
    config = Config()
    tickCounter = TickCounter(config)
    
    updater = MapImageUpdater(tickCounter, config)
    
    # Simulate time passing beyond cooldown
    tickCounter.tick = 1000  # Set to a high value
    updater.tickLastUpdated = 0  # Set to old value
    
    # Mock the updateMapImage method
    updater.updateMapImage = Mock()
    
    # Should update now that cooldown has passed
    updater.updateIfCooldownOver()
    updater.updateMapImage.assert_called_once()


def test_update_map_image():
    config = Config()
    tickCounter = TickCounter(config)
    
    # Create mock image and generator
    mock_image = Mock()
    mock_generator = Mock()
    mock_generator.generate.return_value = mock_image
    mock_generator.mapImagePath = "test_path.png"
    
    updater = MapImageUpdater(tickCounter, config)
    updater.mapImageGenerator = mock_generator
    
    # Call updateMapImage
    updater.updateMapImage()
    
    # Verify the expected calls were made
    mock_generator.generate.assert_called_once()
    mock_image.save.assert_called_once_with("test_path.png")
    mock_generator.clearRoomImages.assert_called_once()
    
    # Verify tick was updated
    assert updater.tickLastUpdated == tickCounter.getTick()