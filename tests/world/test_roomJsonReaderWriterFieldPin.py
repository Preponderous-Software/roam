"""Pins the exact key set RoomJsonReaderWriter writes to a room save file.

RFC 0017 adds view-only state next to rooms (a WorldView revision, biome
inference). None of it may leak into saves. If this test fails, a field was
added to or removed from the room save format: that is a save-format change,
which needs a matching schemas/room.json change and the owner's review, not an
edit to this list.
"""

import random
from unittest.mock import MagicMock

from entity.living.chicken import Chicken
from player.player import Player
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.roomType import RoomType

ROOM_KEYS = {
    "backgroundColor",
    "x",
    "y",
    "z",
    "name",
    "id",
    "livingEntityIds",
    "grid",
    "creationDate",
}
GRID_KEYS = {"id", "columns", "rows", "locations"}
LOCATION_KEYS = {"id", "x", "y", "entities"}
ENTITY_KEYS = {
    "id",
    "entityClass",
    "name",
    "creationDate",
    "environmentId",
    "gridId",
    "locationId",
}
LIVING_ENTITY_KEYS = ENTITY_KEYS | {
    "energy",
    "tickCreated",
    "tickLastReproduced",
    "imagePath",
}


def _roomJson(resolve, test_config, tmp_path, roomType):
    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.gridSize = 5
    random.seed(7)
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 0
    room = RoomFactory(5, MagicMock(), tickCounter).createRoom(roomType, 0, 0)
    chicken = Chicken(0)
    room.addEntity(chicken)
    room.addLivingEntity(chicken)
    room.addEntity(Player(0))
    return resolve(RoomJsonReaderWriter).generateJsonForRoom(room)


def test_room_save_field_set_is_pinned(resolve, test_config, tmp_path):
    for roomType in (RoomType.GRASSLAND, RoomType.MOUNTAIN, RoomType.CAVE):
        roomJson = _roomJson(resolve, test_config, tmp_path, roomType)

        assert set(roomJson) == ROOM_KEYS
        assert set(roomJson["grid"]) == GRID_KEYS
        for location in roomJson["grid"]["locations"]:
            assert set(location) == LOCATION_KEYS
            for entity in location["entities"]:
                if entity["entityClass"] in ("Chicken", "Player"):
                    assert set(entity) == LIVING_ENTITY_KEYS
                elif entity["entityClass"] in ("Grass", "Stone", "CaveFloor"):
                    assert set(entity) == ENTITY_KEYS


def test_room_type_is_not_persisted(resolve, test_config, tmp_path):
    # roomType lives in memory only (roam#601 proposes persisting it; until
    # that separate decision is made, nothing in RFC 0017 may write it).
    roomJson = _roomJson(resolve, test_config, tmp_path, RoomType.FOREST)

    assert "roomType" not in roomJson
    assert "biome" not in roomJson
    assert "revision" not in roomJson
