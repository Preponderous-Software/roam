import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import pytest

from src.config.config import Config
from src.config.keyBindings import KeyBindings


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def isolate_config_file(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )


def test_defaults():
    kb = KeyBindings()
    assert kb.getKey("move_up") == pygame.K_w
    assert kb.getKey("move_left") == pygame.K_a
    assert kb.getKey("move_down") == pygame.K_s
    assert kb.getKey("move_right") == pygame.K_d
    assert kb.getKey("alt_move_up") == pygame.K_UP
    assert kb.getKey("alt_move_left") == pygame.K_LEFT
    assert kb.getKey("alt_move_down") == pygame.K_DOWN
    assert kb.getKey("alt_move_right") == pygame.K_RIGHT
    assert kb.getKey("run") == pygame.K_LSHIFT
    assert kb.getKey("crouch") == pygame.K_LCTRL
    assert kb.getKey("inventory") == pygame.K_i
    assert kb.getKey("toggle_minimap") == pygame.K_m
    assert kb.getKey("toggle_debug") == pygame.K_F3
    assert kb.getKey("toggle_help") == pygame.K_F1


def test_set_key():
    kb = KeyBindings()
    kb.setKey("move_up", pygame.K_UP)
    assert kb.getKey("move_up") == pygame.K_UP


def test_set_key_ignores_unknown_action():
    kb = KeyBindings()
    kb.setKey("nonexistent_action", pygame.K_x)
    assert kb.getKey("nonexistent_action") is None


def test_get_actions():
    kb = KeyBindings()
    actions = kb.getActions()
    assert "move_up" in actions
    assert "inventory" in actions
    assert "toggle_debug" in actions


def test_get_label():
    kb = KeyBindings()
    assert kb.getLabel("move_up") == "Move Up"
    assert kb.getLabel("inventory") == "Inventory"


def test_get_key_name():
    kb = KeyBindings()
    name = kb.getKeyName("move_up")
    assert isinstance(name, str)
    assert len(name) > 0


def test_no_conflicts_by_default():
    kb = KeyBindings()
    assert not kb.hasConflicts()
    assert len(kb.getConflicts()) == 0


def test_detects_conflicts():
    kb = KeyBindings()
    kb.setKey("move_up", pygame.K_a)
    conflicts = kb.getConflicts()
    assert "move_up" in conflicts
    assert "move_left" in conflicts
    assert kb.hasConflicts()


def test_reset_to_defaults():
    kb = KeyBindings()
    kb.setKey("move_up", pygame.K_UP)
    kb.setKey("move_left", pygame.K_LEFT)
    kb.resetToDefaults()
    assert kb.getKey("move_up") == pygame.K_w
    assert kb.getKey("move_left") == pygame.K_a
    assert not kb.hasConflicts()


def test_load_from_config():
    kb = KeyBindings()
    configValues = {
        "key_move_up": pygame.K_UP,
        "key_inventory": pygame.K_TAB,
    }
    kb.loadFromConfig(configValues)
    assert kb.getKey("move_up") == pygame.K_UP
    assert kb.getKey("inventory") == pygame.K_TAB
    # unmodified bindings keep defaults
    assert kb.getKey("move_down") == pygame.K_s


def test_load_from_config_ignores_non_int_values():
    kb = KeyBindings()
    configValues = {
        "key_move_up": "not_a_key",
        "key_move_down": True,
    }
    kb.loadFromConfig(configValues)
    assert kb.getKey("move_up") == pygame.K_w
    assert kb.getKey("move_down") == pygame.K_s


def test_save_to_config_file(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("debug: true\n", encoding="utf-8")
    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()
    kb = KeyBindings()
    kb.setKey("move_up", pygame.K_UP)
    kb.saveToConfigFile(config)

    content = configFilePath.read_text(encoding="utf-8")
    assert "key_move_up: " + str(pygame.K_UP) in content
    assert "debug: true" in content


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()
    kb = KeyBindings()
    kb.setKey("move_up", pygame.K_UP)
    kb.setKey("inventory", pygame.K_TAB)
    kb.saveToConfigFile(config)

    # Load back
    kb2 = KeyBindings()
    configValues = Config.readConfigFile()
    kb2.loadFromConfig(configValues)
    assert kb2.getKey("move_up") == pygame.K_UP
    assert kb2.getKey("inventory") == pygame.K_TAB
    # Unmodified bindings keep defaults
    assert kb2.getKey("move_down") == pygame.K_s


def test_save_updates_existing_bindings(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text(
        "key_move_up: " + str(pygame.K_UP) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()
    kb = KeyBindings()
    kb.loadFromConfig(Config.readConfigFile())
    assert kb.getKey("move_up") == pygame.K_UP

    kb.setKey("move_up", pygame.K_KP8)
    kb.saveToConfigFile(config)

    content = configFilePath.read_text(encoding="utf-8")
    assert "key_move_up: " + str(pygame.K_KP8) in content
    assert content.count("key_move_up") == 1


def test_conflict_detection_multiple_bindings():
    kb = KeyBindings()
    # Set three actions to the same key
    kb.setKey("move_up", pygame.K_x)
    kb.setKey("move_down", pygame.K_x)
    kb.setKey("inventory", pygame.K_x)
    conflicts = kb.getConflicts()
    assert "move_up" in conflicts
    assert "move_down" in conflicts
    assert "inventory" in conflicts
    assert kb.hasConflicts()


def test_no_conflict_when_all_unique():
    kb = KeyBindings()
    # Default bindings are all unique
    assert not kb.hasConflicts()
    # Remap one without collision
    kb.setKey("move_up", pygame.K_KP8)
    assert not kb.hasConflicts()
