import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import pytest

from src.config.config import Config


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def test_defaults():
    config = Config()

    assert config.debug == True
    assert config.fullscreen == False
    assert config.autoEatFoodInInventory == True
    assert config.removeDeadEntities == True
    assert config.showMiniMap == True
    assert config.cameraFollowPlayer == True


def test_toggle_camera_follow_player():
    config = Config()

    assert config.cameraFollowPlayer == True
    config.cameraFollowPlayer = False
    assert config.cameraFollowPlayer == False
    config.cameraFollowPlayer = True
    assert config.cameraFollowPlayer == True


def test_reads_values_from_config_file(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            "debug: false\n"
            "fullscreen: true\n"
            "cameraFollowPlayer: false\n"
            "playerMovementEnergyCost: 0.75\n"
            "pathToSaveDirectory: saves/custom\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()

    assert config.debug == False
    assert config.fullscreen == True
    assert config.cameraFollowPlayer == False
    assert config.playerMovementEnergyCost == 0.75
    assert config.pathToSaveDirectory == "saves/custom"
