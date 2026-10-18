import json
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from api.spectatorFiles import resolveStaticFile
from api.worldSnapshot import (
    DEFAULT_RADIUS,
    clampRadius,
    worldViewToSnapshot,
)
from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from player.player import Player
from rendering.worldViewSink import WorldViewSink
from world.tickCounter import TickCounter

_logger = getLogger(__name__)

_NOT_INITIALIZED = (503, {"error": "game world not yet initialized"})
_NOT_FOUND = (404, {"error": "room not found"})
_NO_VIEW_YET = (503, {"error": "no world view published yet; retry shortly"})
_BAD_RADIUS = (400, {"error": "radius must be an integer"})


def _findRoomContainingEntity(rooms, environmentId):
    for room in rooms:
        if room.getID() == environmentId:
            return room
    return None


def _findRoomByCoordinates(rooms, x, y, z=0):
    for room in rooms:
        if room.getX() == x and room.getY() == y and room.getZ() == z:
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
# Endpoints (all GET, JSON, bound to 127.0.0.1 only):
#   /api/v1/world, /api/v1/rooms, /api/v1/rooms/{x}/{y}[/{z}], /api/v1/player,
#   /api/v1/entities
#   /api/v1/snapshot?radius=R  world-shaped snapshot of the loaded rooms within
#       R rooms (default 1, max 3) of the player's room, on every level: each
#       tile's entity stack, background colours, light sources and the
#       player's tile and facing. For 3D viewers (RFC 0017); see
#       api/worldSnapshot.py.
#   /spectator/  a three.js page that renders /api/v1/snapshot in 3D, plus
#       /assets/images/{name}.png for its sprites (see api/spectatorFiles.py)
#
# `map` is handed in via setMap() rather than constructor-injected: Map is
# registered transient in bootstrap.py (a fresh instance per resolve), so this
# component must share WorldScreen's actual live Map object instead of
# resolving its own disconnected one.
@component
class RestApiServer:
    def __init__(
        self,
        player: Player,
        tickCounter: TickCounter,
        config: Config,
    ):
        self.player = player
        self.tickCounter = tickCounter
        self.config = config
        self.map = None
        self._httpServer = None
        self._executor = None
        self._worldViewSink = _RestWorldViewSink(self)

    def getWorldViewSink(self):
        return self._worldViewSink

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
        self._worldViewSink.clear()
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

    def getRoomByCoordinates(self, x, y, z=0):
        if self.map is None:
            return _NOT_INITIALIZED
        with self.map._lock:
            rooms = list(self.map.getRooms())
            room = _findRoomByCoordinates(rooms, x, y, z)
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

    def getSnapshot(self, radius=DEFAULT_RADIUS):
        # RFC 0017: serves the most recent WorldView the game thread
        # published to this server's sink (an atomic reference swap), so this
        # HTTP thread never iterates live room grids. The request also tells
        # the sink a spectator is watching, which is what makes the game
        # thread build views at all (see _RestWorldViewSink).
        radius = clampRadius(radius)
        self._worldViewSink.noteRequest(radius)
        worldView = self._worldViewSink.getLatest()
        if worldView is None:
            return _NO_VIEW_YET
        viewRadius = worldView.getCameraHint().getVisibleRadiusRooms()
        return 200, worldViewToSnapshot(worldView, min(radius, viewRadius))


# The REST server's WorldViewSink. Building a view costs the game thread
# O(tiles in view) (CHANGELOG.md, 2026-10-18 timing), so instead of wanting one
# every tick whenever restEnabled is true, it wants one only while a spectator
# is polling /api/v1/snapshot (a request in the last WATCH_SECONDS), at most
# once per MIN_PUBLISH_SECONDS, and only as wide as the radius last asked for.
# With no spectator the game pays one boolean check per tick, as the 2D
# frontends do.
class _RestWorldViewSink(WorldViewSink):
    WATCH_SECONDS = 5.0
    MIN_PUBLISH_SECONDS = 0.25

    def __init__(self, restApiServer):
        self._restApiServer = restApiServer
        self._latest = None
        self._lastRequestTime = None
        self._lastPublishTime = None
        self._requestedRadius = DEFAULT_RADIUS

    def noteRequest(self, radius):
        self._requestedRadius = radius
        self._lastRequestTime = time.monotonic()

    def wantsWorldView(self):
        if self._lastRequestTime is None or not self._restApiServer.isRunning():
            return False
        now = time.monotonic()
        if now - self._lastRequestTime > self.WATCH_SECONDS:
            return False
        return (
            self._lastPublishTime is None
            or now - self._lastPublishTime >= self.MIN_PUBLISH_SECONDS
            or self._latest is None
            or self._latest.getCameraHint().getVisibleRadiusRooms()
            < self._requestedRadius
        )

    def getWantedRadiusRooms(self):
        return self._requestedRadius

    def publish(self, worldView):
        self._latest = worldView
        self._lastPublishTime = time.monotonic()

    def getLatest(self):
        return self._latest

    def clear(self):
        self._latest = None
        self._lastRequestTime = None
        self._lastPublishTime = None


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

    def _writeFile(self, path, contentType):
        with open(path, "rb") as staticFile:
            body = staticFile.read()
        self.send_response(200)
        self.send_header("Content-Type", contentType)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        restApiServer = self.server.restApiServer
        parsedUrl = urlparse(self.path)
        path = parsedUrl.path
        parts = [segment for segment in path.split("/") if segment]
        try:
            if parts == ["api", "v1", "world"]:
                self._writeJson(*restApiServer.getWorldStatus())
            elif parts == ["api", "v1", "rooms"]:
                self._writeJson(*restApiServer.getRooms())
            elif len(parts) in (5, 6) and parts[:3] == ["api", "v1", "rooms"]:
                try:
                    x, y = int(parts[3]), int(parts[4])
                    z = int(parts[5]) if len(parts) == 6 else 0
                except ValueError:
                    self._writeJson(*_NOT_FOUND)
                else:
                    self._writeJson(*restApiServer.getRoomByCoordinates(x, y, z))
            elif parts == ["api", "v1", "player"]:
                self._writeJson(*restApiServer.getPlayerStatus())
            elif parts == ["api", "v1", "entities"]:
                self._writeJson(*restApiServer.getEntities())
            elif parts == ["api", "v1", "snapshot"]:
                radiusValues = parse_qs(parsedUrl.query).get("radius")
                try:
                    radius = int(radiusValues[0]) if radiusValues else DEFAULT_RADIUS
                except ValueError:
                    self._writeJson(*_BAD_RADIUS)
                else:
                    self._writeJson(*restApiServer.getSnapshot(radius))
            else:
                staticFile = resolveStaticFile(parts)
                if staticFile is None:
                    self._writeJson(404, {"error": "not found"})
                else:
                    self._writeFile(*staticFile)
        except Exception:
            _logger.exception("rest api request failed", path=self.path)
            self._writeJson(500, {"error": "internal server error"})
