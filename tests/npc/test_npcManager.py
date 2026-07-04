from types import SimpleNamespace
from unittest.mock import MagicMock

from entity.living.npc import Npc
from entity.oakWood import OakWood
from npc.npcManager import NpcManager
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


def test_toggle_mode_clears_behavior_cache():
    m = _manager()
    room = _room()
    m.spawnNpc(room, 0)
    m.tickRoom(room, 0)  # creates behavior entries
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
    m.tickRoom(room, 0)  # creates behavior record
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
    m.tickRoom(room, 0)
    state, goal = m.getBehaviorInfo(npc)
    assert isinstance(state, str)
    assert len(state) > 0
