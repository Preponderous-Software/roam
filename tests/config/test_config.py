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
    assert config.limitTps == True
    assert config.pushableStone == True


def test_toggle_camera_follow_player():
    config = Config()

    assert config.cameraFollowPlayer == True
    config.cameraFollowPlayer = False
    assert config.cameraFollowPlayer == False
    config.cameraFollowPlayer = True
    assert config.cameraFollowPlayer == True


def test_toggle_limit_tps():
    config = Config()

    assert config.limitTps == True
    config.limitTps = False
    assert config.limitTps == False
    config.limitTps = True
    assert config.limitTps == True


def test_toggle_pushable_stone():
    config = Config()

    assert config.pushableStone == True
    config.pushableStone = False
    assert config.pushableStone == False
    config.pushableStone = True
    assert config.pushableStone == True


def test_reads_values_from_config_file(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            "debug: false\n"
            "fullscreen: true\n"
            "cameraFollowPlayer: false\n"
            "limitTps: false\n"
            "pushableStone: false\n"
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
    assert not config.limitTps
    assert not config.pushableStone
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


def test_save_window_size_creates_entries(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("debug: true\n", encoding="utf-8")
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()
    config.saveWindowSize(800, 600)

    content = configFilePath.read_text(encoding="utf-8")
    assert "savedWindowWidth: 800" in content
    assert "savedWindowHeight: 600" in content


def test_save_window_size_updates_existing_entries(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        "savedWindowWidth: 500\nsavedWindowHeight: 500\n", encoding="utf-8"
    )
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()
    config.saveWindowSize(900, 700)

    content = configFilePath.read_text(encoding="utf-8")
    assert "savedWindowWidth: 900" in content
    assert "savedWindowHeight: 700" in content
    assert "500" not in content


def test_save_window_size_matches_whitespace_before_colon(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        "savedWindowWidth : 500\nsavedWindowHeight : 500\n", encoding="utf-8"
    )
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()
    config.saveWindowSize(900, 700)

    content = configFilePath.read_text(encoding="utf-8")
    assert "savedWindowWidth: 900" in content
    assert "savedWindowHeight: 700" in content
    # No duplicate keys — old lines were replaced, not appended
    assert content.count("savedWindowWidth") == 1
    assert content.count("savedWindowHeight") == 1


def test_save_window_size_clamps_to_minimum(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("", encoding="utf-8")
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()
    config.saveWindowSize(100, 200)

    content = configFilePath.read_text(encoding="utf-8")
    assert "savedWindowWidth: 400" in content
    assert "savedWindowHeight: 400" in content


def test_saved_window_size_is_loaded_on_init(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        "savedWindowWidth: 800\nsavedWindowHeight: 600\n", encoding="utf-8"
    )
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()

    assert config.displayWidth == 800.0
    assert config.displayHeight == 600.0


def test_saved_window_size_fallback_when_too_large(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        "savedWindowWidth: 99999\nsavedWindowHeight: 99999\n", encoding="utf-8"
    )
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()

    # Should fall back to default (90% of screen height)
    screenHeight = pygame.display.Info().current_h
    expectedDefault = screenHeight * 0.90
    assert config.displayWidth == expectedDefault
    assert config.displayHeight == expectedDefault


def test_manual_display_overrides_saved_window_size(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        (
            "savedWindowWidth: 800\n"
            "savedWindowHeight: 600\n"
            "displayWidth: 1024\n"
            "displayHeight: 768\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()

    assert config.displayWidth == 1024.0
    assert config.displayHeight == 768.0


def test_no_saved_dimensions_uses_default(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("", encoding="utf-8")
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()

    screenHeight = pygame.display.Info().current_h
    expectedDefault = screenHeight * 0.90
    assert config.displayWidth == expectedDefault
    assert config.displayHeight == expectedDefault


def test_save_window_size_preserves_other_config(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        "debug: false\nticksPerSecond: 60\n", encoding="utf-8"
    )
    monkeypatch.setattr(Config, "getConfigFilePath", staticmethod(lambda: configFilePath))

    config = Config()
    config.saveWindowSize(800, 600)

    content = configFilePath.read_text(encoding="utf-8")
    assert "debug: false" in content
    assert "ticksPerSecond: 60" in content
    assert "savedWindowWidth: 800" in content
    assert "savedWindowHeight: 600" in content
