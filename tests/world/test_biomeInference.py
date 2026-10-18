import random
from unittest.mock import MagicMock

import pytest

from world.biomeInference import inferBiome, inferBiomeFromClassNames
from world.roomFactory import RoomFactory
from world.roomType import RoomType
from world.startingHomeGenerator import StartingHomeGenerator

GRID_SIZE = 17
SURFACE_TYPES = [
    RoomType.GRASSLAND,
    RoomType.FOREST,
    RoomType.JUNGLE,
    RoomType.MOUNTAIN,
]


def _roomFactory():
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 0
    return RoomFactory(GRID_SIZE, MagicMock(), tickCounter)


def _forgetRoomType(room):
    # What a room reloaded from a save looks like: roomType is not persisted.
    room.setRoomType(None)
    return room


@pytest.mark.parametrize("roomType", SURFACE_TYPES)
def test_infers_every_generated_surface_room_type(roomType):
    factory = _roomFactory()
    for seed in range(40):
        random.seed(seed)
        room = _forgetRoomType(factory.createRoom(roomType, seed, 0))

        assert inferBiome(room) == roomType, "seed " + str(seed)


def test_infers_generated_cave_rooms():
    factory = _roomFactory()
    for depth in (1, 2, 3):
        random.seed(depth)
        room = _forgetRoomType(factory.createCaveRoom(0, 0, -depth))

        assert inferBiome(room) == RoomType.CAVE


@pytest.mark.parametrize("roomType", [RoomType.GRASSLAND, RoomType.FOREST])
def test_starting_home_does_not_change_the_inferred_biome(roomType):
    # The home's oak-log walls must not make a grassland look like a forest.
    factory = _roomFactory()
    for seed in range(20):
        random.seed(seed)
        room = factory.createRoom(roomType, 0, 0)
        StartingHomeGenerator().generate(room)
        _forgetRoomType(room)

        assert inferBiome(room) == roomType, "seed " + str(seed)


def test_empty_room_is_empty():
    room = _forgetRoomType(_roomFactory().createRoom(RoomType.EMPTY, 0, 0))

    assert inferBiome(room) == RoomType.EMPTY


def test_in_memory_room_type_wins_over_contents():
    random.seed(3)
    room = _roomFactory().createRoom(RoomType.GRASSLAND, 0, 0)
    room.setRoomType(RoomType.MOUNTAIN)

    assert inferBiome(room) == RoomType.MOUNTAIN


def test_negative_z_is_always_cave():
    assert inferBiomeFromClassNames(["Stone"], z=-1) == RoomType.CAVE


def test_class_name_rules():
    assert inferBiomeFromClassNames(["Grass", "Banana"]) == RoomType.JUNGLE
    assert inferBiomeFromClassNames(["Stone", "IronOre"]) == RoomType.MOUNTAIN
    assert inferBiomeFromClassNames(["Grass", "Stone"]) == RoomType.GRASSLAND
    assert inferBiomeFromClassNames(["Grass", "Leaves"]) == RoomType.FOREST
    assert inferBiomeFromClassNames(["Grass", "OakWood"]) == RoomType.FOREST
    assert (
        inferBiomeFromClassNames(["Grass", "OakWood", "WoodFloor"])
        == RoomType.GRASSLAND
    )
    assert inferBiomeFromClassNames([]) == RoomType.EMPTY
