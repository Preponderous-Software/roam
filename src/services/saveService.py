# @author Copilot
# @since April 20th, 2026
import os

from appContainer import component
from codex.codex import Codex
from config.config import Config
from gameLogging.logger import getLogger
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
from repositories.codexRepository import CodexRepository
from repositories.playerRepository import PlayerRepository
from repositories.worldRepository import WorldRepository
from stats.stats import Stats
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


@component
class SaveService:
    """Coordinates all save/load operations across repositories."""

    def __init__(
        self,
        config: Config,
        stats: Stats,
        tickCounter: TickCounter,
        codex: Codex,
        playerRepository: PlayerRepository,
        worldRepository: WorldRepository,
        codexRepository: CodexRepository,
        inventoryJsonReaderWriter: InventoryJsonReaderWriter,
    ):
        self.config = config
        self.stats = stats
        self.tickCounter = tickCounter
        self.codex = codex
        self.playerRepository = playerRepository
        self.worldRepository = worldRepository
        self.codexRepository = codexRepository
        self.inventoryJsonReaderWriter = inventoryJsonReaderWriter

    def saveAll(self, currentRoom):
        """Save all game state synchronously."""
        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)
        self.worldRepository.saveRoom(currentRoom)
        self.playerRepository.saveLocation(currentRoom)
        self.playerRepository.saveAttributes()
        self.playerRepository.saveInventory(self.inventoryJsonReaderWriter)
        self.stats.save()
        self.tickCounter.save()
        self.codexRepository.save(self.codex)

    def loadAll(self, mapInstance):
        """Load all game state. Returns the loaded currentRoom or None."""
        currentRoom = None
        path = self.config.pathToSaveDirectory + "/playerLocation.json"
        if os.path.exists(path):
            currentRoom = self.playerRepository.loadLocation(mapInstance)

        attrPath = self.config.pathToSaveDirectory + "/playerAttributes.json"
        if os.path.exists(attrPath):
            self.playerRepository.loadAttributes()

        statsPath = self.config.pathToSaveDirectory + "/stats.json"
        if os.path.exists(statsPath):
            self.stats.load()

        tickPath = self.config.pathToSaveDirectory + "/tick.json"
        if os.path.exists(tickPath):
            self.tickCounter.load()

        invPath = self.config.pathToSaveDirectory + "/playerInventory.json"
        if os.path.exists(invPath):
            self.playerRepository.loadInventory(self.inventoryJsonReaderWriter)

        codexPath = self.config.pathToSaveDirectory + "/codex.json"
        if os.path.exists(codexPath):
            entities = self.codexRepository.load()
            if entities is not None:
                self.codex.setDiscovered(entities)

        return currentRoom
