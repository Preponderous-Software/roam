from unittest.mock import MagicMock

from src.world.roomFactory import RoomFactory
from src.world.roomType import RoomType
from world.room import Room


def createRoomFactory():
    graphik = MagicMock()
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 0
    return RoomFactory(3, graphik, tickCounter)


def test_initialization():
    factory = createRoomFactory()

    assert factory.gridSize == 3
    assert factory.lastRoomTypeCreated == RoomType.GRASSLAND


def test_create_empty_room():
    factory = createRoomFactory()

    room = factory.createRoom(RoomType.EMPTY, 0, 0)

    assert isinstance(room, Room)
    assert room.getX() == 0
    assert room.getY() == 0
    assert factory.lastRoomTypeCreated == RoomType.EMPTY


def test_create_grassland_room():
    factory = createRoomFactory()

    room = factory.createRoom(RoomType.GRASSLAND, 1, 2)

    assert isinstance(room, Room)
    assert room.getX() == 1
    assert room.getY() == 2
    assert factory.lastRoomTypeCreated == RoomType.GRASSLAND


def test_create_forest_room():
    factory = createRoomFactory()

    room = factory.createRoom(RoomType.FOREST, 3, 4)

    assert isinstance(room, Room)
    assert room.getX() == 3
    assert room.getY() == 4
    assert factory.lastRoomTypeCreated == RoomType.FOREST


def test_create_jungle_room():
    factory = createRoomFactory()

    room = factory.createRoom(RoomType.JUNGLE, 5, 6)

    assert isinstance(room, Room)
    assert room.getX() == 5
    assert room.getY() == 6
    assert factory.lastRoomTypeCreated == RoomType.JUNGLE


def test_create_mountain_room():
    factory = createRoomFactory()

    room = factory.createRoom(RoomType.MOUNTAIN, 7, 8)

    assert isinstance(room, Room)
    assert room.getX() == 7
    assert room.getY() == 8
    assert factory.lastRoomTypeCreated == RoomType.MOUNTAIN


def test_create_random_room():
    factory = createRoomFactory()

    room = factory.createRandomRoom(0, 0)

    assert isinstance(room, Room)
    assert room.getX() == 0
    assert room.getY() == 0


def test_create_empty_room_color():
    factory = createRoomFactory()

    room = factory.createEmptyRoom((255, 0, 0), 0, 0)

    assert room.getBackgroundColor() == (255, 0, 0)


def test_create_room_name():
    factory = createRoomFactory()

    room = factory.createRoom(RoomType.EMPTY, 5, 10)

    assert room.getName() == "(5, 10)"


def test_spawn_grass():
    factory = createRoomFactory()
    room = factory.createEmptyRoom((0, 0, 0), 0, 0)

    factory.spawnGrass(room)

    assert room.getNumEntities() > 0


def test_fill_with_rocks():
    factory = createRoomFactory()
    room = factory.createEmptyRoom((0, 0, 0), 0, 0)

    factory.fillWithRocks(room)

    # each location should have at least one entity (stone)
    assert room.getNumEntities() >= room.getGrid().getSize()


def test_last_room_type_updated():
    factory = createRoomFactory()

    factory.createRoom(RoomType.MOUNTAIN, 0, 0)
    assert factory.lastRoomTypeCreated == RoomType.MOUNTAIN

    factory.createRoom(RoomType.FOREST, 1, 1)
    assert factory.lastRoomTypeCreated == RoomType.FOREST

    factory.createRoom(RoomType.JUNGLE, 2, 2)
    assert factory.lastRoomTypeCreated == RoomType.JUNGLE

    factory.createRoom(RoomType.GRASSLAND, 3, 3)
    assert factory.lastRoomTypeCreated == RoomType.GRASSLAND


def test_create_grass_room_has_entities():
    factory = createRoomFactory()

    room = factory.createGrassRoom(0, 0)

    # grass rooms should have grass spawned
    assert room.getNumEntities() > 0


def test_create_mountain_room_has_entities():
    factory = createRoomFactory()

    room = factory.createMountainRoom(0, 0)

    # mountain rooms should have rocks filling the grid
    assert room.getNumEntities() > 0
