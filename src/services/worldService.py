# @author Copilot
# @since April 20th, 2026
from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from stats.stats import Stats
from ui.status import Status

_logger = getLogger(__name__)


@component
class WorldService:
    """Handles world generation, room management, and world state changes."""

    def __init__(self, config: Config, stats: Stats, status: Status):
        self.config = config
        self.stats = stats
        self.status = status

    def getOrLoadRoom(self, x, y, map):
        """Get a room from the map or load/generate it."""
        room = map.getRoom(x, y)
        if room == -1:
            room = map.generateNewRoom(x, y)
        return room

    def loadOrGenerateRoom(self, x, y, map):
        """Load a room from file or generate a new one, with status messages."""
        wasCached = map.hasRoom(x, y)
        room = map.getRoom(x, y)
        if room != -1:
            if not wasCached:
                self.status.set("Area loaded")
            return room
        room = map.generateNewRoom(x, y)
        self.status.set("New area discovered")
        self.stats.incrementScore()
        self.stats.incrementRoomsExplored()
        return room
