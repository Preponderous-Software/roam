# @author Copilot
# @since April 20th, 2026
from appContainer import component
from gameLogging.logger import getLogger
from services.saveService import SaveService
from services.worldService import WorldService
from services.entityService import EntityService
from world.roomPreloader import RoomPreloader

_logger = getLogger(__name__)


@component
class WorldController:
    """Routes world-level actions including room transitions and persistence."""

    def __init__(
        self,
        saveService: SaveService,
        worldService: WorldService,
        entityService: EntityService,
        roomPreloader: RoomPreloader,
    ):
        self.saveService = saveService
        self.worldService = worldService
        self.entityService = entityService
        self.roomPreloader = roomPreloader

    def initialize(self, mapInstance):
        """Load saved game state into the map. Returns loaded currentRoom or None."""
        return self.saveService.loadAll(mapInstance)

    def save(self, currentRoom):
        """Save all game state synchronously."""
        self.saveService.saveAll(currentRoom)

    def discoverLivingEntitiesInRoom(self, currentRoom):
        """Discover living entities in the current room and update codex."""
        self.entityService.discoverLivingEntitiesInRoom(currentRoom)

    def preloadNearbyRooms(self, roomX, roomY, map):
        self.roomPreloader.preloadNearbyRooms(roomX, roomY, map)
