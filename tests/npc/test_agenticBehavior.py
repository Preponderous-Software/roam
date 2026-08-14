"""Characterization tests for the agentic (CPC) NPC behavior.

No network call is ever made: the Anthropic client is replaced by a stub whose
`messages.create` returns a canned response, and the background thread that
`tick` spawns is captured and run inline so the real `_callAI` logic is
exercised on the test thread.
"""

import json
import queue
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from entity.apple import Apple
from entity.banana import Banana
from entity.fence import Fence
from entity.grass import Grass
from entity.living.chicken import Chicken
from entity.living.npc import Npc
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.woodFloor import WoodFloor
from npc import agenticBehavior as agenticBehaviorModule
from npc.agenticBehavior import (
    _CALL_INTERVAL_TICKS,
    AgenticBehavior,
    _cellGlyph,
)
from world.room import Room


def _config(tps=30):
    return SimpleNamespace(ticksPerSecond=tps)


def _setup(gridSize=5, npcEnergy=100, npcX=None, npcY=None):
    """Return (room, npc, behavior) with the NPC placed at the grid centre."""
    room = Room("Test", gridSize, (0, 0, 0), 0, 0, MagicMock())
    npc = Npc("Bob", 0)
    npc.setEnergy(npcEnergy)
    x = gridSize // 2 if npcX is None else npcX
    y = gridSize // 2 if npcY is None else npcY
    loc = room.getGrid().getLocationByCoordinates(x, y)
    room.addEntityToLocation(npc, loc)
    room.addLivingEntity(npc)
    behavior = AgenticBehavior()
    behavior._client = None
    return room, npc, behavior


def _locationOfNpc(room, npc):
    return room.getGrid().getLocation(npc.getLocationID())


def _stubClient(responseText):
    """A stand-in for `anthropic.Anthropic` that returns `responseText`."""
    block = SimpleNamespace(type="text", text=responseText)
    response = SimpleNamespace(content=[block])
    return SimpleNamespace(
        messages=SimpleNamespace(create=MagicMock(return_value=response))
    )


class _InlineThread:
    """Stands in for `threading.Thread`, running the target on `start()`."""

    instances = []

    def __init__(self, target=None, args=(), daemon=False):
        self._target = target
        self._args = args
        self.daemon = daemon
        _InlineThread.instances.append(self)

    def start(self):
        self._target(*self._args)


@pytest.fixture
def inlineThread(monkeypatch):
    _InlineThread.instances = []
    monkeypatch.setattr(agenticBehaviorModule.threading, "Thread", _InlineThread)
    return _InlineThread


# ------------------------------------------------------------------ #
# Client construction                                                  #
# ------------------------------------------------------------------ #


def test_build_client_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(agenticBehaviorModule, "_ANTHROPIC_AVAILABLE", True)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert AgenticBehavior._buildClient() is None


def test_build_client_returns_none_when_package_missing(monkeypatch):
    monkeypatch.setattr(agenticBehaviorModule, "_ANTHROPIC_AVAILABLE", False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert AgenticBehavior._buildClient() is None


def test_build_client_constructs_with_key(monkeypatch):
    monkeypatch.setattr(agenticBehaviorModule, "_ANTHROPIC_AVAILABLE", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        agenticBehaviorModule,
        "_anthropic_module",
        SimpleNamespace(Anthropic=lambda api_key: f"client:{api_key}"),
        raising=False,
    )
    assert AgenticBehavior._buildClient() == "client:test-key"


def test_build_client_swallows_construction_failure(monkeypatch):
    def explode(api_key):
        raise RuntimeError("no network")

    monkeypatch.setattr(agenticBehaviorModule, "_ANTHROPIC_AVAILABLE", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        agenticBehaviorModule,
        "_anthropic_module",
        SimpleNamespace(Anthropic=explode),
        raising=False,
    )
    assert AgenticBehavior._buildClient() is None


# ------------------------------------------------------------------ #
# Introspection and room-change flag                                   #
# ------------------------------------------------------------------ #


def test_wants_room_change_initially_false():
    _, _, behavior = _setup()
    assert behavior.wantsRoomChange() is False


def test_clear_room_change_request():
    _, _, behavior = _setup()
    behavior._wantsRoomChange = True
    behavior.clearRoomChangeRequest()
    assert behavior.wantsRoomChange() is False


def test_initial_state_and_goal():
    _, _, behavior = _setup()
    assert behavior.getStateName() == "cpc-idle"
    assert behavior.getGoalDescription() == ""


# ------------------------------------------------------------------ #
# Fallback to the programmatic FSM when no client is available         #
# ------------------------------------------------------------------ #


def test_tick_delegates_to_fallback_when_client_is_none():
    room, npc, behavior = _setup()
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert npc.getTickLastMoved() == 0  # the FSM acted
    assert behavior.getStateName().startswith("fsm:")
    assert behavior.getStateName() == "fsm:" + behavior._fallback.getStateName()
    assert behavior.getGoalDescription() == behavior._fallback.getGoalDescription()


def test_fallback_path_never_queues_an_ai_call(inlineThread):
    room, npc, behavior = _setup()
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert inlineThread.instances == []
    assert behavior._pendingCall is False


# ------------------------------------------------------------------ #
# Cooldown guard and queue draining                                    #
# ------------------------------------------------------------------ #


def test_tick_skips_when_cooldown_not_expired():
    room, npc, behavior = _setup()
    behavior._client = _stubClient("{}")
    behavior._actionQueue.put({"type": "idle"})
    npc.setTickLastMoved(100)

    # movementSpeed=15, tps=30 → cooldown of 2 ticks; only 1 has elapsed.
    behavior.tick(npc, room, 101, _config())

    assert behavior._actionQueue.qsize() == 1
    assert npc.getTickLastMoved() == 100


def test_tick_executes_one_queued_action_per_call():
    room, npc, behavior = _setup()
    behavior._client = _stubClient("{}")
    behavior._actionQueue.put({"type": "idle"})
    behavior._actionQueue.put({"type": "idle"})
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert behavior._actionQueue.qsize() == 1
    assert behavior.getStateName() == "cpc-idle"


def test_tick_schedules_ai_call_when_queue_is_drained(inlineThread):
    room, npc, behavior = _setup()
    behavior._client = _stubClient(
        json.dumps({"goal": "find wood", "actions": [{"type": "gather"}]})
    )
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())

    assert len(inlineThread.instances) == 1
    assert inlineThread.instances[0].daemon is True
    # The captured thread ran inline, so the response is already applied.
    assert behavior.getGoalDescription() == "find wood"
    assert behavior._actionQueue.get_nowait() == {"type": "gather"}
    assert behavior._pendingCall is False


def test_tick_does_not_schedule_a_second_call_before_the_interval(inlineThread):
    room, npc, behavior = _setup()
    behavior._client = _stubClient(json.dumps({"goal": "", "actions": []}))
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())
    behavior.tick(npc, room, 100, _config())

    assert len(inlineThread.instances) == 1


def test_tick_schedules_again_once_the_interval_has_elapsed(inlineThread):
    room, npc, behavior = _setup()
    behavior._client = _stubClient(json.dumps({"goal": "", "actions": []}))
    npc.setTickLastMoved(-1000)

    behavior.tick(npc, room, 0, _config())
    for tickNumber in range(1, _CALL_INTERVAL_TICKS + 1):
        npc.setTickLastMoved(-1000)
        behavior.tick(npc, room, tickNumber, _config())

    assert len(inlineThread.instances) == 2


# ------------------------------------------------------------------ #
# _callAI response handling                                            #
# ------------------------------------------------------------------ #


def test_call_ai_queues_actions_and_records_goal():
    _, _, behavior = _setup()
    behavior._client = _stubClient(
        json.dumps(
            {
                "goal": "build a shelter",
                "actions": [{"type": "move", "direction": 1}, {"type": "place"}],
            }
        )
    )
    behavior._pendingCall = True

    behavior._callAI("world state")

    assert behavior.getGoalDescription() == "build a shelter"
    assert behavior._actionQueue.get_nowait() == {"type": "move", "direction": 1}
    assert behavior._actionQueue.get_nowait() == {"type": "place"}
    assert behavior._pendingCall is False


def test_call_ai_strips_markdown_fences():
    _, _, behavior = _setup()
    payload = json.dumps({"goal": "fenced", "actions": [{"type": "idle"}]})
    behavior._client = _stubClient("```json\n" + payload + "\n```")

    behavior._callAI("world state")

    assert behavior.getGoalDescription() == "fenced"
    assert behavior._actionQueue.get_nowait() == {"type": "idle"}


def test_call_ai_skips_malformed_actions():
    _, _, behavior = _setup()
    behavior._client = _stubClient(
        json.dumps(
            {
                "goal": "mixed",
                "actions": ["not-a-dict", {"direction": 0}, {"type": "eat"}],
            }
        )
    )

    behavior._callAI("world state")

    assert behavior._actionQueue.get_nowait() == {"type": "eat"}
    assert behavior._actionQueue.empty()


def test_call_ai_keeps_previous_goal_when_response_omits_one():
    _, _, behavior = _setup()
    behavior._goalDescription = "previous goal"
    behavior._client = _stubClient(json.dumps({"goal": "", "actions": []}))

    behavior._callAI("world state")

    assert behavior.getGoalDescription() == "previous goal"


def test_call_ai_survives_invalid_json():
    _, _, behavior = _setup()
    behavior._client = _stubClient("not json at all")
    behavior._pendingCall = True

    behavior._callAI("world state")

    assert behavior._actionQueue.empty()
    assert behavior._pendingCall is False


def test_call_ai_survives_a_raising_client():
    _, _, behavior = _setup()
    behavior._client = SimpleNamespace(
        messages=SimpleNamespace(create=MagicMock(side_effect=RuntimeError("boom")))
    )
    behavior._pendingCall = True

    behavior._callAI("world state")

    assert behavior._actionQueue.empty()
    assert behavior._pendingCall is False


def test_call_ai_defaults_to_empty_object_without_a_text_block():
    _, _, behavior = _setup()
    block = SimpleNamespace(type="thinking", text="ignored")
    behavior._client = SimpleNamespace(
        messages=SimpleNamespace(
            create=MagicMock(return_value=SimpleNamespace(content=[block]))
        )
    )

    behavior._callAI("world state")

    assert behavior._actionQueue.empty()
    assert behavior.getGoalDescription() == ""


# ------------------------------------------------------------------ #
# World-state serialisation                                            #
# ------------------------------------------------------------------ #


def test_build_world_state_reports_unknown_position():
    room, npc, behavior = _setup()
    npc.setLocationID(-1)

    assert behavior._buildWorldState(npc, room) == "Position unknown. Idle."


def test_build_world_state_reports_position_and_energy():
    room, npc, behavior = _setup(npcEnergy=42)

    worldState = behavior._buildWorldState(npc, room)

    assert worldState.startswith("Position (2,2)  Energy 42/100")


def test_build_world_state_reports_empty_inventory():
    room, npc, behavior = _setup()

    assert "Inventory: empty" in behavior._buildWorldState(npc, room)


def test_build_world_state_summarises_inventory_stacks():
    room, npc, behavior = _setup()
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())

    assert "Inventory: OakWood×2" in behavior._buildWorldState(npc, room)


def test_build_world_state_draws_a_five_by_five_grid_around_the_npc():
    room, npc, behavior = _setup(gridSize=7)
    gridRows = behavior._buildWorldState(npc, room).splitlines()[3:8]

    assert len(gridRows) == 5
    assert all(len(row.split(" ")) == 5 for row in gridRows)
    assert gridRows[2].split(" ")[2] == "@"


def test_build_world_state_places_neighbours_relative_to_the_npc():
    room, npc, behavior = _setup(gridSize=7)
    location = _locationOfNpc(room, npc)
    north = room.getGrid().getLocationByCoordinates(
        location.getX(), location.getY() - 1
    )
    room.addEntityToLocation(OakWood(), north)

    gridRows = behavior._buildWorldState(npc, room).splitlines()[3:8]

    assert gridRows[1].split(" ")[2] == "T"


def test_build_world_state_marks_off_grid_cells_with_a_question_mark():
    # Characterizes current behavior: out-of-bounds cells reuse the "?" glyph
    # that the legend assigns to creatures. Reported as a separate issue.
    room, npc, behavior = _setup(gridSize=5, npcX=0, npcY=0)

    gridRows = behavior._buildWorldState(npc, room).splitlines()[3:8]

    assert gridRows[0] == "? ? ? ? ?"
    assert gridRows[2].split(" ")[0] == "?"


# ------------------------------------------------------------------ #
# Cell glyphs                                                          #
# ------------------------------------------------------------------ #


def test_cell_glyph_is_dot_when_empty():
    room, _, _ = _setup()
    assert _cellGlyph(room.getGrid().getLocationByCoordinates(0, 0)) == "."


@pytest.mark.parametrize(
    "entityFactory, expectedGlyph",
    [
        (Apple, "A"),
        (Banana, "B"),
        (OakWood, "T"),
        (Stone, "S"),
        (WoodFloor, "W"),
    ],
)
def test_cell_glyph_for_known_entities(entityFactory, expectedGlyph):
    room, _, _ = _setup()
    location = room.getGrid().getLocationByCoordinates(0, 0)
    room.addEntityToLocation(entityFactory(), location)

    assert _cellGlyph(location) == expectedGlyph


def test_cell_glyph_prefers_living_entities():
    room, _, _ = _setup()
    location = room.getGrid().getLocationByCoordinates(0, 0)
    room.addEntityToLocation(Apple(), location)
    room.addEntityToLocation(Chicken(0), location)

    assert _cellGlyph(location) == "?"


def test_cell_glyph_is_hash_for_an_unlisted_solid_entity():
    room, _, _ = _setup()
    location = room.getGrid().getLocationByCoordinates(0, 0)
    fence = Fence()
    assert fence.isSolid()  # guards the premise of this test
    room.addEntityToLocation(fence, location)

    assert _cellGlyph(location) == "#"


def test_cell_glyph_is_dot_for_an_unlisted_passable_entity():
    room, _, _ = _setup()
    location = room.getGrid().getLocationByCoordinates(0, 0)
    room.addEntityToLocation(Grass(), location)

    assert _cellGlyph(location) == "."


# ------------------------------------------------------------------ #
# Action execution — movement                                          #
# ------------------------------------------------------------------ #


def test_execute_action_does_nothing_without_a_location():
    room, npc, behavior = _setup()
    npc.setLocationID(-1)

    behavior._executeAction({"type": "move", "direction": 0}, npc, room, 5)

    assert behavior.getStateName() == "cpc-idle"
    assert behavior.wantsRoomChange() is False


def test_execute_action_moves_the_npc():
    room, npc, behavior = _setup(gridSize=7)
    before = npc.getLocationID()

    behavior._executeAction({"type": "move", "direction": 0}, npc, room, 5)

    assert npc.getLocationID() != before
    assert behavior.getStateName() == "cpc-move"
    assert npc.getTickLastMoved() == 5


def test_execute_action_wraps_out_of_range_directions():
    room, npc, behavior = _setup(gridSize=7)
    location = _locationOfNpc(room, npc)
    expected = room.getGrid().getLocationByCoordinates(
        location.getX() + 1, location.getY()
    )

    # 7 % 4 == 3 == right
    behavior._executeAction({"type": "move", "direction": 7}, npc, room, 5)

    assert npc.getLocationID() == expected.getID()


def test_execute_action_requests_a_room_change_at_the_boundary():
    room, npc, behavior = _setup(gridSize=5, npcX=0, npcY=0)
    before = npc.getLocationID()

    behavior._executeAction({"type": "move", "direction": 0}, npc, room, 5)

    assert behavior.wantsRoomChange() is True
    assert npc.getLocationID() == before
    assert npc.getTickLastMoved() == 5
    assert behavior.getStateName() == "cpc-move"


# ------------------------------------------------------------------ #
# Action execution — gather                                            #
# ------------------------------------------------------------------ #


def test_execute_action_gathers_an_item_from_the_current_tile():
    room, npc, behavior = _setup()
    location = _locationOfNpc(room, npc)
    wood = OakWood()
    room.addEntityToLocation(wood, location)

    behavior._executeAction({"type": "gather"}, npc, room, 7)

    assert npc.getInventory().getNumItemsByType(OakWood) == 1
    assert wood.getID() not in location.getEntities()
    assert npc.getTickLastGathered() == 7
    assert behavior.getStateName() == "cpc-gather"


def test_execute_action_ignores_living_entities_when_gathering():
    room, npc, behavior = _setup()
    location = _locationOfNpc(room, npc)
    chicken = Chicken(0)
    room.addEntityToLocation(chicken, location)

    behavior._executeAction({"type": "gather"}, npc, room, 7)

    assert chicken.getID() in location.getEntities()
    assert npc.getInventory().getNumTakenInventorySlots() == 0


def test_execute_action_leaves_ungatherable_entities_in_place():
    room, npc, behavior = _setup()
    location = _locationOfNpc(room, npc)
    floor = WoodFloor()
    room.addEntityToLocation(floor, location)

    behavior._executeAction({"type": "gather"}, npc, room, 7)

    assert floor.getID() in location.getEntities()
    assert npc.getInventory().getNumTakenInventorySlots() == 0


def test_execute_action_leaves_the_item_when_the_inventory_is_full():
    room, npc, behavior = _setup()
    while npc.getInventory().placeIntoFirstAvailableInventorySlot(Stone()):
        pass
    location = _locationOfNpc(room, npc)
    apple = Apple()
    room.addEntityToLocation(apple, location)

    behavior._executeAction({"type": "gather"}, npc, room, 7)

    assert apple.getID() in location.getEntities()


# ------------------------------------------------------------------ #
# Action execution — eat                                               #
# ------------------------------------------------------------------ #


def test_execute_action_eats_food_from_the_inventory():
    room, npc, behavior = _setup(npcEnergy=10)
    apple = Apple()
    appleEnergy = apple.getEnergy()
    npc.getInventory().placeIntoFirstAvailableInventorySlot(apple)

    behavior._executeAction({"type": "eat"}, npc, room, 9)

    assert npc.getEnergy() == pytest.approx(10 + appleEnergy)
    assert npc.getInventory().getNumTakenInventorySlots() == 0
    assert npc.getTickLastMoved() == 9
    assert behavior.getStateName() == "cpc-eat"


def test_execute_action_eats_regardless_of_hunger():
    room, npc, behavior = _setup(npcEnergy=100)
    apple = Apple()
    npc.getInventory().placeIntoFirstAvailableInventorySlot(apple)

    behavior._executeAction({"type": "eat"}, npc, room, 9)

    assert npc.getInventory().getNumTakenInventorySlots() == 0


def test_execute_action_skips_non_food_when_eating():
    room, npc, behavior = _setup(npcEnergy=10)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(Stone())

    behavior._executeAction({"type": "eat"}, npc, room, 9)

    assert npc.getEnergy() == pytest.approx(10)
    assert npc.getInventory().getNumItemsByType(Stone) == 1


# ------------------------------------------------------------------ #
# Action execution — place                                             #
# ------------------------------------------------------------------ #


def test_execute_action_places_wood_on_an_adjacent_tile():
    room, npc, behavior = _setup(gridSize=7)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    location = _locationOfNpc(room, npc)
    target = room.getGrid().getLocationByCoordinates(
        location.getX() + 1, location.getY()
    )

    behavior._executeAction({"type": "place", "dx": 1, "dy": 0}, npc, room, 11)

    assert len(target.getEntities()) == 1
    assert npc.getInventory().getNumItemsByType(OakWood) == 0
    assert npc.getTickLastPlaced() == 11
    assert behavior.getStateName() == "cpc-place"


def test_execute_action_place_is_a_no_op_without_wood():
    room, npc, behavior = _setup(gridSize=7)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(Stone())
    location = _locationOfNpc(room, npc)
    target = room.getGrid().getLocationByCoordinates(
        location.getX() + 1, location.getY()
    )

    behavior._executeAction({"type": "place", "dx": 1, "dy": 0}, npc, room, 11)

    assert target.getEntities() == {}
    assert npc.getInventory().getNumItemsByType(Stone) == 1
    assert npc.getTickLastMoved() == 11


def test_execute_action_place_is_a_no_op_off_grid():
    room, npc, behavior = _setup(gridSize=5, npcX=0, npcY=0)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())

    behavior._executeAction({"type": "place", "dx": -1, "dy": 0}, npc, room, 11)

    assert npc.getInventory().getNumItemsByType(OakWood) == 1
    assert npc.getTickLastMoved() == 11


def test_execute_action_place_is_a_no_op_onto_a_solid_tile():
    room, npc, behavior = _setup(gridSize=7)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    location = _locationOfNpc(room, npc)
    target = room.getGrid().getLocationByCoordinates(
        location.getX() + 1, location.getY()
    )
    room.addEntityToLocation(Stone(), target)

    behavior._executeAction({"type": "place", "dx": 1, "dy": 0}, npc, room, 11)

    assert npc.getInventory().getNumItemsByType(OakWood) == 1
    assert len(target.getEntities()) == 1


def test_execute_action_place_is_a_no_op_onto_a_living_entity():
    room, npc, behavior = _setup(gridSize=7)
    npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
    location = _locationOfNpc(room, npc)
    target = room.getGrid().getLocationByCoordinates(
        location.getX() + 1, location.getY()
    )
    room.addEntityToLocation(Chicken(0), target)

    behavior._executeAction({"type": "place", "dx": 1, "dy": 0}, npc, room, 11)

    assert npc.getInventory().getNumItemsByType(OakWood) == 1
    assert len(target.getEntities()) == 1


# ------------------------------------------------------------------ #
# Action execution — idle and unknown types                            #
# ------------------------------------------------------------------ #


@pytest.mark.parametrize("action", [{"type": "idle"}, {"type": "dance"}, {}])
def test_execute_action_idles_on_idle_and_unknown_types(action):
    room, npc, behavior = _setup()
    before = npc.getLocationID()

    behavior._executeAction(action, npc, room, 13)

    assert npc.getLocationID() == before
    assert npc.getTickLastMoved() == 13
    assert behavior.getStateName() == "cpc-idle"


def test_action_queue_is_empty_on_construction():
    _, _, behavior = _setup()
    assert isinstance(behavior._actionQueue, queue.Queue)
    assert behavior._actionQueue.empty()
