from types import SimpleNamespace
from unittest.mock import MagicMock

from entity.apple import Apple
from entity.living.chicken import Chicken
from entity.living.npc import Npc
from entity.oakWood import OakWood
from entity.stone import Stone
from npc.agenticBehavior import AgenticBehavior
from npc.npcManager import NpcManager
from npc.programmaticBehavior import ProgrammaticBehavior
from world.room import Room


def _config():
    return SimpleNamespace(ticksPerSecond=30, npcMode="npc")


def _room(gridSize=5):
    return Room("Test", gridSize, (0, 0, 0), 0, 0, MagicMock())


def _manager():
    return NpcManager(_config())


# ------------------------------------------------------------------ #
# Mode management                                                      #
# ------------------------------------------------------------------ #


def test_default_mode_is_npc():
    assert _manager().getMode() == "npc"


def test_default_mode_display():
    assert _manager().getModeDisplay() == "NPC"


def test_toggle_mode_npc_to_cpc():
    m = _manager()
    m.toggleMode()
    assert m.getMode() == "cpc"
    assert m.getModeDisplay() == "CPC"


def test_toggle_mode_cpc_back_to_npc():
    m = _manager()
    m.toggleMode()
    m.toggleMode()
    assert m.getMode() == "npc"


def _tick_room(manager, room, tick):
    """Helper: tick one room by wrapping tickActiveRooms with a minimal map mock."""
    mock_map = MagicMock()
    mock_map.getRoom.return_value = room
    manager.tickActiveRooms(mock_map, 0, 0, 0, 0, tick)


def test_toggle_mode_clears_behavior_cache():
    m = _manager()
    room = _room()
    m.spawnNpc(room, 0)
    _tick_room(m, room, 0)  # creates behavior entries
    assert len(m._behaviors) > 0
    m.toggleMode()
    assert len(m._behaviors) == 0


# ------------------------------------------------------------------ #
# Spawning                                                             #
# ------------------------------------------------------------------ #


def test_spawn_npc_returns_npc_instance():
    m = _manager()
    npc = m.spawnNpc(_room(), 0)
    assert isinstance(npc, Npc)


def test_spawn_npc_adds_to_living_entities():
    m = _manager()
    room = _room()
    npc = m.spawnNpc(room, 0)
    assert npc.getID() in room.getLivingEntities()


def test_spawned_npc_mode_matches_manager():
    m = _manager()
    npc = m.spawnNpc(_room(), 0)
    assert npc.getMode() == "npc"


def test_spawned_npc_mode_cpc_when_manager_is_cpc():
    m = _manager()
    m.toggleMode()
    npc = m.spawnNpc(_room(), 0)
    assert npc.getMode() == "cpc"


# ------------------------------------------------------------------ #
# Death drops                                                          #
# ------------------------------------------------------------------ #


def test_drop_inventory_at_death_places_items_in_room():
    m = _manager()
    room = _room()
    npc = m.spawnNpc(room, 0)
    wood = OakWood()
    npc.getInventory().placeIntoFirstAvailableInventorySlot(wood)

    loc = room.getGrid().getLocation(npc.getLocationID())
    before = len(loc.getEntities())
    m.dropInventoryAtDeath(npc, room)
    assert len(loc.getEntities()) > before


def test_drop_inventory_at_death_empties_inventory():
    m = _manager()
    room = _room()
    npc = m.spawnNpc(room, 0)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    m.dropInventoryAtDeath(npc, room)
    assert npc.getInventory().getNumTakenInventorySlots() == 0


# ------------------------------------------------------------------ #
# Cleanup                                                              #
# ------------------------------------------------------------------ #


def test_cleanup_removes_behavior_for_dead_npc():
    m = _manager()
    room = _room()
    npc = m.spawnNpc(room, 0)
    _tick_room(m, room, 0)  # creates behavior record
    assert npc.getID() in m._behaviors
    room.removeLivingEntity(npc)
    m.cleanupDeadNpcs(room)
    assert npc.getID() not in m._behaviors


# ------------------------------------------------------------------ #
# Behavior introspection                                               #
# ------------------------------------------------------------------ #


def test_get_behavior_info_before_tick_returns_mode_name():
    m = _manager()
    room = _room()
    npc = m.spawnNpc(room, 0)
    state, goal = m.getBehaviorInfo(npc)
    assert state == "npc"
    assert goal == ""


def test_get_behavior_info_after_tick_has_state():
    m = _manager()
    room = _room()
    npc = m.spawnNpc(room, 0)
    _tick_room(m, room, 0)
    state, goal = m.getBehaviorInfo(npc)
    assert isinstance(state, str)
    assert len(state) > 0


def test_get_behavior_info_reports_cached_behavior():
    m = _manager()
    npc = m.spawnNpc(_room(), 0)
    m._behaviors[npc.getID()] = _StubBehavior(stateName="stub", goal="goal")
    assert m.getBehaviorInfo(npc) == ("stub", "goal")


# ------------------------------------------------------------------ #
# Spawning edge cases                                                  #
# ------------------------------------------------------------------ #


def _fillWithStone(room):
    grid = room.getGrid()
    for lid in grid.getLocations():
        room.addEntityToLocation(Stone(), grid.getLocation(lid))


def test_spawn_npc_seeds_three_wood_and_three_apples():
    npc = _manager().spawnNpc(_room(), 0)
    items = []
    for slot in npc.getInventory().getInventorySlots():
        items.extend(slot.getContents())
    assert sum(isinstance(i, OakWood) for i in items) == 3
    assert sum(isinstance(i, Apple) for i in items) == 3


def test_spawn_npc_lands_on_non_solid_location():
    room = _room()
    grid = room.getGrid()
    lids = list(grid.getLocations())
    openLid = lids[-1]
    for lid in lids:
        if lid != openLid:
            room.addEntityToLocation(Stone(), grid.getLocation(lid))
    npc = _manager().spawnNpc(room, 0)
    assert npc.getLocationID() == openLid


def test_find_open_spawn_location_is_none_when_every_tile_is_solid():
    room = _room()
    _fillWithStone(room)
    assert _manager()._findOpenSpawnLocation(room) is None


def test_spawn_npc_still_placed_when_every_tile_is_solid():
    room = _room()
    _fillWithStone(room)
    npc = _manager().spawnNpc(room, 0)
    assert npc.getLocationID() in room.getGrid().getLocations()
    assert npc.getID() in room.getLivingEntities()


def test_drop_inventory_at_death_is_noop_when_npc_not_in_grid():
    m = _manager()
    room = _room()
    npc = Npc("Ghost", 0)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    m.dropInventoryAtDeath(npc, room)
    assert npc.getInventory().getNumTakenInventorySlots() == 1
    assert room.getGrid().getNumEntities() == 0


# ------------------------------------------------------------------ #
# Behavior selection                                                   #
# ------------------------------------------------------------------ #


def test_get_behavior_is_programmatic_in_npc_mode():
    m = _manager()
    npc = Npc("Bob", 0)
    npc.setMode("npc")
    assert isinstance(m._getBehavior(npc), ProgrammaticBehavior)


def test_get_behavior_is_agentic_when_npc_itself_is_cpc():
    m = _manager()
    npc = Npc("Bob", 0)
    npc.setMode("cpc")
    assert m.getMode() == "npc"
    assert isinstance(m._getBehavior(npc), AgenticBehavior)


def test_get_behavior_is_agentic_when_manager_is_cpc():
    m = _manager()
    m.toggleMode()
    npc = Npc("Bob", 0)
    npc.setMode("npc")
    assert isinstance(m._getBehavior(npc), AgenticBehavior)


def test_get_behavior_is_cached_per_npc():
    m = _manager()
    npc = Npc("Bob", 0)
    assert m._getBehavior(npc) is m._getBehavior(npc)


# ------------------------------------------------------------------ #
# Tick dispatch                                                        #
# ------------------------------------------------------------------ #


class _StubBehavior:
    """Minimal NpcBehavior stand-in that records ticks and can request exit."""

    def __init__(self, wantsExit=False, stateName="stub", goal=""):
        self.ticks = []
        self.wantsExit = wantsExit
        self.cleared = 0
        self.stateName = stateName
        self.goal = goal

    def tick(self, npc, room, tick, config):
        self.ticks.append(tick)

    def getStateName(self):
        return self.stateName

    def getGoalDescription(self):
        return self.goal

    def wantsRoomChange(self):
        return self.wantsExit

    def clearRoomChangeRequest(self):
        self.cleared += 1
        self.wantsExit = False


class _FakeMap:
    def __init__(self, rooms):
        self.rooms = rooms
        self.requested = []

    def getRoom(self, x, y, z):
        self.requested.append((x, y, z))
        return self.rooms.get((x, y, z), -1)


def _roomAt(x, y, z=0, gridSize=5):
    return Room("Test", gridSize, (0, 0, 0), x, y, MagicMock(), z)


def _placeNpc(room, x, y):
    npc = Npc("Bob", 0)
    room.addEntityToLocation(npc, room.getGrid().getLocationByCoordinates(x, y))
    room.addLivingEntity(npc)
    return npc


def test_tick_active_rooms_requests_every_room_in_radius():
    fakeMap = _FakeMap({})
    _manager().tickActiveRooms(fakeMap, 10, 20, -1, 1, 0)
    expected = {(10 + dx, 20 + dy, -1) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    assert set(fakeMap.requested) == expected
    assert len(fakeMap.requested) == 9


def test_tick_active_rooms_skips_unloaded_rooms():
    fakeMap = _FakeMap({(0, 0, 0): None})
    assert _manager().tickActiveRooms(fakeMap, 0, 0, 0, 1, 0) == set()


def test_tick_active_rooms_ignores_non_npc_living_entities():
    m = _manager()
    room = _roomAt(0, 0)
    chicken = Chicken(0)
    room.addEntity(chicken)
    room.addLivingEntity(chicken)
    m.tickActiveRooms(_FakeMap({(0, 0, 0): room}), 0, 0, 0, 0, 0)
    assert m._behaviors == {}


def test_tick_active_rooms_passes_tick_and_reports_no_dirty_rooms_without_exit():
    m = _manager()
    room = _roomAt(0, 0)
    npc = _placeNpc(room, 2, 2)
    stub = _StubBehavior()
    m._behaviors[npc.getID()] = stub
    dirty = m.tickActiveRooms(_FakeMap({(0, 0, 0): room}), 0, 0, 0, 0, 42)
    assert stub.ticks == [42]
    assert dirty == set()


def test_tick_active_rooms_moves_exiting_npc_and_marks_both_rooms_dirty():
    m = _manager()
    fromRoom = _roomAt(0, 0)
    toRoom = _roomAt(1, 0)
    npc = _placeNpc(fromRoom, 4, 2)
    stub = _StubBehavior(wantsExit=True)
    m._behaviors[npc.getID()] = stub
    fakeMap = _FakeMap({(0, 0, 0): fromRoom, (1, 0, 0): toRoom})
    dirty = m.tickActiveRooms(fakeMap, 0, 0, 0, 0, 0)
    assert dirty == {fromRoom, toRoom}
    assert stub.cleared == 1
    assert npc.getID() in toRoom.getLivingEntities()
    assert npc.getID() not in fromRoom.getLivingEntities()


def test_tick_active_rooms_marks_only_source_dirty_when_crossing_fails():
    m = _manager()
    fromRoom = _roomAt(0, 0)
    npc = _placeNpc(fromRoom, 4, 2)
    m._behaviors[npc.getID()] = _StubBehavior(wantsExit=True)
    dirty = m.tickActiveRooms(_FakeMap({(0, 0, 0): fromRoom}), 0, 0, 0, 0, 0)
    assert dirty == {fromRoom}
    assert npc.getID() in fromRoom.getLivingEntities()


# ------------------------------------------------------------------ #
# Room crossing                                                        #
# ------------------------------------------------------------------ #


def _cross(startX, startY, targetRoomCoords):
    fromRoom = _roomAt(0, 0)
    npc = _placeNpc(fromRoom, startX, startY)
    rooms = {(0, 0, 0): fromRoom}
    targetRoom = None
    if targetRoomCoords is not None:
        targetRoom = _roomAt(targetRoomCoords[0], targetRoomCoords[1])
        rooms[(targetRoomCoords[0], targetRoomCoords[1], 0)] = targetRoom
    result = _manager()._handleRoomCrossing(npc, fromRoom, _FakeMap(rooms), 0)
    return npc, fromRoom, targetRoom, result


def _npcCoords(npc, room):
    loc = room.getGrid().getLocation(npc.getLocationID())
    return (loc.getX(), loc.getY())


def test_crossing_west_edge_enters_east_edge_of_room_to_the_west():
    npc, fromRoom, targetRoom, result = _cross(0, 2, (-1, 0))
    assert result is targetRoom
    assert _npcCoords(npc, targetRoom) == (4, 2)


def test_crossing_east_edge_enters_west_edge_of_room_to_the_east():
    npc, fromRoom, targetRoom, result = _cross(4, 3, (1, 0))
    assert result is targetRoom
    assert _npcCoords(npc, targetRoom) == (0, 3)


def test_crossing_north_edge_enters_south_edge_of_room_above():
    npc, fromRoom, targetRoom, result = _cross(1, 0, (0, -1))
    assert result is targetRoom
    assert _npcCoords(npc, targetRoom) == (1, 4)


def test_crossing_south_edge_enters_north_edge_of_room_below():
    npc, fromRoom, targetRoom, result = _cross(3, 4, (0, 1))
    assert result is targetRoom
    assert _npcCoords(npc, targetRoom) == (3, 0)


def test_crossing_removes_npc_from_source_room():
    npc, fromRoom, targetRoom, result = _cross(0, 2, (-1, 0))
    assert npc.getID() not in fromRoom.getLivingEntities()
    for lid in fromRoom.getGrid().getLocations():
        assert not fromRoom.getGrid().getLocation(lid).isEntityPresent(npc)
    assert npc.getID() in targetRoom.getLivingEntities()


def test_crossing_from_corner_is_refused():
    npc, fromRoom, targetRoom, result = _cross(0, 0, (-1, 0))
    assert result is None
    assert npc.getID() in fromRoom.getLivingEntities()
    assert npc.getID() not in targetRoom.getLivingEntities()


def test_crossing_from_interior_is_refused():
    npc, fromRoom, targetRoom, result = _cross(2, 2, (-1, 0))
    assert result is None
    assert npc.getID() in fromRoom.getLivingEntities()


def test_crossing_into_unloaded_room_is_refused():
    npc, fromRoom, targetRoom, result = _cross(0, 2, None)
    assert result is None
    assert npc.getID() in fromRoom.getLivingEntities()
    assert _npcCoords(npc, fromRoom) == (0, 2)


def test_crossing_with_stale_location_id_is_refused():
    fromRoom = _roomAt(0, 0)
    npc = Npc("Ghost", 0)
    fromRoom.addLivingEntity(npc)
    fakeMap = _FakeMap({(0, 0, 0): fromRoom, (-1, 0, 0): _roomAt(-1, 0)})
    assert _manager()._handleRoomCrossing(npc, fromRoom, fakeMap, 0) is None
    assert npc.getID() in fromRoom.getLivingEntities()
