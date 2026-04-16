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


@pytest.fixture(autouse=True)
def isolate_config_file(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("", encoding="utf-8")
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))


def test_defaults():
    config = Config()

    assert config.debug == True
    assert config.fullscreen == False
    assert config.autoEatFoodInInventory == True
    assert config.removeDeadEntities == True
    assert config.showMiniMap == True
    assert config.cameraFollowPlayer == True
    assert config.vsync == True


def test_toggle_camera_follow_player():
    config = Config()

    assert config.cameraFollowPlayer == True
    config.cameraFollowPlayer = False
    assert config.cameraFollowPlayer == False
    config.cameraFollowPlayer = True
    assert config.cameraFollowPlayer == True


def test_toggle_vsync():
    config = Config()

    assert config.vsync == True
    config.vsync = False
    assert config.vsync == False
    config.vsync = True
    assert config.vsync == True


def test_reads_values_from_config_file(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            "debug: false\n"
            "fullscreen: true\n"
            "cameraFollowPlayer: false\n"
            "vsync: false\n"
            "playerMovementEnergyCost: 0.75\n"
            "pathToSaveDirectory: saves/custom\n"
            "black: [1, 2, 3]\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()

    assert not config.debug
    assert config.fullscreen
    assert not config.cameraFollowPlayer
    assert not config.vsync
    assert config.playerMovementEnergyCost == 0.75
    assert config.pathToSaveDirectory == "saves/custom"
    assert config.black == (1, 2, 3)


def test_handles_read_errors_with_defaults(monkeypatch):
    class UnreadableConfigPath:
        def exists(self):
            return True

        def open(self, *args, **kwargs):
            raise OSError("Cannot read file")

    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: UnreadableConfigPath())
    )

    config = Config()

    assert config.debug
    assert config.black == (0, 0, 0)


def test_ignores_invalid_or_empty_values(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            "debug:\n"
            "ticksPerSecond: fast\n"
            "black: none\n"
            "pathToSaveDirectory:\n"
            "displayWidth: none\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()

    assert config.debug
    assert config.ticksPerSecond == 30
    assert config.black == (0, 0, 0)
    assert config.pathToSaveDirectory == "saves/defaultsavefile"
    assert config.displayWidth == config.displayHeight


def test_preserves_hash_character_in_quoted_strings(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            'pathToSaveDirectory: "saves/#1" # keep this value\n'
            "debug: true\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()

    assert config.pathToSaveDirectory == "saves/#1"


def test_inline_comments_are_ignored_for_unquoted_values(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            "debug: true # enabled\n"
            "ticksPerSecond: 45 # faster tick rate\n"
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()

    assert config.debug
    assert config.ticksPerSecond == 45


def test_preserves_hash_after_escaped_quote_in_string(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            'pathToSaveDirectory: "saves/\\"#1" # keep after escaped quote\n'
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()

    assert "#1" in config.pathToSaveDirectory
    assert config.pathToSaveDirectory.startswith("saves/")
