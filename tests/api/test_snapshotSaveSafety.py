"""Save-safety tests for RFC 0017 (Roam 3D).

Viewing the world must never change a save. The most likely way to break one
is a viewer that loads or generates a neighbouring room: that room is then
saved and alters the world the player would otherwise have generated.
"""

import os
import random

import pytest

from api.restApiServer import RestApiServer
from api.worldSnapshot import MAX_RADIUS
from player.player import Player
from screen.worldScreen import WorldScreen
from world import roomJsonReaderWriter as roomJsonReaderWriterModule
from world.map import Map
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.startingHomeGenerator import StartingHomeGenerator
from world.worldViewBuilder import WorldViewBuilder

LOADED_ROOMS = [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (1, 1, 0), (0, 0, -1)]


def _seededWorld(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.gridSize = 17
    test_config.dayNightCycleEnabled = True
    test_config.cameraFollowPlayer = True
    random.seed(20261018)
    worldMap = resolve(Map)
    home = worldMap.generateNewRoom(0, 0)
    for x, y, z in LOADED_ROOMS:
        worldMap.generateNewRoom(x, y, z)
    player = resolve(Player)
    home.addEntityToLocation(player, StartingHomeGenerator().generate(home))
    server = resolve(RestApiServer)
    server.setMap(worldMap)
    return worldMap, server, resolve(WorldViewBuilder), player


def _viewAndSnapshot(worldMap, server, builder, player, radius, tick=0):
    # The game thread's publish step (WorldScreen._publishWorldView) followed
    # by the HTTP thread's read, as in a running game.
    worldView = builder.build(worldMap, player, tick, MAX_RADIUS)
    server.getWorldViewSink().publish(worldView)
    return worldView, server.getSnapshot(radius)


def _saveAllRooms(resolve, test_config, worldMap):
    writer = resolve(RoomJsonReaderWriter)
    for room in worldMap.getRooms():
        writer.saveRoom(
            room, test_config.getRoomFilePath(room.getX(), room.getY(), room.getZ())
        )


def _readSaveDirectory(path):
    files = {}
    for directory, _, names in os.walk(path):
        for name in names:
            fullPath = os.path.join(directory, name)
            with open(fullPath, "rb") as saveFile:
                files[os.path.relpath(fullPath, path)] = saveFile.read()
    return files


def test_snapshots_leave_the_save_byte_identical(resolve, test_config, tmp_path):
    worldMap, server, builder, player = _seededWorld(resolve, test_config, tmp_path)
    _saveAllRooms(resolve, test_config, worldMap)
    before = _readSaveDirectory(tmp_path)

    for tick in range(5):
        for radius in range(MAX_RADIUS + 1):
            worldView, (status, _) = _viewAndSnapshot(
                worldMap, server, builder, player, radius, tick
            )
            assert worldView is not None
            assert status == 200
    _saveAllRooms(resolve, test_config, worldMap)
    after = _readSaveDirectory(tmp_path)

    assert len(before) == len(LOADED_ROOMS) + 1
    assert after.keys() == before.keys()
    for path in before:
        assert after[path] == before[path], path


def _raiser(name):
    def _raise(*args, **kwargs):
        raise AssertionError(name + " must not be called while building a view")

    return _raise


def test_snapshot_never_loads_generates_or_writes_rooms(
    resolve, test_config, tmp_path, monkeypatch
):
    worldMap, server, builder, player = _seededWorld(resolve, test_config, tmp_path)
    _saveAllRooms(resolve, test_config, worldMap)
    roomCount = len(worldMap.getRooms())
    for name in ("getRoom", "generateNewRoom", "addRoom"):
        monkeypatch.setattr(Map, name, _raiser("Map." + name))
    for name in ("createRoom", "createRandomRoom", "createCaveRoom"):
        monkeypatch.setattr(RoomFactory, name, _raiser("RoomFactory." + name))
    for name in ("saveRoom", "loadRoom", "generateJsonForRoom"):
        monkeypatch.setattr(
            RoomJsonReaderWriter, name, _raiser("RoomJsonReaderWriter." + name)
        )
    monkeypatch.setattr(
        roomJsonReaderWriterModule,
        "writeJsonAtomically",
        _raiser("writeJsonAtomically"),
    )
    monkeypatch.setattr(WorldScreen, "getOrLoadRoom", _raiser("getOrLoadRoom"))

    worldView, (status, snapshot) = _viewAndSnapshot(
        worldMap, server, builder, player, MAX_RADIUS
    )

    assert len(worldView.getRooms()) == roomCount
    assert status == 200
    # Radius 3 reaches 49 surface positions, but only the loaded ones appear.
    assert len(snapshot["rooms"]) == roomCount
    assert len(worldMap.getRooms()) == roomCount


@pytest.mark.parametrize("radius", [0, 1, MAX_RADIUS])
def test_snapshot_does_not_touch_the_rooms_directory(
    resolve, test_config, tmp_path, radius
):
    worldMap, server, builder, player = _seededWorld(resolve, test_config, tmp_path)

    _viewAndSnapshot(worldMap, server, builder, player, radius)

    assert not os.path.exists(test_config.getRoomsDirectory())
