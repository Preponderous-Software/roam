from entity.apple import Apple
from entity.chest import Chest
from entity.gravestone import Gravestone
from entity.oakWood import OakWood
from screen.pickupableEntities import canBePickedUp


def test_common_resource_can_be_picked_up():
    assert canBePickedUp(OakWood()) is True


def test_gravestone_cannot_be_picked_up():
    # Gravestones are not in the pickupable set (they are retrieved, not carried).
    assert canBePickedUp(Gravestone()) is False


def test_empty_chest_can_be_picked_up():
    assert canBePickedUp(Chest()) is True


def test_non_empty_chest_cannot_be_picked_up():
    chest = Chest()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())

    assert canBePickedUp(chest) is False


def test_chest_becomes_pickupable_again_once_emptied():
    chest = Chest()
    apple = Apple()
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(apple)
    assert canBePickedUp(chest) is False

    chest.getStoredInventory().removeByItem(apple)
    assert canBePickedUp(chest) is True
