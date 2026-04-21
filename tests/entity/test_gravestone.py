from src.entity.gravestone import Gravestone
from src.entity.apple import Apple
from src.entity.oakWood import OakWood


def test_initialization():
    gravestone = Gravestone()

    assert gravestone.name == "Gravestone"
    assert gravestone.getImagePath() == "assets/images/gravestone.png"
    assert gravestone.isSolid() == True


def test_has_stored_inventory():
    gravestone = Gravestone()

    assert gravestone.getStoredInventory() is not None


def test_stored_inventory_starts_empty():
    gravestone = Gravestone()

    assert gravestone.getStoredInventory().getNumItems() == 0


def test_can_store_items_in_stored_inventory():
    gravestone = Gravestone()
    apple = Apple()

    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(apple)

    assert gravestone.getStoredInventory().getNumItems() == 1


def test_stored_inventories_are_independent_per_gravestone():
    stone1 = Gravestone()
    stone2 = Gravestone()

    stone1.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())

    assert stone1.getStoredInventory().getNumItems() == 1
    assert stone2.getStoredInventory().getNumItems() == 0


def test_multiple_items_can_be_stored():
    gravestone = Gravestone()

    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())

    assert gravestone.getStoredInventory().getNumItems() == 2
