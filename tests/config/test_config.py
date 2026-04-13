import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.init()
from src.config.config import Config


def test_defaults():
    config = Config()

    assert config.debug == True
    assert config.fullscreen == False
    assert config.autoEatFoodInInventory == True
    assert config.removeDeadEntities == True
    assert config.showMiniMap == True
    assert config.cameraFollowPlayer == False


def test_toggle_camera_follow_player():
    config = Config()

    assert config.cameraFollowPlayer == False
    config.cameraFollowPlayer = True
    assert config.cameraFollowPlayer == True
    config.cameraFollowPlayer = False
    assert config.cameraFollowPlayer == False
