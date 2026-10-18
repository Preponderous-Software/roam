from unittest.mock import MagicMock

from entity.campfire import Campfire
from entity.goldenLantern import GoldenLantern
from entity.grass import Grass
from entity.torch import Torch
from world.lightSources import collectLightSources
from world.room import Room


def _room():
    return Room("test", 5, (10, 20, 30), 0, 0, MagicMock())


def _put(room, entity, x, y):
    room.addEntityToLocation(entity, room.getGrid().getLocationByCoordinates(x, y))


def test_room_without_lights_has_none():
    room = _room()
    _put(room, Grass(), 1, 1)

    assert collectLightSources(room) == []


def test_collects_every_light_in_tile_coordinates():
    room = _room()
    _put(room, Grass(), 0, 0)
    _put(room, Torch(), 0, 0)
    _put(room, Campfire(), 3, 1)
    _put(room, GoldenLantern(), 4, 4)

    assert sorted(collectLightSources(room)) == [
        (0, 0, 6, "Torch"),
        (3, 1, 8, "Campfire"),
        (4, 4, 10, "GoldenLantern"),
    ]
