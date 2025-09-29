import pygame
from src.config.config import Config


def test_initialization():
    pygame.init()  # Initialize pygame for display info
    config = Config()
    
    # Test static configuration values
    assert config.black == (0, 0, 0)
    assert config.white == (255, 255, 255)
    assert config.playerMovementEnergyCost == 0.2
    assert config.playerInteractionEnergyCost == 0.05
    assert config.runSpeedFactor == 2
    assert config.energyDepletionRate == 0.01
    assert config.playerInteractionDistanceLimit == 5
    assert config.ticksPerSecond == 30
    assert config.gridSize == 17
    assert config.worldBorder == 0
    assert config.pathToSaveDirectory == "saves/defaultsavefile"
    
    # Test dynamic configuration values
    assert config.debug == True
    assert config.fullscreen == False
    assert config.autoEatFoodInInventory == True
    assert config.removeDeadEntities == True
    assert config.showMiniMap == True
    
    # Test display dimensions are calculated
    assert config.displayWidth > 0
    assert config.displayHeight > 0
    assert config.displayWidth == config.displayHeight  # Should be square based on formula
    
    pygame.quit()


def test_config_modification():
    pygame.init()
    config = Config()
    
    # Test that dynamic values can be modified
    config.debug = False
    assert config.debug == False
    
    config.fullscreen = True
    assert config.fullscreen == True
    
    config.autoEatFoodInInventory = False
    assert config.autoEatFoodInInventory == False
    
    config.removeDeadEntities = False
    assert config.removeDeadEntities == False
    
    config.showMiniMap = False
    assert config.showMiniMap == False
    
    pygame.quit()