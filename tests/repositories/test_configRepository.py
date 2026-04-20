import pytest
from unittest.mock import MagicMock

from repositories.configRepository import ConfigRepository
from config.config import Config


def makeRepo():
    config = MagicMock(spec=Config)
    return ConfigRepository(config), config


def test_save_window_size_delegates_to_config():
    repo, config = makeRepo()
    repo.saveWindowSize(1920, 1080)
    config.saveWindowSize.assert_called_once_with(1920, 1080)


def test_save_window_size_different_values():
    repo, config = makeRepo()
    repo.saveWindowSize(800, 600)
    config.saveWindowSize.assert_called_once_with(800, 600)
