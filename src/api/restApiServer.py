import json
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from player.player import Player
from world.tickCounter import TickCounter

_logger = getLogger(__name__)

_NOT_INITIALIZED = (503, {"error": "game world not yet initialized"})
_NOT_FOUND = (404, {"error": "room not found"})


def _findRoomContainingEntity(rooms, environmentId):
    for room in rooms:
        if room.getID() == environmentId:
            return room
    return None


def _findRoomByCoordinates(rooms, x, y):
    for room in rooms:
        if room.getX() == x and room.getY() == y and room.getZ() == 0:
            return room
    return None


def _serializeRoomSummary(room):
    return {
        "x": room.getX(),
        "y": room.getY(),
        "z": room.getZ(),
        "roomType": room.getRoomType(),
        "numEntities": room.getNumEntities(),
    }


def _serializeEntity(entity, room):
    return {
        "entityClass": entity.__class__.__name__,
        "name": entity.getName(),
        "locationId": str(entity.getLocationID()),
        "roomX": room.getX(),
        "roomY": room.getY(),
    }


def _collectEntities(room):
    entities = []
    for location in room.getGrid().getLocations().values():
        for entity in location.getEntities().values():
            entities.append(_serializeEntity(entity, room))
    return entities


# @author Daniel McCoy Stephenson
# @since August 2nd, 2026
#
# Embedded, opt-in, read-only HTTP API (issue #231) so external client tools
# (e.g. a world viewer) can query live game state without coupling to Roam's
# internals. Disabled unless config.restEnabled is true.
#
# `map` is handed in via setMap() rather than constructor-injected: Map is
# registered transient in bootstrap.py (a fresh instance per resolve), so this
# component must share WorldScreen's actual live Map object instead of
# resolving its own disconnected one.
@component
class RestApiServer:
    def __init__(self, player: Player, tickCounter: TickCounter, config: Config):
        self.player = player
        self.tickCounter = tickCounter
        self.config = config
        self.map = None
        self._httpServer = None
        self._executor = None

    def setMap(self, map):
        self.map = map

    def isRunning(self):
        return self._httpServer is not None

    def start(self):
        if not self.config.restEnabled:
            return
        if self._httpServer is not None:
            return
        try:
            httpServer = _RestApiHTTPServer(
                ("127.0.0.1", self.config.restPort), _RestApiRequestHandler
            )
        except OSError as error:
            _logger.warning(
                "rest api port unavailable; REST server disabled",
                restPort=self.config.restPort,
                error=str(error),
            )
            return
        httpServer.restApiServer = self
        self._httpServer = httpServer
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._executor.submit(self._httpServer.serve_forever)
        _logger.info("rest api server started", restPort=self.config.restPort)

    def shutdown(self):
        if self._httpServer is None:
            return
        self._httpServer.shutdown()
        self._httpServer.server_close()
        if self._executor is not None:
            self._executor.shutdown(wait=True)
        self._httpServer = None
        self._executor = None
        _logger.info("rest api server stopped")

    def getWorldStatus(self):
        if self.map is None:
            return _NOT_INITIALIZED
        with self.map._lock:
            rooms = list(self.map.getRooms())
        room = _findRoomContainingEntity(rooms, self.player.getEnvironmentID())
        if room is None:
            return _NOT_INITIALIZED
        location = room.getGrid().getLocation(self.player.getLocationID())
        return 200, {
            "roomX": room.getX(),
            "roomY": room.getY(),
            "roomZ": room.getZ(),
            "roomType": room.getRoomType(),
            "tickCount": self.tickCounter.getTick(),
            "playerLocation": {"x": location.getX(), "y": location.getY()},
        }

    def getRooms(self):
        if self.map is None:
            return _NOT_INITIALIZED
        with self.map._lock:
            rooms = list(self.map.getRooms())
        return 200, [_serializeRoomSummary(room) for room in rooms]

    def getRoomByCoordinates(self, x, y):
        if self.map is None:
            return _NOT_INITIALIZED
        with self.map._lock:
            rooms = list(self.map.getRooms())
        room = _findRoomByCoordinates(rooms, x, y)
        if room is None:
            return _NOT_FOUND
        return 200, {
            "x": room.getX(),
            "y": room.getY(),
            "z": room.getZ(),
            "roomType": room.getRoomType(),
            "entities": _collectEntities(room),
        }

    def getPlayerStatus(self):
        if self.map is None or self.player.getEnvironmentID() == -1:
            return _NOT_INITIALIZED
        with self.map._lock:
            rooms = list(self.map.getRooms())
        room = _findRoomContainingEntity(rooms, self.player.getEnvironmentID())
        if room is None:
            return _NOT_INITIALIZED
        return 200, {
            "energy": self.player.getEnergy(),
            "direction": self.player.getDirection(),
            "inventoryItemCount": self.player.getInventory().getNumItems(),
            "roomX": room.getX(),
            "roomY": room.getY(),
            "roomZ": room.getZ(),
        }

    def getEntities(self):
        if self.map is None:
            return _NOT_INITIALIZED
        with self.map._lock:
            rooms = list(self.map.getRooms())
        entities = []
        for room in rooms:
            entities.extend(_collectEntities(room))
        return 200, entities


class _RestApiHTTPServer(HTTPServer):
    allow_reuse_address = True


class _RestApiRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        _logger.debug("rest api request", message=format % args)

    def _writeJson(self, statusCode, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(statusCode)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        restApiServer = self.server.restApiServer
        parts = [segment for segment in self.path.split("/") if segment]
        try:
            if parts == ["api", "v1", "world"]:
                self._writeJson(*restApiServer.getWorldStatus())
            elif parts == ["api", "v1", "rooms"]:
                self._writeJson(*restApiServer.getRooms())
            elif len(parts) == 5 and parts[:3] == ["api", "v1", "rooms"]:
                try:
                    x, y = int(parts[3]), int(parts[4])
                except ValueError:
                    self._writeJson(*_NOT_FOUND)
                else:
                    self._writeJson(*restApiServer.getRoomByCoordinates(x, y))
            elif parts == ["api", "v1", "player"]:
                self._writeJson(*restApiServer.getPlayerStatus())
            elif parts == ["api", "v1", "entities"]:
                self._writeJson(*restApiServer.getEntities())
            else:
                self._writeJson(404, {"error": "not found"})
        except Exception:
            _logger.exception("rest api request failed", path=self.path)
            self._writeJson(500, {"error": "internal server error"})
