# @author Copilot
# @since April 20th, 2026
from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


@component
class ConfigRepository:
    """Handles all persistence for game configuration."""

    def __init__(self, config: Config):
        self.config = config

    def saveWindowSize(self, width, height):
        self.config.saveWindowSize(width, height)
