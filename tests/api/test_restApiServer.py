import json
import threading
import urllib.error
import urllib.request
from unittest.mock import MagicMock

from api.restApiServer import RestApiServer
from player.player import Player
from world.tickCounter import TickCounter


class _FakeLocation:
    def __init__(self, x, y, entities):
        self._x = x
        self._y = y
        self._entities = entities

    def getX(self):
        return self._x

    def getY(self):
        return self._y

    def getEntities(self):
        return self._entities


class _FakeGrid:
    def __init__(self, locations, locationById=None):
        self._locations = locations
        self._locationById = locationById or {}

    def getLocations(self):
        return self._locations

    def getLocation(self, locationId):
        return self._locationById[locationId]


class FakeChicken:
    def __init__(self, name, locationId):
        self._name = name
        self._locationId = locationId

    def getName(self):
        return self._name

    def getLocationID(self):
        return self._locationId


def _makeRoom(x, y, z=0, roomType="grassland", numEntities=0, roomId="room-id"):
    room = MagicMock()
    room.getX.return_value = x
    room.getY.return_value = y
    room.getZ.return_value = z
    room.getRoomType.return_value = roomType
    room.getNumEntities.return_value = numEntities
    room.getID.return_value = roomId
    room.getGrid.return_value = _FakeGrid({})
    return room


def _makeMap(rooms):
    fakeMap = MagicMock()
    fakeMap._lock = threading.Lock()
    fakeMap.getRooms.return_value = rooms
    return fakeMap


def _createServer(resolve, override_dependency):
    player = MagicMock()
    player.getEnvironmentID.return_value = -1
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 42
    override_dependency(Player, player)
    override_dependency(TickCounter, tickCounter)
    server = resolve(RestApiServer)
    return server, player, tickCounter


def test_rest_disabled_by_default_does_not_start(
    resolve, override_dependency, test_config
):
    test_config.restEnabled = False
    server, _, _ = _createServer(resolve, override_dependency)

    server.start()

    assert server.isRunning() is False
    server.shutdown()  # no-op, must not raise


def test_get_rooms_returns_503_before_map_is_attached(
    resolve, override_dependency, test_config
):
    server, _, _ = _createServer(resolve, override_dependency)

    status, payload = server.getRooms()

    assert status == 503
    assert "error" in payload


def test_get_rooms_lists_loaded_rooms(resolve, override_dependency, test_config):
    server, _, _ = _createServer(resolve, override_dependency)
    room = _makeRoom(1, 2, roomType="forest", numEntities=3)
    server.setMap(_makeMap([room]))

    status, payload = server.getRooms()

    assert status == 200
    assert payload == [{"x": 1, "y": 2, "z": 0, "roomType": "forest", "numEntities": 3}]


def test_get_room_by_coordinates_not_found(resolve, override_dependency, test_config):
    server, _, _ = _createServer(resolve, override_dependency)
    server.setMap(_makeMap([_makeRoom(1, 2)]))

    status, payload = server.getRoomByCoordinates(9, 9)

    assert status == 404
    assert "error" in payload


def test_get_room_by_coordinates_cave_room(resolve, override_dependency, test_config):
    server, _, _ = _createServer(resolve, override_dependency)
    room = _makeRoom(0, 0, z=-1, roomType="cave", numEntities=0)
    server.setMap(_makeMap([room]))

    # z=0 should not find a cave room (z=-1)
    status, _ = server.getRoomByCoordinates(0, 0, z=0)
    assert status == 404

    # z=-1 should find it
    status, payload = server.getRoomByCoordinates(0, 0, z=-1)
    assert status == 200
    assert payload["z"] == -1
    assert payload["roomType"] == "cave"


def test_get_room_by_coordinates_returns_entities(
    resolve, override_dependency, test_config
):
    server, _, _ = _createServer(resolve, override_dependency)
    entity = FakeChicken("Chicken", "loc-1")
    room = _makeRoom(3, 4, roomType="grassland", numEntities=1)
    room.getGrid.return_value = _FakeGrid(
        {"loc-1": _FakeLocation(0, 0, {"e1": entity})}
    )
    server.setMap(_makeMap([room]))

    status, payload = server.getRoomByCoordinates(3, 4)

    assert status == 200
    assert payload["roomType"] == "grassland"
    assert payload["entities"] == [
        {
            "entityClass": "FakeChicken",
            "name": "Chicken",
            "locationId": "loc-1",
            "roomX": 3,
            "roomY": 4,
        }
    ]


def test_get_entities_flattens_across_rooms(resolve, override_dependency, test_config):
    server, _, _ = _createServer(resolve, override_dependency)
    entityA = FakeChicken("Chicken", "loc-a")
    entityB = FakeChicken("Rabbit", "loc-b")
    roomA = _makeRoom(0, 0)
    roomA.getGrid.return_value = _FakeGrid(
        {"loc-a": _FakeLocation(0, 0, {"a": entityA})}
    )
    roomB = _makeRoom(1, 0)
    roomB.getGrid.return_value = _FakeGrid(
        {"loc-b": _FakeLocation(1, 0, {"b": entityB})}
    )
    server.setMap(_makeMap([roomA, roomB]))

    status, payload = server.getEntities()

    assert status == 200
    names = sorted(entity["name"] for entity in payload)
    assert names == ["Chicken", "Rabbit"]


def test_get_player_status_503_when_player_not_placed(
    resolve, override_dependency, test_config
):
    server, player, _ = _createServer(resolve, override_dependency)
    server.setMap(_makeMap([]))
    player.getEnvironmentID.return_value = -1

    status, payload = server.getPlayerStatus()

    assert status == 503
    assert "error" in payload


def test_get_player_status_returns_player_state(
    resolve, override_dependency, test_config
):
    server, player, _ = _createServer(resolve, override_dependency)
    room = _makeRoom(5, 6, roomId="player-room")
    server.setMap(_makeMap([room]))
    player.getEnvironmentID.return_value = "player-room"
    player.getEnergy.return_value = 75
    player.getDirection.return_value = 2
    inventory = MagicMock()
    inventory.getNumItems.return_value = 4
    player.getInventory.return_value = inventory

    status, payload = server.getPlayerStatus()

    assert status == 200
    assert payload == {
        "energy": 75,
        "direction": 2,
        "inventoryItemCount": 4,
        "roomX": 5,
        "roomY": 6,
        "roomZ": 0,
    }


def test_get_world_status_returns_room_and_player_location(
    resolve, override_dependency, test_config
):
    server, player, tickCounter = _createServer(resolve, override_dependency)
    location = _FakeLocation(7, 8, {})
    room = _makeRoom(5, 6, roomType="cave", roomId="player-room")
    room.getGrid.return_value = _FakeGrid({}, locationById={"loc-1": location})
    server.setMap(_makeMap([room]))
    player.getEnvironmentID.return_value = "player-room"
    player.getLocationID.return_value = "loc-1"

    status, payload = server.getWorldStatus()

    assert status == 200
    assert payload == {
        "roomX": 5,
        "roomY": 6,
        "roomZ": 0,
        "roomType": "cave",
        "tickCount": 42,
        "playerLocation": {"x": 7, "y": 8},
    }


def test_start_disables_server_on_port_conflict(
    resolve, override_dependency, test_config
):
    import socket

    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    port = blocker.getsockname()[1]

    test_config.restEnabled = True
    test_config.restPort = port
    server, _, _ = _createServer(resolve, override_dependency)

    server.start()

    assert server.isRunning() is False
    server.shutdown()
    blocker.close()


def test_start_serves_endpoints_over_http(resolve, override_dependency, test_config):
    test_config.restEnabled = True
    test_config.restPort = 0
    server, _, _ = _createServer(resolve, override_dependency)
    room = _makeRoom(1, 1, roomType="mountain", numEntities=0)
    server.setMap(_makeMap([room]))

    server.start()
    try:
        assert server.isRunning() is True
        port = server._httpServer.server_address[1]

        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v1/rooms", timeout=5
        ) as response:
            body = json.loads(response.read())
        assert body == [
            {"x": 1, "y": 1, "z": 0, "roomType": "mountain", "numEntities": 0}
        ]

        # query strings must not break routing
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v1/rooms?foo=bar", timeout=5
        ) as response:
            body = json.loads(response.read())
        assert body == [
            {"x": 1, "y": 1, "z": 0, "roomType": "mountain", "numEntities": 0}
        ]

        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v1/rooms/9/9", timeout=5
        ) as response:
            pass
        raise AssertionError("expected HTTPError for a missing room")
    except urllib.error.HTTPError as error:
        assert error.code == 404
    finally:
        server.shutdown()

    assert server.isRunning() is False


def test_start_serves_cave_room_by_z_coordinate(
    resolve, override_dependency, test_config
):
    test_config.restEnabled = True
    test_config.restPort = 0
    server, _, _ = _createServer(resolve, override_dependency)
    surface_room = _makeRoom(0, 0, z=0, roomType="grassland")
    cave_room = _makeRoom(0, 0, z=-1, roomType="cave")
    server.setMap(_makeMap([surface_room, cave_room]))

    server.start()
    try:
        port = server._httpServer.server_address[1]

        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/v1/rooms/0/0/-1", timeout=5
        ) as response:
            body = json.loads(response.read())
        assert body["z"] == -1
        assert body["roomType"] == "cave"
    finally:
        server.shutdown()


def test_shutdown_without_start_is_a_noop(resolve, override_dependency, test_config):
    server, _, _ = _createServer(resolve, override_dependency)

    server.shutdown()  # must not raise
