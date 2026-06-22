from unittest.mock import MagicMock

from entity.bed import Bed
from entity.chest import Chest
from entity.oakWood import OakWood
from entity.torch import Torch
from entity.woodFloor import WoodFloor
from src.player.player import Player
from src.world.room import Room
from src.world.startingHomeGenerator import StartingHomeGenerator


def createRoom(gridSize=17):
    return Room("TestRoom", gridSize, (0, 0, 0), 0, 0, MagicMock())


def entitiesAt(room, x, y):
    location = room.getGrid().getLocationByCoordinates(x, y)
    return list(location.getEntities().values())


def hasEntityType(room, x, y, entityType):
    return any(isinstance(e, entityType) for e in entitiesAt(room, x, y))


def test_generate_returns_center_location():
    room = createRoom(17)
    generator = StartingHomeGenerator()

    spawn = generator.generate(room)

    assert spawn != -1
    assert spawn.getX() == 8
    assert spawn.getY() == 8


def test_walls_are_oak_wood_on_the_border():
    room = createRoom(17)
    StartingHomeGenerator().generate(room)

    # Corners of the 7x7 home (centered on 8,8 -> spans 5..11).
    assert hasEntityType(room, 5, 5, OakWood)
    assert hasEntityType(room, 11, 5, OakWood)
    assert hasEntityType(room, 5, 11, OakWood)
    assert hasEntityType(room, 11, 11, OakWood)


def test_interior_has_wood_floor():
    room = createRoom(17)
    StartingHomeGenerator().generate(room)

    assert hasEntityType(room, 8, 8, WoodFloor)
    assert hasEntityType(room, 6, 6, WoodFloor)


def test_doorway_is_floor_not_wall():
    room = createRoom(17)
    StartingHomeGenerator().generate(room)

    # Bottom-center wall tile is left open as a doorway.
    assert hasEntityType(room, 8, 11, WoodFloor)
    assert not hasEntityType(room, 8, 11, OakWood)


def test_bed_and_chest_are_placed():
    room = createRoom(17)
    StartingHomeGenerator().generate(room)

    assert hasEntityType(room, 6, 6, Bed)
    assert hasEntityType(room, 10, 6, Chest)


def test_torch_is_placed_on_a_free_interior_corner():
    room = createRoom(17)
    StartingHomeGenerator().generate(room)

    # Bottom-left interior corner; distinct from the bed/chest top corners.
    assert hasEntityType(room, 6, 10, Torch)
    assert not hasEntityType(room, 6, 10, Bed)
    assert not hasEntityType(room, 6, 10, Chest)


def test_small_room_skips_building():
    room = createRoom(3)
    generator = StartingHomeGenerator()

    spawn = generator.generate(room)

    # Nothing built, but a valid center spawn is still returned.
    assert spawn != -1
    assert room.getGrid().getNumEntities() == 0


def test_grant_starting_items_adds_food():
    player = Player(0)
    generator = StartingHomeGenerator()

    generator.grantStartingItems(player)

    inventory = player.getInventory()
    assert inventory.getNumItems() == 8
