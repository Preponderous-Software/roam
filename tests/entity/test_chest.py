from entity.chest import Chest
from entity.apple import Apple
from entity.oakWood import OakWood


def test_initialization():
    chest = Chest()

    assert chest.name == "Chest"
    assert chest.getImagePath() == "assets/images/chest.png"
    assert chest.isSolid() == True


def test_has_stored_inventory():
    chest = Chest()

    assert chest.getStoredInventory() is not None


def test_stored_inventory_starts_empty():
    chest = Chest()

    assert chest.getStoredInventory().getNumItems() == 0


def test_can_store_items_in_stored_inventory():
    chest = Chest()
    apple = Apple()

    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(apple)

    assert chest.getStoredInventory().getNumItems() == 1


def test_stored_inventories_are_independent_per_chest():
    chest1 = Chest()
    chest2 = Chest()

    chest1.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())

    assert chest1.getStoredInventory().getNumItems() == 1
    assert chest2.getStoredInventory().getNumItems() == 0


def test_multiple_items_can_be_stored():
    chest = Chest()

    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())

    assert chest.getStoredInventory().getNumItems() == 2
