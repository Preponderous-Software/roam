from world.biomeInference import inferBiomeFromClassNames
from world.lightSources import collectLightSources

# The world-shaped, read-only snapshot served at GET /api/v1/snapshot (RFC 0017
# stage 1). A 3D viewer can place every entity on its tile from it, which the
# other REST endpoints cannot do: they carry no tile x/y, background colour or
# light radius.
#
# Built from rooms that are ALREADY LOADED only. Nothing here may call
# Map.getRoom (it loads rooms from disk), Map.generateNewRoom, RoomFactory or
# WorldScreen.getOrLoadRoom: loading or generating a room is a side effect that
# later reaches the save directory. tests/api/test_snapshotSaveSafety.py
# enforces this.

SNAPSHOT_FORMAT = "roam-world-snapshot"
SNAPSHOT_VERSION = 1
DEFAULT_RADIUS = 1
MAX_RADIUS = 3

_DIRECTION_NAMES = {0: "up", 1: "left", 2: "down", 3: "right"}


def clampRadius(radius):
    return max(0, min(MAX_RADIUS, int(radius)))


def directionName(player):
    """The way the player faces: their current direction while moving, else
    the last direction they moved in, else "down" (the spawn sprite)."""
    direction = player.getDirection()
    if direction not in _DIRECTION_NAMES:
        direction = player.getLastDirection()
    return _DIRECTION_NAMES.get(direction, "down")


def _findPlayerRoom(rooms, player):
    environmentId = player.getEnvironmentID()
    for room in rooms:
        if room.getID() == environmentId:
            return room
    return None


class _ClassTable:
    def __init__(self):
        self.names = []
        self.images = []
        self._indexByName = {}

    def indexOf(self, entity):
        name = entity.__class__.__name__
        index = self._indexByName.get(name)
        if index is None:
            index = len(self.names)
            self._indexByName[name] = index
            self.names.append(name)
            getImagePath = getattr(entity, "getImagePath", None)
            self.images.append(getImagePath() if getImagePath else None)
        return index


def _serializeRoom(room, player, gridSize, classTable):
    tiles = [[] for _ in range(gridSize * gridSize)]
    classNames = []
    for location in list(room.getGrid().getLocations().values()):
        x, y = location.getX(), location.getY()
        if not (0 <= x < gridSize and 0 <= y < gridSize):
            continue
        stack = tiles[y * gridSize + x]
        # Bottom to top, in the order the location holds them (the top entity
        # is the one the 2D view draws).
        for entity in list(location.getEntities().values()):
            if entity is player:
                continue
            stack.append(classTable.indexOf(entity))
            classNames.append(entity.__class__.__name__)
    roomType = room.getRoomType()
    biome = (
        roomType
        if roomType is not None
        else inferBiomeFromClassNames(classNames, room.getZ())
    )
    return {
        "x": room.getX(),
        "y": room.getY(),
        "z": room.getZ(),
        "roomType": roomType,
        "biome": biome,
        "backgroundColor": [int(c) for c in room.getBackgroundColor()],
        "tiles": tiles,
    }


def buildWorldSnapshot(rooms, player, tick, dayNightCycle, config, radius):
    """Return the snapshot dict, or None when the player is not in any of the
    given (loaded) rooms yet.

    rooms is the list of loaded rooms; radius (already clamped) is how many
    rooms around the player's room, on every level, are included.
    """
    playerRoom = _findPlayerRoom(rooms, player)
    if playerRoom is None:
        return None
    playerLocation = playerRoom.getGrid().getLocation(player.getLocationID())
    gridSize = playerRoom.getGrid().getColumns()
    playerRoomX, playerRoomY = playerRoom.getX(), playerRoom.getY()

    classTable = _ClassTable()
    roomsJson = []
    lights = []
    for room in rooms:
        if (
            abs(room.getX() - playerRoomX) > radius
            or abs(room.getY() - playerRoomY) > radius
        ):
            continue
        roomsJson.append(_serializeRoom(room, player, gridSize, classTable))
        roomKey = [room.getX(), room.getY(), room.getZ()]
        for tileX, tileY, radiusTiles, entityClass in collectLightSources(room):
            lights.append(
                {
                    "room": roomKey,
                    "x": tileX,
                    "y": tileY,
                    "radiusTiles": radiusTiles,
                    "entityClass": entityClass,
                }
            )

    dayNightEnabled = config.dayNightCycleEnabled
    return {
        "format": SNAPSHOT_FORMAT,
        "version": SNAPSHOT_VERSION,
        "tick": tick,
        "gridSize": gridSize,
        "radius": radius,
        "dayNight": {
            "enabled": dayNightEnabled,
            "cycleLengthTicks": config.dayNightCycleLengthTicks,
            "overlayOpacity": (
                dayNightCycle.getOverlayOpacity(tick) if dayNightEnabled else 0
            ),
            "phase": dayNightCycle.getPhase(tick),
        },
        "player": {
            "room": [playerRoomX, playerRoomY, playerRoom.getZ()],
            "x": playerLocation.getX(),
            "y": playerLocation.getY(),
            "direction": directionName(player),
        },
        "classes": classTable.names,
        "classImages": classTable.images,
        "rooms": roomsJson,
        "lights": lights,
    }
