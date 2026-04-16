from unittest.mock import MagicMock

from src.world.map import Map
from src.world.room import Room


def createMap(tmp_path):
    graphik = MagicMock()
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 0
    config = MagicMock()
    config.pathToSaveDirectory = str(tmp_path)
    return Map(3, graphik, tickCounter, config)


def test_initialization(tmp_path):
    mapInstance = createMap(tmp_path)

    assert mapInstance.getRooms() == []
    assert mapInstance.gridSize == 3


def test_get_rooms_empty(tmp_path):
    mapInstance = createMap(tmp_path)

    assert mapInstance.getRooms() == []
    assert len(mapInstance.getRooms()) == 0


def test_generate_new_room(tmp_path):
    mapInstance = createMap(tmp_path)

    room = mapInstance.generateNewRoom(0, 0)

    assert type(room).__name__ == "Room"
    assert room.getX() == 0
    assert room.getY() == 0
    assert len(mapInstance.getRooms()) == 1


def test_generate_multiple_rooms(tmp_path):
    mapInstance = createMap(tmp_path)

    room1 = mapInstance.generateNewRoom(0, 0)
    room2 = mapInstance.generateNewRoom(1, 0)
    room3 = mapInstance.generateNewRoom(0, 1)

    assert len(mapInstance.getRooms()) == 3
    assert room1.getX() == 0
    assert room2.getX() == 1
    assert room3.getY() == 1


def test_get_room_existing(tmp_path):
    mapInstance = createMap(tmp_path)
    room = mapInstance.generateNewRoom(5, 5)

    result = mapInstance.getRoom(5, 5)

    assert result == room


def test_get_room_not_existing(tmp_path):
    mapInstance = createMap(tmp_path)

    result = mapInstance.getRoom(99, 99)

    assert result == -1


def test_add_room(tmp_path):
    mapInstance = createMap(tmp_path)
    graphik = MagicMock()
    room = Room("TestRoom", 3, (0, 0, 0), 2, 3, graphik)

    mapInstance.addRoom(room)

    assert len(mapInstance.getRooms()) == 1
    assert mapInstance.getRoom(2, 3) == room


def test_add_room_duplicate_coordinates(tmp_path):
    mapInstance = createMap(tmp_path)
    graphik = MagicMock()
    room1 = Room("Room1", 3, (0, 0, 0), 2, 3, graphik)
    room2 = Room("Room2", 3, (0, 0, 0), 2, 3, graphik)

    mapInstance.addRoom(room1)
    mapInstance.addRoom(room2)

    # should update the index but not duplicate in the list
    assert len(mapInstance.getRooms()) == 1
    assert mapInstance.getRoom(2, 3) == room2


def test_get_location_of_entity(tmp_path):
    mapInstance = createMap(tmp_path)
    room = mapInstance.generateNewRoom(0, 0)

    from src.entity.apple import Apple

    entity = Apple()
    room.addEntity(entity)

    location = mapInstance.getLocationOfEntity(entity, room)

    assert location is not None
