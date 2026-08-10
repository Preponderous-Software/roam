import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import threading
from unittest.mock import MagicMock


def _makeWorldScreen(test_config, tmp_path, x=0, y=0, z=0):
    from screen.worldScreen import WorldScreen

    test_config.pathToSaveDirectory = str(tmp_path)
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = test_config
    ws.currentZ = z
    ws.currentRoom = MagicMock()
    ws.currentRoom.getX.return_value = x
    ws.currentRoom.getY.return_value = y
    ws.currentRoom.getZ.return_value = z
    ws.roomJsonReaderWriter = MagicMock()
    ws.roomJsonReaderWriter.generateJsonForRoom.return_value = {"z": z}
    ws._saveLock = threading.Lock()
    ws._saveInProgress = False
    ws._saveExecutor = MagicMock()
    return ws


def _submittedRoomPath(ws):
    return ws._saveExecutor.submit.call_args.args[2]


def test_async_save_of_a_surface_room_keeps_the_legacy_path(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path, x=1, y=2)

    ws.save()

    assert _submittedRoomPath(ws) == str(tmp_path) + "/rooms/room_1_2.json"


def test_async_save_of_a_cave_room_carries_the_level(test_config, tmp_path):
    # The async save built the room path without z, so a cave room's JSON was
    # written over the surface room's file at the same coordinates. Loading
    # (1, 2, 0) then returned cave content indexed under (1, 2, -1), losing the
    # surface room. The synchronous path already passed room.getZ().
    ws = _makeWorldScreen(test_config, tmp_path, x=1, y=2, z=-1)

    ws.save()

    assert _submittedRoomPath(ws) == str(tmp_path) + "/rooms/room_1_2_-1.json"


def test_async_and_synchronous_saves_agree_on_the_cave_room_path(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path, x=-3, y=4, z=-2)

    ws.save()

    expected = test_config.getRoomFilePath(
        ws.currentRoom.getX(), ws.currentRoom.getY(), ws.currentRoom.getZ()
    )
    assert _submittedRoomPath(ws) == expected
