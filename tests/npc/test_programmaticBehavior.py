import uuid

import pytest
from collections import deque
from types import SimpleNamespace
from unittest.mock import MagicMock

from entity.apple import Apple
from entity.living.npc import Npc
from entity.oakWood import OakWood
from entity.stone import Stone
from npc.programmaticBehavior import (
    ProgrammaticBehavior,
    _BUILD_THRESHOLD,
    _SCAN_INTERVAL,
    _SEEK_BUDGET,
    _WANDER_STEPS,
    _RoomKnowledge,
    _directionToward,
    _getNeighbor,
    _hasLiving,
    _hasSolid,
    _locationOf,
    _npcMove,
)
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


# ------------------------------------------------------------------ #
# Oscillation detection and _blockedTargets                           #
# ------------------------------------------------------------------ #


def test_seek_budget_expiry_blacklists_target():
    """When _seekBudget hits zero the target ID is added to _blockedTargets."""
    room, npc, behavior = _setup(gridSize=5)
    target_loc = room.getGrid().getLocationByCoordinates(4, 4)
    room.addEntityToLocation(Apple(), target_loc)
    behavior._nearestCache = target_loc
    behavior._seekBudget = 1  # expires on next tick

    npc.setTickLastMoved(-1000)
    behavior.tick(npc, room, 0, _config())

    assert target_loc.getID() in behavior._blockedTargets
    assert behavior._nearestCache is None


def test_gather_clears_blocked_targets():
    """Successfully gathering an item resets _blockedTargets."""
    room, npc, behavior = _setup(gridSize=5)
    centre = 5 // 2
    loc = room.getGrid().getLocationByCoordinates(centre, centre)
    room.addEntityToLocation(Apple(), loc)
    npc.setEnergy(100)  # not hungry; will gather
    target_loc = room.getGrid().getLocationByCoordinates(4, 4)
    behavior._blockedTargets = {target_loc.getID()}  # pre-populated

    npc.setTickLastMoved(-1000)
    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "gathering"
    assert len(behavior._blockedTargets) == 0


def test_oscillation_blacklists_target():
    """Repeated A-B-A position pattern eventually blacklists the target."""
    room, npc, behavior = _setup(gridSize=5)
    target_loc = room.getGrid().getLocationByCoordinates(4, 4)
    room.addEntityToLocation(Apple(), target_loc)
    behavior._nearestCache = target_loc
    behavior._seekBudget = 100
    behavior._oscillationCount = 1  # one prior detection; next triggers blacklist

    # Arrange posHistory so the NPC's current tile completes an A-B-A pattern.
    # After the tick appends curLocId, history becomes [other, curLocId, other, curLocId]
    # → ph[-3]==ph[-1] and ph[-3]!=ph[-2] ✓
    npc_lid = str(room.getGrid().getLocation(npc.getLocationID()).getID())
    behavior._posHistory = deque(["other", npc_lid, "other"], maxlen=4)

    npc.setTickLastMoved(-1000)
    behavior.tick(npc, room, 0, _config())

    assert target_loc.getID() in behavior._blockedTargets
    assert behavior._nearestCache is None


def test_oscillation_clears_blocked_targets_at_safety_cap():
    """Blacklisting a sixth target clears the whole set instead of growing it."""
    room, npc, behavior = _setup(gridSize=5)
    target_loc = _at(room, 4, 4)
    room.addEntityToLocation(Apple(), target_loc)
    behavior._nearestCache = target_loc
    behavior._seekBudget = 100
    behavior._oscillationCount = 1
    behavior._blockedTargets = {uuid.uuid4() for _ in range(5)}
    npc_lid = str(npc.getLocationID())
    behavior._posHistory = deque(["other", npc_lid, "other"], maxlen=4)

    npc.setTickLastMoved(-1000)
    behavior.tick(npc, room, 0, _config())

    assert behavior._blockedTargets == set()
    assert behavior._nearestCache is None
    assert behavior._scanCooldown == _SCAN_INTERVAL * 3


def test_non_oscillating_step_resets_oscillation_count():
    room, npc, behavior = _setup(gridSize=5)
    target_loc = _at(room, 4, 2)
    room.addEntityToLocation(Apple(), target_loc)
    behavior._nearestCache = target_loc
    behavior._seekBudget = 100
    behavior._oscillationCount = 1

    npc.setTickLastMoved(-1000)
    behavior.tick(npc, room, 0, _config())

    assert behavior._oscillationCount == 0
    assert behavior.getStateName() == "seeking_resource"


# ------------------------------------------------------------------ #
# Helpers                                                               #
# ------------------------------------------------------------------ #


def _at(room, x, y):
    return room.getGrid().getLocationByCoordinates(x, y)


def _npcXY(room, npc):
    loc = room.getGrid().getLocation(npc.getLocationID())
    return (loc.getX(), loc.getY())


def _surround(room, x, y, directions):
    """Place a Stone on the neighbor of (x, y) in each given direction."""
    offsets = {0: (0, -1), 1: (-1, 0), 2: (0, 1), 3: (1, 0)}
    for d in directions:
        dx, dy = offsets[d]
        room.addEntityToLocation(Stone(), _at(room, x + dx, y + dy))


def _moveNpcTo(room, npc, x, y):
    room.getGrid().getLocation(npc.getLocationID()).removeEntity(npc)
    room.addEntityToLocation(npc, _at(room, x, y))


# ------------------------------------------------------------------ #
# _locationOf                                                           #
# ------------------------------------------------------------------ #


def test_location_of_returns_npc_location():
    room, npc, _ = _setup()
    assert _locationOf(npc, room) is _at(room, 2, 2)


def test_location_of_returns_none_for_unplaced_sentinel():
    room, npc, _ = _setup()
    npc.setLocationID("-1")
    assert _locationOf(npc, room) is None


def test_location_of_returns_none_for_id_not_in_grid():
    room, npc, _ = _setup()
    npc.setLocationID(uuid.uuid4())
    assert _locationOf(npc, room) is None


def test_tick_does_nothing_when_npc_location_not_in_grid():
    room, npc, behavior = _setup()
    npc.setLocationID(uuid.uuid4())
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert npc.getTickLastMoved() == -1000
    assert behavior.getStateName() == "wandering"
    assert behavior.getGoalDescription() == ""


# ------------------------------------------------------------------ #
# Grid helpers                                                          #
# ------------------------------------------------------------------ #


@pytest.mark.parametrize(
    "direction, expected",
    [(0, (2, 1)), (1, (1, 2)), (2, (2, 3)), (3, (3, 2))],
)
def test_get_neighbor_maps_direction_codes(direction, expected):
    room, _, _ = _setup()
    neighbor = _getNeighbor(_at(room, 2, 2), direction, room.getGrid())
    assert (neighbor.getX(), neighbor.getY()) == expected


@pytest.mark.parametrize(
    "x, y, direction", [(2, 0, 0), (0, 2, 1), (2, 4, 2), (4, 2, 3)]
)
def test_get_neighbor_returns_none_past_edge(x, y, direction):
    room, _, _ = _setup()
    assert _getNeighbor(_at(room, x, y), direction, room.getGrid()) is None


def test_has_solid_true_only_with_solid_entity():
    room, _, _ = _setup()
    loc = _at(room, 0, 0)
    room.addEntityToLocation(Apple(), loc)
    assert _hasSolid(loc) is False
    room.addEntityToLocation(Stone(), loc)
    assert _hasSolid(loc) is True


def test_has_living_true_only_with_living_entity():
    room, _, _ = _setup()
    empty = _at(room, 0, 0)
    room.addEntityToLocation(OakWood(), empty)
    assert _hasLiving(empty) is False
    assert _hasLiving(_at(room, 2, 2)) is True


@pytest.mark.parametrize(
    "target, expected",
    [
        ((4, 3), 3),  # dx dominant, positive → right
        ((0, 1), 1),  # dx dominant, negative → left
        ((3, 4), 2),  # dy dominant, positive → down
        ((1, 0), 0),  # dy dominant, negative → up
        ((3, 3), 3),  # |dx| == |dy| → horizontal wins
        ((2, 2), 1),  # same tile → dx == 0 is not > 0 → left
    ],
)
def test_direction_toward(target, expected):
    room, _, _ = _setup()
    assert _directionToward(_at(room, 2, 2), _at(room, *target)) == expected


# ------------------------------------------------------------------ #
# _npcMove (shared with agenticBehavior)                               #
# ------------------------------------------------------------------ #


def test_npc_move_steps_into_open_neighbor():
    room, npc, _ = _setup()
    moved = _npcMove(npc, _at(room, 2, 2), room, 7, 3)

    assert moved is True
    assert _npcXY(room, npc) == (3, 2)
    assert npc.getDirection() == 3
    assert npc.getTickLastMoved() == 7
    assert npc.getEnergy() == pytest.approx(99.5)
    assert _at(room, 2, 2).isEntityPresent(npc) is False


def test_npc_move_blocked_forward_tries_clockwise_perpendicular_first():
    room, npc, _ = _setup()
    _surround(room, 2, 2, [3])  # block right

    _npcMove(npc, _at(room, 2, 2), room, 0, 3)

    # (3 + 1) % 4 == 0 → up
    assert _npcXY(room, npc) == (2, 1)
    assert npc.getDirection() == 0


def test_npc_move_falls_back_to_reverse_when_allowed():
    room, npc, _ = _setup()
    _surround(room, 2, 2, [3, 0, 2])  # block right and both perpendiculars

    moved = _npcMove(npc, _at(room, 2, 2), room, 0, 3)

    assert moved is True
    assert _npcXY(room, npc) == (1, 2)
    assert npc.getDirection() == 1


def test_npc_move_without_reverse_stays_put_and_consumes_turn():
    room, npc, _ = _setup()
    _surround(room, 2, 2, [3, 0, 2])

    moved = _npcMove(npc, _at(room, 2, 2), room, 5, 3, allowReverse=False)

    assert moved is False
    assert _npcXY(room, npc) == (2, 2)
    assert npc.getTickLastMoved() == 5
    assert npc.getEnergy() == 100  # no energy spent on a blocked move


def test_npc_move_at_edge_uses_perpendicular():
    room, npc, _ = _setup()
    _moveNpcTo(room, npc, 4, 2)

    _npcMove(npc, _at(room, 4, 2), room, 0, 3)

    assert _npcXY(room, npc) == (4, 1)


# ------------------------------------------------------------------ #
# _RoomKnowledge                                                        #
# ------------------------------------------------------------------ #


def test_room_knowledge_unknown_room_assumed_to_have_resources():
    knowledge = _RoomKnowledge()
    assert knowledge.hasFood(3, 3) is True
    assert knowledge.hasWood(3, 3) is True


def test_room_knowledge_record_is_reflected_in_queries():
    knowledge = _RoomKnowledge()
    knowledge.record(1, 2, False, True)
    assert knowledge.hasFood(1, 2) is False
    assert knowledge.hasWood(1, 2) is True


def test_best_exit_direction_none_without_matching_room():
    knowledge = _RoomKnowledge()
    assert knowledge.bestExitDirection(0, 0, wantFood=True) is None
    knowledge.record(1, 0, False, True)
    assert knowledge.bestExitDirection(0, 0, wantFood=True) is None
    assert knowledge.bestExitDirection(0, 0, wantFood=False) == 3


def test_best_exit_direction_picks_nearest_matching_room():
    knowledge = _RoomKnowledge()
    knowledge.record(5, 0, True, False)
    knowledge.record(0, -2, True, False)
    assert knowledge.bestExitDirection(0, 0, wantFood=True) == 0


@pytest.mark.parametrize(
    "roomXY, expected",
    [((-3, 1), 1), ((1, 4), 2), ((2, 2), 3)],
)
def test_best_exit_direction_axis_choice(roomXY, expected):
    knowledge = _RoomKnowledge()
    knowledge.record(roomXY[0], roomXY[1], True, True)
    assert knowledge.bestExitDirection(0, 0, wantFood=True) == expected


def test_best_exit_direction_for_current_room_points_left():
    """A matching record for the current room (distance 0) is not excluded;
    dx == 0 falls through to the "left" branch."""
    knowledge = _RoomKnowledge()
    knowledge.record(0, 0, True, True)
    assert knowledge.bestExitDirection(0, 0, wantFood=True) == 1


# ------------------------------------------------------------------ #
# Priority 1/2 edge paths                                              #
# ------------------------------------------------------------------ #


def test_hungry_npc_does_not_eat_non_food_items():
    room, npc, behavior = _setup(npcEnergy=40)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(Stone())
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() != "eating"
    assert npc.getInventory().getNumItemsByType(Stone) == 1


def test_gather_ignores_other_living_entity_on_tile():
    room, npc, behavior = _setup()
    room.addEntityToLocation(Npc("Other", 0), _at(room, 2, 2))
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() != "gathering"
    assert npc.getInventory().getNumTakenInventorySlots() == 0


# ------------------------------------------------------------------ #
# Priority 3 edge paths (_tryPlace)                                    #
# ------------------------------------------------------------------ #


def test_try_place_returns_false_without_wood():
    room, npc, behavior = _setup()
    assert behavior._tryPlace(npc, _at(room, 2, 2), room, 0) is False


def test_try_place_skips_solid_and_living_neighbors():
    room, npc, behavior = _setup()
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    _surround(room, 2, 2, [0, 1, 2])
    room.addEntityToLocation(Npc("Other", 0), _at(room, 3, 2))

    assert behavior._tryPlace(npc, _at(room, 2, 2), room, 0) is False
    assert npc.getInventory().getNumItemsByType(OakWood) == 1


def test_place_blocked_falls_through_to_lower_priorities():
    room, npc, behavior = _setup()
    for _ in range(_BUILD_THRESHOLD):
        npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    _surround(room, 2, 2, [0, 1, 2, 3])
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() != "placing"
    assert npc.getInventory().getNumItemsByType(OakWood) == _BUILD_THRESHOLD


# ------------------------------------------------------------------ #
# Inventory full                                                       #
# ------------------------------------------------------------------ #


def test_inventory_full_of_non_wood_wanders_with_inventory_full_goal():
    room, npc, behavior = _setup()
    while npc.getInventory().placeIntoFirstAvailableInventorySlot(Stone()):
        pass
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "wandering"
    assert behavior.getGoalDescription() == "inventory full"
    assert _npcXY(room, npc) != (2, 2)


def test_inventory_full_of_wood_builds_before_wandering():
    """A full inventory of OakWood clears the build threshold, so priority 3
    runs before the inventory-full wander branch is reached."""
    room, npc, behavior = _setup()
    while npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood()):
        pass
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getGoalDescription() == "building shelter"


# ------------------------------------------------------------------ #
# Priority 4: seek nearest resource                                    #
# ------------------------------------------------------------------ #


def test_hungry_npc_steps_toward_visible_food():
    room, npc, behavior = _setup(npcEnergy=40)
    target = _at(room, 4, 2)
    room.addEntityToLocation(Apple(), target)
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "seeking_resource"
    assert behavior.getGoalDescription() == "moving to resource"
    assert behavior._nearestCache is target
    assert behavior._seekBudget == _SEEK_BUDGET - 1
    assert _npcXY(room, npc) == (3, 2)


def test_hungry_npc_reaches_and_gathers_food():
    room, npc, behavior = _setup(npcEnergy=40)
    room.addEntityToLocation(Apple(), _at(room, 4, 2))
    npc.setTickLastMoved(-1000)

    for tick in range(0, 30, 3):
        behavior.tick(npc, room, tick, _config())

    assert npc.getEnergy() > 40
    assert not any(isinstance(e, Apple) for e in _at(room, 4, 2).getEntities().values())


def test_scan_records_current_room_knowledge():
    room, npc, behavior = _setup()
    room.addEntityToLocation(Apple(), _at(room, 0, 0))
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior._knowledge.hasFood(0, 0) is True
    assert behavior._knowledge.hasWood(0, 0) is False
    assert behavior._scanCooldown == _SCAN_INTERVAL


def test_existing_target_is_not_replaced_by_rescan():
    room, npc, behavior = _setup(npcEnergy=40)
    far = _at(room, 0, 0)
    room.addEntityToLocation(Apple(), far)
    room.addEntityToLocation(Apple(), _at(room, 3, 2))
    behavior._nearestCache = far
    behavior._seekBudget = 100
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior._nearestCache is far


def test_find_nearest_skips_blocked_targets():
    room, npc, behavior = _setup()
    near = _at(room, 3, 2)
    far = _at(room, 0, 0)
    room.addEntityToLocation(Apple(), near)
    room.addEntityToLocation(Apple(), far)
    behavior._blockedTargets = {near.getID()}

    assert behavior._findNearest(_at(room, 2, 2), room, (Apple,)) is far


def test_npc_sidesteps_solid_wood_instead_of_stepping_onto_it():
    """OakWood is solid, and the NPC only gathers from its own tile, so a
    wood target is never entered and never gathered — the NPC sidesteps.
    Characterizes current behavior; see Preponderous-Software/roam#577."""
    room, npc, behavior = _setup()
    room.addEntityToLocation(OakWood(), _at(room, 3, 2))
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "seeking_resource"
    assert _npcXY(room, npc) == (2, 1)  # (3 + 1) % 4 == 0 → up

    for tick in range(3, 3 * 200, 3):
        behavior.tick(npc, room, tick, _config())

    assert npc.getInventory().getNumItemsByType(OakWood) == 0
    assert any(isinstance(e, OakWood) for e in _at(room, 3, 2).getEntities().values())


# ------------------------------------------------------------------ #
# Priority 5: seek room exit when hungry and room is depleted          #
# ------------------------------------------------------------------ #


def test_hungry_npc_in_empty_room_walks_toward_nearest_edge():
    room, npc, behavior = _setup(npcEnergy=40)
    _moveNpcTo(room, npc, 1, 2)
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "seeking_exit"
    assert behavior.getGoalDescription() == "leaving room to find food"
    assert _npcXY(room, npc) == (0, 2)
    assert npc.getDirection() == 1
    assert npc.getEnergy() == pytest.approx(39.5)
    assert behavior.wantsRoomChange() is False


def test_hungry_npc_at_edge_requests_room_change():
    room, npc, behavior = _setup(npcEnergy=40)
    _moveNpcTo(room, npc, 0, 2)
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.wantsRoomChange() is True
    assert _npcXY(room, npc) == (0, 2)
    assert npc.getTickLastMoved() == 0


def test_exit_seeking_prefers_direction_of_known_food_room():
    room, npc, behavior = _setup(npcEnergy=40)
    behavior._knowledge.record(1, 0, True, False)  # food in the room to the east
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert _npcXY(room, npc) == (3, 2)
    assert npc.getDirection() == 3


def test_exit_seeking_boxed_in_waits():
    room, npc, behavior = _setup(npcEnergy=40)
    _surround(room, 2, 2, [0, 1, 2, 3])
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "seeking_exit"
    assert _npcXY(room, npc) == (2, 2)
    assert npc.getTickLastMoved() == 0
    assert npc.getEnergy() == 40
    assert behavior.wantsRoomChange() is False


# ------------------------------------------------------------------ #
# Priority 6: wander                                                   #
# ------------------------------------------------------------------ #


def test_wander_direction_is_held_for_wander_steps(monkeypatch):
    rolls = iter([3, 1, 2])
    monkeypatch.setattr(
        "npc.programmaticBehavior.random.randint", lambda a, b: next(rolls)
    )
    behavior = ProgrammaticBehavior()  # consumes the first roll in __init__

    directions = [behavior._pickWanderDir() for _ in range(_WANDER_STEPS + 1)]

    # stepsLeft starts at 0, so the first pick re-rolls; that direction is
    # held for _WANDER_STEPS picks before the next re-roll.
    assert directions == [1] * _WANDER_STEPS + [2]


def test_not_hungry_npc_in_empty_room_wanders():
    room, npc, behavior = _setup()
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior.getStateName() == "wandering"
    assert behavior.getGoalDescription() == "exploring"
    assert _npcXY(room, npc) != (2, 2)
