# @author Copilot
# @since April 20th, 2026
from appContainer import component
from player.player import Player
from services.craftingService import CraftingService
from services.inventoryService import InventoryService


@component
class InventoryController:
    """Thin input router for inventory actions.

    Receives inventory-related actions forwarded from the screen, determines
    which service method to call, and delegates immediately.  All UI state
    (cursor slot, craft-panel visibility) and hit-testing geometry remain in
    the view (InventoryScreen).
    """

    def __init__(
        self,
        player: Player,
        craftingService: CraftingService,
        inventoryService: InventoryService,
    ):
        self.player = player
        self.craftingService = craftingService
        self.inventoryService = inventoryService

    def craftRecipe(self, recipe):
        """Route a craft action to the crafting service."""
        return self.craftingService.craftRecipe(recipe, self.player.getInventory())

    def changeSelectedSlot(self, index):
        """Route a slot selection change to the inventory service."""
        self.inventoryService.changeSelectedInventorySlot(index)
