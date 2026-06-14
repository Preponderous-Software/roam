import pytest

from entity.apple import Apple
from entity.chest import Chest
from entity.gravestone import Gravestone
from entity.living.livingEntityRegistry import LIVING_ENTITY_TYPES
from entity.oakWood import OakWood
from player.player import Player
from screen.pickupableEntities import canBePickedUp


def test_common_resource_can_be_picked_up():
    assert canBePickedUp(OakWood()) is True


@pytest.mark.parametrize("creatureClass", LIVING_ENTITY_TYPES.values())
def test_every_registered_creature_can_be_picked_up(creatureClass):
    # All spawnable creatures (chickens, bears, and the newer fauna) are
    # carryable, so each must report as pickupable.
    assert canBePickedUp(creatureClass(0)) is True


def test_player_cannot_be_picked_up():
    # The player is a LivingEntity but must never be pickupable.
    assert canBePickedUp(Player(0)) is False


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
