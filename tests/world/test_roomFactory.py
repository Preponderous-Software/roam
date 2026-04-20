import random

from world.roomFactory import RoomFactory
from world.roomType import RoomType


def createRoomFactory(resolve, test_config):
    test_config.gridSize = 3
    return resolve(RoomFactory)


def test_initialization(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    assert factory.gridSize == 3
    assert factory.lastRoomTypeCreated == RoomType.GRASSLAND


def test_create_empty_room(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createRoom(RoomType.EMPTY, 0, 0)

    assert type(room).__name__ == "Room"
    assert room.getX() == 0
    assert room.getY() == 0
    assert factory.lastRoomTypeCreated == RoomType.EMPTY


def test_create_grassland_room(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createRoom(RoomType.GRASSLAND, 1, 2)

    assert type(room).__name__ == "Room"
    assert room.getX() == 1
    assert room.getY() == 2
    assert factory.lastRoomTypeCreated == RoomType.GRASSLAND


def test_create_forest_room(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createRoom(RoomType.FOREST, 3, 4)

    assert type(room).__name__ == "Room"
    assert room.getX() == 3
    assert room.getY() == 4
    assert factory.lastRoomTypeCreated == RoomType.FOREST


def test_create_jungle_room(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createRoom(RoomType.JUNGLE, 5, 6)

    assert type(room).__name__ == "Room"
    assert room.getX() == 5
    assert room.getY() == 6
    assert factory.lastRoomTypeCreated == RoomType.JUNGLE


def test_create_mountain_room(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createRoom(RoomType.MOUNTAIN, 7, 8)

    assert type(room).__name__ == "Room"
    assert room.getX() == 7
    assert room.getY() == 8
    assert factory.lastRoomTypeCreated == RoomType.MOUNTAIN


def test_create_random_room(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createRandomRoom(0, 0)

    assert type(room).__name__ == "Room"
    assert room.getX() == 0
    assert room.getY() == 0


def test_create_empty_room_color(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createEmptyRoom((255, 0, 0), 0, 0)

    assert room.getBackgroundColor() == (255, 0, 0)


def test_create_room_name(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createRoom(RoomType.EMPTY, 5, 10)

    assert room.getName() == "(5, 10)"


def test_spawn_grass(resolve, test_config):
    random.seed(42)
    factory = createRoomFactory(resolve, test_config)
    room = factory.createEmptyRoom((0, 0, 0), 0, 0)

    factory.spawnGrass(room)

    assert room.getNumEntities() > 0


def test_fill_with_rocks(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)
    room = factory.createEmptyRoom((0, 0, 0), 0, 0)

    factory.fillWithRocks(room)

    # each location should have at least one entity (stone)
    assert room.getNumEntities() >= room.getGrid().getSize()


def test_last_room_type_updated(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    factory.createRoom(RoomType.MOUNTAIN, 0, 0)
    assert factory.lastRoomTypeCreated == RoomType.MOUNTAIN

    factory.createRoom(RoomType.FOREST, 1, 1)
    assert factory.lastRoomTypeCreated == RoomType.FOREST

    factory.createRoom(RoomType.JUNGLE, 2, 2)
    assert factory.lastRoomTypeCreated == RoomType.JUNGLE

    factory.createRoom(RoomType.GRASSLAND, 3, 3)
    assert factory.lastRoomTypeCreated == RoomType.GRASSLAND


def test_create_grass_room_has_entities(resolve, test_config):
    random.seed(42)
    factory = createRoomFactory(resolve, test_config)

    room = factory.createGrassRoom(0, 0)

    # grass rooms should have grass spawned
    assert room.getNumEntities() > 0


def test_create_mountain_room_has_entities(resolve, test_config):
    factory = createRoomFactory(resolve, test_config)

    room = factory.createMountainRoom(0, 0)

    # mountain rooms should have rocks filling the grid
    assert room.getNumEntities() > 0
