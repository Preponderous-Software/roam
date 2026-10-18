import json
import threading
from unittest.mock import MagicMock

from entity.grass import Grass
from entity.stone import Stone
from entity.torch import Torch
from player.player import Player
from rendering.web3dWorldViewSink import Web3DWorldViewSink
from rendering.webRenderer import WebRenderer
from ui.geometry import Rect
from world.dayNightCycle import DayNightCycle
from world.room import Room
from world.worldViewBuilder import WorldViewBuilder

GRID = 4


def _room(x, y):
    room = Room("r", GRID, (5, 6, 7), x, y, MagicMock())
    room.getGrid().getLocationByCoordinates(0, 0).addEntity(Grass())
    return room


def _world():
    rooms = [_room(x, 0) for x in (-1, 0, 1, 2)]
    player = Player(0)
    rooms[1].addEntityToLocation(
        player, rooms[1].getGrid().getLocationByCoordinates(1, 1)
    )
    rooms[1].getGrid().getLocationByCoordinates(2, 2).addEntity(Torch())
    fakeMap = MagicMock()
    fakeMap._lock = threading.Lock()
    fakeMap.getRooms.return_value = rooms
    config = MagicMock()
    config.dayNightCycleEnabled = True
    config.dayNightCycleLengthTicks = 100
    config.cameraFollowPlayer = True
    builder = WorldViewBuilder(DayNightCycle(config), config)
    return rooms, player, fakeMap, builder


def _keys(message):
    return {(r["x"], r["y"], r["z"]) for r in message["rooms"]}


def test_first_message_is_full_then_only_changed_rooms_are_sent():
    rooms, player, fakeMap, builder = _world()
    sink = Web3DWorldViewSink(lambda m: None)

    first = sink.encode(builder.build(fakeMap, player, 0, 1))
    second = sink.encode(builder.build(fakeMap, player, 1, 1))
    rooms[2].getGrid().getLocationByCoordinates(3, 3).addEntity(Stone())
    third = sink.encode(builder.build(fakeMap, player, 2, 1))

    assert first["full"] is True
    assert _keys(first) == {(-1, 0, 0), (0, 0, 0), (1, 0, 0)}
    assert second["full"] is False and second["rooms"] == []
    assert _keys(third) == {(1, 0, 0)}
    assert [first["seq"], second["seq"], third["seq"]] == [1, 2, 3]


def test_rooms_leaving_the_view_are_dropped_and_a_resync_resends_everything():
    rooms, player, fakeMap, builder = _world()
    sink = Web3DWorldViewSink(lambda m: None)
    sink.encode(builder.build(fakeMap, player, 0, 1))

    fakeMap.getRooms.return_value = rooms[1:]  # (-1, 0) no longer loaded
    shrunk = sink.encode(builder.build(fakeMap, player, 1, 1))
    sink.requestFull()
    resync = sink.encode(builder.build(fakeMap, player, 2, 1))

    assert shrunk["dropped"] == [[-1, 0, 0]]
    assert resync["full"] is True
    assert _keys(resync) == {(0, 0, 0), (1, 0, 0)}


def test_message_has_the_snapshot_shape_and_is_json_serialisable():
    rooms, player, fakeMap, builder = _world()
    sink = Web3DWorldViewSink(lambda m: None)

    message = sink.encode(builder.build(fakeMap, player, 50, 1))

    json.dumps(message)
    assert message["type"] == "worldview" and message["v"] == 1
    assert message["player"] == {"room": [0, 0, 0], "x": 1, "y": 1, "direction": "down"}
    assert message["dayNight"]["phase"] == "night"
    assert message["lights"] == [
        {"room": [0, 0, 0], "x": 2, "y": 2, "radiusTiles": 6, "entityClass": "Torch"}
    ]
    home = next(r for r in message["rooms"] if (r["x"], r["z"]) == (0, 0))
    names = [[message["classes"][i] for i in stack] for stack in home["tiles"]]
    assert names[0] == ["Grass"] and names[2 * GRID + 2] == ["Torch"]
    assert names[1 * GRID + 1] == []  # the player is not a tile entity
    assert dict(zip(message["classes"], message["classImages"]))["Grass"] == (
        "assets/images/grass.png"
    )


class _FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _runTicks(sink, clock, costMs, ticks, tickSeconds=1.0 / 30.0):
    sink.encode = lambda worldView: {}
    published = 0
    for _ in range(ticks):
        clock.now += tickSeconds
        if sink.wantsWorldView():
            clock.now += costMs / 1000.0
            sink.publish(None)
            published += 1
    return published


def test_cadence_adapts_to_measured_cost():
    clock = _FakeClock()
    cheap = Web3DWorldViewSink(lambda m: None, clock=clock)
    assert _runTicks(cheap, clock, 0.5, 30) == 30
    assert cheap.getEvery() == 1

    clock = _FakeClock()
    costly = Web3DWorldViewSink(lambda m: None, clock=clock)
    _runTicks(costly, clock, 5.0, 60)
    assert costly.getEvery() == 3

    clock = _FakeClock()
    huge = Web3DWorldViewSink(lambda m: None, clock=clock)
    _runTicks(huge, clock, 100.0, 60)
    assert huge.getEvery() == Web3DWorldViewSink.MAX_EVERY


def test_never_publishes_faster_than_30_a_second():
    clock = _FakeClock()
    sink = Web3DWorldViewSink(lambda m: None, clock=clock)

    # An uncapped loop at 300 ticks a second for one second.
    published = _runTicks(sink, clock, 0.1, 300, tickSeconds=1.0 / 300.0)

    # 30 a second, with 10% slack so a loop paced at exactly 30 TPS is never
    # skipped.
    assert 28 <= published <= 34


def test_publish_posts_and_times_itself():
    rooms, player, fakeMap, builder = _world()
    clock = _FakeClock()
    posted = []
    sink = Web3DWorldViewSink(posted.append, clock=clock)

    assert sink.wantsWorldView() is True
    clock.now += 0.009  # 9 ms
    sink.publish(builder.build(fakeMap, player, 0, 1))

    assert len(posted) == 1 and posted[0]["full"] is True
    assert sink.getAverageMs() == 9.0
    assert sink.getEvery() == 5
    answers = []
    for _ in range(5):
        clock.now += 1.0 / 30.0
        answers.append(sink.wantsWorldView())
    assert answers == [False] * 4 + [True]


# --- the web renderer's 3D capability ----------------------------------------


def test_web_renderer_defaults_to_2d():
    renderer = WebRenderer(lambda payload: None)

    assert renderer.drawsWorldFromView() is False


def test_web_renderer_3d_mode_cuts_a_transparent_hole():
    sent = []
    renderer = WebRenderer(sent.append, drawsWorldFromView=True)

    renderer.clearRegion(Rect(10, 20, 300, 400))
    renderer.present()

    assert renderer.drawsWorldFromView() is True
    assert json.loads(sent[0])["calls"] == [
        {"op": "cut", "x": 10, "y": 20, "w": 300, "h": 400}
    ]
