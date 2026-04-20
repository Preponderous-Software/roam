# @author Copilot
# @since April 20th, 2026
from appContainer import component
from gameLogging.logger import getLogger
from ui.status import Status

_logger = getLogger(__name__)


@component
class CraftingService:
    """Handles crafting logic and recipe validation."""

    def __init__(self, status: Status):
        self.status = status

    def canCraft(self, recipe, inventory):
        return recipe.canCraft(inventory)

    def craftRecipe(self, recipe, inventory):
        if not recipe.canCraft(inventory):
            self.status.set("Not enough materials")
            return False

        # Pre-validate capacity for all result items
        availableSpace = 0
        probe = recipe.getResultClass()()
        probeName = probe.getName()
        for slot in inventory.getInventorySlots():
            if slot.isEmpty():
                availableSpace += slot.getMaxStackSize()
            elif slot.getContents()[0].getName() == probeName:
                availableSpace += slot.getMaxStackSize() - slot.getNumItems()
        if availableSpace < recipe.getResultCount():
            self.status.set("Inventory full")
            return False

        results = recipe.craft(inventory)
        if results is not None:
            for result in results:
                if not inventory.placeIntoFirstAvailableInventorySlot(result):
                    self.status.set("Inventory full while placing crafted items")
                    return False
            self.status.set("Crafted " + recipe.getName())
            return True
        return False
