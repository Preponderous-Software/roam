# @author Copilot
# @since April 20th, 2026
from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from player.player import Player
from stats.stats import Stats
from ui.status import Status
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


@component
class InventoryService:
    """Handles inventory operations and item management for the player."""

    def __init__(
        self,
        config: Config,
        player: Player,
        stats: Stats,
        status: Status,
        tickCounter: TickCounter,
    ):
        self.config = config
        self.player = player
        self.stats = stats
        self.status = status
        self.tickCounter = tickCounter

    def eatFoodInInventory(self):
        for itemSlot in self.player.getInventory().getInventorySlots():
            if itemSlot.isEmpty():
                continue
            item = itemSlot.getContents()[0]
            if self.player.canEat(item) and item.getEnergy() > 0:
                self.player.addEnergy(item.getEnergy())
                self.player.getInventory().removeByItem(item)
                self.stats.incrementFoodEaten()
                self.status.set("Ate " + item.getName() + " from inventory")
                self.stats.incrementScore()
                return

    def changeSelectedInventorySlot(self, index):
        self.player.getInventory().setSelectedInventorySlotIndex(index)
        inventorySlot = self.player.getInventory().getSelectedInventorySlot()
        if inventorySlot.isEmpty():
            self.status.set("Empty slot")
            return
        item = inventorySlot.getContents()[0]
        self.status.set("Selected " + item.getName())
