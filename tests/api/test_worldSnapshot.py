import json
import threading
import urllib.error
import urllib.request
from unittest.mock import MagicMock

import pytest

from api import restApiServer as restApiServerModule
from api.restApiServer import RestApiServer
from api.worldSnapshot import (
    MAX_RADIUS,
    SNAPSHOT_FORMAT,
    clampRadius,
    worldViewToSnapshot,
)
from entity.grass import Grass
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.torch import Torch
from entity.woodFloor import WoodFloor
from player.player import Player
from world.dayNightCycle import DayNightCycle
from world.room import Room
from world.roomType import RoomType
from world.tickCounter import TickCounter
from world.worldViewBuilder import WorldViewBuilder, directionName

GRID = 5


def _room(x, y, z=0, color=(10, 20, 30)):
    return Room("r", GRID, color, x, y, MagicMock(), z)


def _put(room, entity, x, y):
    room.addEntityToLocation(entity, room.getGrid().getLocationByCoordinates(x, y))


def _config(dayNightEnabled=True):
    config = MagicMock()
    config.dayNightCycleEnabled = dayNightEnabled
    config.dayNightCycleLengthTicks = 1000
    config.cameraFollowPlayer = True
    return config


def _world():
    home = _room(0, 0)
    player = Player(0)
    _put(home, Grass(), 2, 3)
    _put(home, player, 2, 3)
    _put(home, Torch(), 1, 1)
    _put(home, Stone(), 4, 0)
    east = _room(1, 0)
    _put(east, Grass(), 0, 0)
    east.setRoomType(RoomType.FOREST)
    cave = _room(0, 0, -1)
    far = _room(3, 0)
    return [home, east, cave, far], home, player


def _makeMap(rooms):
    fakeMap = MagicMock()
    fakeMap._lock = threading.Lock()
    fakeMap.getRooms.return_value = rooms
    return fakeMap


def _view(rooms, player, tick=0, config=None, radius=MAX_RADIUS):
    config = config or _config()
    builder = WorldViewBuilder(DayNightCycle(config), config)
    return builder.build(_makeMap(rooms), player, tick, radius)


def _build(rooms, player, tick=0, radius=1, config=None):
    worldView = _view(rooms, player, tick, config)
    return None if worldView is None else worldViewToSnapshot(worldView, radius)


def test_snapshot_shape():
    rooms, _, player = _world()

    snapshot = _build(rooms, player, tick=500)

    assert snapshot["format"] == SNAPSHOT_FORMAT
    assert snapshot["version"] == 1
    assert snapshot["tick"] == 500
    assert snapshot["gridSize"] == GRID
    assert snapshot["dayNight"] == {
        "enabled": True,
        "cycleLengthTicks": 1000,
        "overlayOpacity": 200,
        "phase": "night",
    }
    assert snapshot["player"] == {
        "room": [0, 0, 0],
        "x": 2,
        "y": 3,
        "direction": "down",
    }
    assert len(snapshot["classes"]) == len(snapshot["classImages"])
    for room in snapshot["rooms"]:
        assert len(room["tiles"]) == GRID * GRID
        assert set(room) == {
            "x",
            "y",
            "z",
            "roomType",
            "biome",
            "backgroundColor",
            "tiles",
        }


def test_tiles_are_row_major_class_indices_without_the_player():
    rooms, _, player = _world()

    snapshot = _build(rooms, player)

    home = next(r for r in snapshot["rooms"] if r["x"] == 0 and r["z"] == 0)
    names = lambda tile: [snapshot["classes"][i] for i in tile]
    assert names(home["tiles"][3 * GRID + 2]) == ["Grass"]
    assert names(home["tiles"][1 * GRID + 1]) == ["Torch"]
    assert names(home["tiles"][0 * GRID + 4]) == ["Stone"]
    assert "Player" not in snapshot["classes"]
    images = dict(zip(snapshot["classes"], snapshot["classImages"]))
    assert images["Grass"] == "assets/images/grass.png"


def test_radius_limits_rooms_but_keeps_every_level():
    rooms, _, player = _world()

    near = {(r["x"], r["y"], r["z"]) for r in _build(rooms, player)["rooms"]}
    wide = {(r["x"], r["y"], r["z"]) for r in _build(rooms, player, radius=3)["rooms"]}
    zero = {(r["x"], r["y"], r["z"]) for r in _build(rooms, player, radius=0)["rooms"]}

    assert near == {(0, 0, 0), (1, 0, 0), (0, 0, -1)}
    assert wide == near | {(3, 0, 0)}
    assert zero == {(0, 0, 0), (0, 0, -1)}


def test_unloaded_rooms_are_absent():
    rooms, home, player = _world()

    snapshot = _build([home], player, radius=3)

    assert [(r["x"], r["y"], r["z"]) for r in snapshot["rooms"]] == [(0, 0, 0)]


def test_biome_uses_room_type_then_falls_back_to_inference():
    rooms, _, player = _world()

    byKey = {(r["x"], r["y"], r["z"]): r for r in _build(rooms, player)["rooms"]}

    assert byKey[(1, 0, 0)]["roomType"] == RoomType.FOREST
    assert byKey[(1, 0, 0)]["biome"] == RoomType.FOREST
    assert byKey[(0, 0, 0)]["roomType"] is None
    assert byKey[(0, 0, 0)]["biome"] == RoomType.GRASSLAND
    assert byKey[(0, 0, -1)]["biome"] == RoomType.CAVE


def test_home_walls_are_not_a_forest():
    rooms, home, player = _world()
    _put(home, OakWood(), 0, 4)
    _put(home, WoodFloor(), 1, 4)

    byKey = {(r["x"], r["y"], r["z"]): r for r in _build(rooms, player)["rooms"]}

    assert byKey[(0, 0, 0)]["biome"] == RoomType.GRASSLAND


def test_lights_are_in_tile_coordinates():
    rooms, _, player = _world()

    snapshot = _build(rooms, player)

    assert snapshot["lights"] == [
        {
            "room": [0, 0, 0],
            "x": 1,
            "y": 1,
            "radiusTiles": 6,
            "entityClass": "Torch",
        }
    ]


def test_background_color_is_a_list_of_ints():
    rooms, _, player = _world()

    snapshot = _build(rooms, player)

    assert snapshot["rooms"][0]["backgroundColor"] == [10, 20, 30]


def test_day_night_disabled_reports_no_overlay():
    rooms, _, player = _world()

    snapshot = _build(rooms, player, tick=500, config=_config(False))

    assert snapshot["dayNight"]["enabled"] is False
    assert snapshot["dayNight"]["overlayOpacity"] == 0


def test_player_not_in_a_loaded_room_gives_none():
    rooms, home, player = _world()

    assert _build(rooms[1:], player) is None


def test_direction_names():
    player = Player(0)
    assert directionName(player) == "down"
    player.setDirection(3)
    assert directionName(player) == "right"
    player.setDirection(-1)  # stopped: keep facing the last way moved
    assert directionName(player) == "right"
    player.setDirection(0)
    assert directionName(player) == "up"


def test_clamp_radius():
    assert clampRadius(-4) == 0
    assert clampRadius(2) == 2
    assert clampRadius(99) == MAX_RADIUS


# --- the REST endpoint ----------------------------------------------------


def _server(resolve, override_dependency, test_config, player):
    test_config.dayNightCycleEnabled = True
    test_config.dayNightCycleLengthTicks = 1000
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 0
    override_dependency(Player, player)
    override_dependency(TickCounter, tickCounter)
    return resolve(RestApiServer)


def test_get_snapshot_503_before_a_view_is_published(
    resolve, override_dependency, test_config
):
    server = _server(resolve, override_dependency, test_config, Player(0))

    status, payload = server.getSnapshot()

    assert status == 503


def test_get_snapshot_serves_the_published_view_and_clamps_radius(
    resolve, override_dependency, test_config
):
    rooms, _, player = _world()
    server = _server(resolve, override_dependency, test_config, player)
    server.getWorldViewSink().publish(_view(rooms, player, tick=77))

    status, payload = server.getSnapshot(99)

    assert status == 200
    assert payload["tick"] == 77
    assert payload["radius"] == MAX_RADIUS
    assert {(r["x"], r["y"], r["z"]) for r in payload["rooms"]} == {
        (0, 0, 0),
        (1, 0, 0),
        (0, 0, -1),
        (3, 0, 0),
    }


class _FakeClock:
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now


def test_rest_sink_wants_views_only_while_a_spectator_polls(
    resolve, override_dependency, test_config, monkeypatch
):
    clock = _FakeClock()
    monkeypatch.setattr(restApiServerModule, "time", clock)
    rooms, _, player = _world()
    test_config.restEnabled = True
    test_config.restPort = 0
    server = _server(resolve, override_dependency, test_config, player)
    sink = server.getWorldViewSink()

    assert sink.wantsWorldView() is False  # not running
    server.start()
    try:
        assert sink.wantsWorldView() is False  # running, nobody watching
        assert server.getSnapshot(2)[0] == 503  # first poll: no view yet
        assert sink.wantsWorldView() is True
        assert sink.getWantedRadiusRooms() == 2

        sink.publish(_view(rooms, player, radius=2))
        assert sink.wantsWorldView() is False  # throttled
        clock.now += sink.MIN_PUBLISH_SECONDS
        assert sink.wantsWorldView() is True

        server.getSnapshot(3)  # a wider radius than the latest view
        sink.publish(_view(rooms, player, radius=2))
        assert sink.wantsWorldView() is True

        clock.now += sink.WATCH_SECONDS + 1  # the spectator went away
        assert sink.wantsWorldView() is False
    finally:
        server.shutdown()

    assert sink.getLatest() is None  # the stale view is dropped
    assert server.getSnapshot()[0] == 503


def test_snapshot_over_http(resolve, override_dependency, test_config):
    rooms, _, player = _world()
    test_config.restEnabled = True
    test_config.restPort = 0
    server = _server(resolve, override_dependency, test_config, player)
    server.start()
    try:
        server.getWorldViewSink().publish(_view(rooms, player))
        port = server._httpServer.server_address[1]
        base = "http://127.0.0.1:" + str(port)
        with urllib.request.urlopen(base + "/api/v1/snapshot?radius=0") as response:
            payload = json.loads(response.read())
        with pytest.raises(urllib.error.HTTPError) as badRadius:
            urllib.request.urlopen(base + "/api/v1/snapshot?radius=abc")
    finally:
        server.shutdown()

    assert payload["format"] == SNAPSHOT_FORMAT
    assert payload["radius"] == 0
    assert badRadius.value.code == 400


def test_snapshot_never_claims_more_radius_than_the_view_has(
    resolve, override_dependency, test_config
):
    rooms, _, player = _world()
    server = _server(resolve, override_dependency, test_config, player)
    server.getWorldViewSink().publish(_view(rooms, player, radius=1))

    status, payload = server.getSnapshot(3)

    assert status == 200
    assert payload["radius"] == 1
    assert (3, 0, 0) not in {(r["x"], r["y"], r["z"]) for r in payload["rooms"]}
