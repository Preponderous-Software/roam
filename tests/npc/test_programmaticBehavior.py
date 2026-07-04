import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from entity.apple import Apple
from entity.living.npc import Npc
from entity.oakWood import OakWood
from npc.programmaticBehavior import ProgrammaticBehavior, _BUILD_THRESHOLD
from world.room import Room


def _config(tps=30):
    return SimpleNamespace(ticksPerSecond=tps)


def _setup(gridSize=5, npcEnergy=100):
    """Return (room, npc, behavior) with the NPC placed at the grid centre."""
    room = Room("Test", gridSize, (0, 0, 0), 0, 0, MagicMock())
    npc = Npc("Bob", 0)
    npc.setEnergy(npcEnergy)
    centre = gridSize // 2
    loc = room.getGrid().getLocationByCoordinates(centre, centre)
    room.addEntityToLocation(npc, loc)
    room.addLivingEntity(npc)
    behavior = ProgrammaticBehavior()
    return room, npc, behavior


# ------------------------------------------------------------------ #
# Cooldown guard                                                        #
# ------------------------------------------------------------------ #


def test_tick_skips_when_cooldown_not_expired():
    room, npc, behavior = _setup()
    # movementSpeed=15, tps=30 → cooldown=2 ticks; set tickLastMoved to 100
    npc.setTickLastMoved(100)
    behavior.tick(npc, room, 101, _config())  # only 1 tick elapsed; < 2
    assert npc.getTickLastMoved() == 100  # unchanged — no action taken


def test_tick_acts_when_cooldown_expired():
    room, npc, behavior = _setup()
    npc.setTickLastMoved(-1000)
    behavior.tick(npc, room, 0, _config())
    assert npc.getTickLastMoved() == 0  # updated by some action


# ------------------------------------------------------------------ #
# Priority 1: eat when hungry                                          #
# ------------------------------------------------------------------ #


def test_eats_food_when_hungry():
    room, npc, behavior = _setup(npcEnergy=40)  # 40 < 50% of 100
    apple = Apple()
    apple_energy = apple.getEnergy()
    npc.getInventory().placeIntoFirstAvailableInventorySlot(apple)
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert npc.getEnergy() == pytest.approx(40 + apple_energy)


def test_does_not_eat_when_not_hungry():
    room, npc, behavior = _setup(npcEnergy=100)
    apple = Apple()
    npc.getInventory().placeIntoFirstAvailableInventorySlot(apple)
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    # Apple should still be in inventory (NPC not hungry)
    assert npc.getInventory().getNumTakenInventorySlots() > 0


# ------------------------------------------------------------------ #
# Priority 2: gather resource at current tile                          #
# ------------------------------------------------------------------ #


def test_gathers_wood_at_current_tile():
    room, npc, behavior = _setup()
    wood = OakWood()
    loc = room.getGrid().getLocation(npc.getLocationID())
    room.addEntityToLocation(wood, loc)
    npc.setTickLastMoved(-1000)

    before = npc.getInventory().getNumTakenInventorySlots()
    behavior.tick(npc, room, 0, _config())

    assert npc.getInventory().getNumTakenInventorySlots() > before


def test_does_not_gather_with_full_inventory():
    room, npc, behavior = _setup()
    # Fill every slot (25 slots × max-stack 20 = 500 items)
    while npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood()):
        pass
    assert npc.getInventory().getNumFreeInventorySlots() == 0
    wood = OakWood()
    loc = room.getGrid().getLocation(npc.getLocationID())
    room.addEntityToLocation(wood, loc)
    npc.setTickLastMoved(-1000)

    items_before = npc.getInventory().getNumTakenInventorySlots()
    behavior.tick(npc, room, 0, _config())

    assert npc.getInventory().getNumTakenInventorySlots() == items_before


# ------------------------------------------------------------------ #
# Priority 3: place wood when carrying enough                          #
# ------------------------------------------------------------------ #


def test_places_wood_when_above_build_threshold():
    room, npc, behavior = _setup()
    for _ in range(_BUILD_THRESHOLD):
        npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    npc.setTickLastMoved(-1000)
    wood_before = npc.getInventory().getNumItemsByType(OakWood)

    behavior.tick(npc, room, 0, _config())

    # One piece of wood placed on an adjacent tile
    assert npc.getInventory().getNumItemsByType(OakWood) < wood_before


# ------------------------------------------------------------------ #
# Wander when inventory is full                                        #
# ------------------------------------------------------------------ #


def test_wanders_when_inventory_full():
    room, npc, behavior = _setup()
    # Fill all 25 slots so the NPC has nowhere to put items
    while npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood()):
        pass
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert npc.getTickLastMoved() == 0


# ------------------------------------------------------------------ #
# wantsRoomChange                                                      #
# ------------------------------------------------------------------ #


def test_wants_room_change_initially_false():
    behavior = ProgrammaticBehavior()
    assert behavior.wantsRoomChange() is False


def test_clear_room_change_request():
    behavior = ProgrammaticBehavior()
    # Manually set the flag (as the exit-seeking code would)
    behavior._wantsRoomChange = True
    behavior.clearRoomChangeRequest()
    assert behavior.wantsRoomChange() is False


# ------------------------------------------------------------------ #
# State / goal introspection                                           #
# ------------------------------------------------------------------ #


def test_get_state_name_returns_string():
    behavior = ProgrammaticBehavior()
    assert isinstance(behavior.getStateName(), str)


def test_get_goal_description_returns_string():
    behavior = ProgrammaticBehavior()
    assert isinstance(behavior.getGoalDescription(), str)


def test_state_is_eating_after_eating():
    room, npc, behavior = _setup(npcEnergy=40)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(Apple())
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "eating"


def test_state_is_gathering_after_gather():
    room, npc, behavior = _setup()
    loc = room.getGrid().getLocation(npc.getLocationID())
    room.addEntityToLocation(OakWood(), loc)
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "gathering"
