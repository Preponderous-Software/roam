from lib.graphik.src.graphik import Graphik
from world.map import Map
from world.room import Room


def createMap(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.gridSize = 3
    return resolve(Map)


def test_initialization(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    assert mapInstance.getRooms() == []
    assert mapInstance.gridSize == 3


def test_get_rooms_empty(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    assert mapInstance.getRooms() == []
    assert len(mapInstance.getRooms()) == 0


def test_generate_new_room(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    room = mapInstance.generateNewRoom(0, 0)

    assert type(room).__name__ == "Room"
    assert room.getX() == 0
    assert room.getY() == 0
    assert len(mapInstance.getRooms()) == 1


def test_generate_multiple_rooms(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    room1 = mapInstance.generateNewRoom(0, 0)
    room2 = mapInstance.generateNewRoom(1, 0)
    room3 = mapInstance.generateNewRoom(0, 1)

    assert len(mapInstance.getRooms()) == 3
    assert room1.getX() == 0
    assert room2.getX() == 1
    assert room3.getY() == 1


def test_get_room_existing(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)
    room = mapInstance.generateNewRoom(5, 5)

    result = mapInstance.getRoom(5, 5)

    assert result == room


def test_get_room_not_existing(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    result = mapInstance.getRoom(99, 99)

    assert result == -1


def test_add_room(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)
    graphik = resolve(Graphik)
    room = Room("TestRoom", 3, (0, 0, 0), 2, 3, graphik)

    mapInstance.addRoom(room)

    assert len(mapInstance.getRooms()) == 1
    assert mapInstance.getRoom(2, 3) == room


def test_add_room_duplicate_coordinates(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)
    graphik = resolve(Graphik)
    room1 = Room("Room1", 3, (0, 0, 0), 2, 3, graphik)
    room2 = Room("Room2", 3, (0, 0, 0), 2, 3, graphik)

    mapInstance.addRoom(room1)
    result = mapInstance.addRoom(room2)

    # should be a no-op when the key exists — returns the existing room
    assert len(mapInstance.getRooms()) == 1
    assert mapInstance.getRoom(2, 3) == room1
    assert result == room1


def test_get_location_of_entity(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)
    room = mapInstance.generateNewRoom(0, 0)

    from entity.apple import Apple

    entity = Apple()
    room.addEntity(entity)

    location = mapInstance.getLocationOfEntity(entity, room)

    assert location is not None


def test_consume_is_new_room_true_for_generated(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    mapInstance.generateNewRoom(1, 2)

    # First call returns True — room was freshly generated
    assert mapInstance.consumeIsNewRoom(1, 2) is True


def test_consume_is_new_room_false_after_consumed(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    mapInstance.generateNewRoom(1, 2)
    mapInstance.consumeIsNewRoom(1, 2)

    # Second call returns False — flag was already consumed
    assert mapInstance.consumeIsNewRoom(1, 2) is False


def test_consume_is_new_room_false_for_added_room(resolve, test_config, tmp_path):
    mapInstance = createMap(resolve, test_config, tmp_path)

    graphik = resolve(Graphik)
    room = Room("Loaded", 3, (0, 0, 0), 3, 4, graphik)
    mapInstance.addRoom(room)

    # Rooms loaded via addRoom (e.g. from disk) are NOT flagged as freshly generated
    assert mapInstance.consumeIsNewRoom(3, 4) is False


def test_consume_is_new_room_false_for_duplicate_generate(
    resolve, test_config, tmp_path
):
    mapInstance = createMap(resolve, test_config, tmp_path)

    mapInstance.generateNewRoom(0, 0)
    # Calling generateNewRoom a second time returns the cached room without
    # adding to _freshlyGeneratedRooms a second time
    mapInstance.generateNewRoom(0, 0)
    mapInstance.consumeIsNewRoom(0, 0)

    # After consuming once, flag is gone
    assert mapInstance.consumeIsNewRoom(0, 0) is False
