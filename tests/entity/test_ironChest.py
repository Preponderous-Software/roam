from entity.apple import Apple
from entity.chest import Chest
from entity.ironChest import IronChest


def test_initialization():
    chest = IronChest()

    assert chest.getName() == "Iron Chest"
    assert chest.getImagePath() == "assets/images/ironChest.png"
    assert chest.isSolid() == True


def test_is_a_chest():
    # worldScreen and pickupableEntities gate chest behavior on
    # isinstance(entity, Chest); IronChest must satisfy that check.
    assert isinstance(IronChest(), Chest)


def test_has_stored_inventory():
    chest = IronChest()

    assert chest.getStoredInventory() is not None


def test_stored_inventory_starts_empty():
    chest = IronChest()

    assert chest.getStoredInventory().getNumItems() == 0


def test_can_store_items_in_stored_inventory():
    chest = IronChest()
    apple = Apple()

    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(apple)

    assert chest.getStoredInventory().getNumItems() == 1
