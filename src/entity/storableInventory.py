from inventory.inventory import Inventory


# @author Copilot
# @since April 21st, 2026
class StorableInventory:
    """Mixin that provides an internal Inventory for entities that can store items.

    Intended to be used by Gravestone and, in the future, Chest entities.
    """

    def __init__(self):
        self._storedInventory = Inventory()

    def getStoredInventory(self):
        return self._storedInventory
