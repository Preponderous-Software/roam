# The world-shaped, read-only snapshot served at GET /api/v1/snapshot (RFC 0017
# stage 1). A 3D viewer can place every entity on its tile from it, which the
# other REST endpoints cannot do: they carry no tile x/y, background colour or
# light radius.
#
# Since stage 2 it is a JSON rendering of the most recent WorldView the game
# thread published (rendering/worldView.py), so the HTTP thread never iterates
# live room grids. WorldViewBuilder only reads rooms that are already loaded;
# see tests/api/test_snapshotSaveSafety.py.

SNAPSHOT_FORMAT = "roam-world-snapshot"
SNAPSHOT_VERSION = 1
DEFAULT_RADIUS = 1
MAX_RADIUS = 3


def clampRadius(radius):
    return max(0, min(MAX_RADIUS, int(radius)))


def worldViewToSnapshot(worldView, radius):
    """Return the snapshot dict for the rooms of worldView within radius
    (already clamped) rooms of the player's room, on every level."""
    player = worldView.getPlayer()
    playerRoomX, playerRoomY, _ = player.getRoom()

    def isNear(roomKey):
        return (
            abs(roomKey[0] - playerRoomX) <= radius
            and abs(roomKey[1] - playerRoomY) <= radius
        )

    images = dict(worldView.getClassImages())
    classes = []
    classIndex = {}

    def indexOf(name):
        index = classIndex.get(name)
        if index is None:
            index = classIndex[name] = len(classes)
            classes.append(name)
        return index

    rooms = []
    for roomView in worldView.getRooms():
        if not isNear(roomView.getKey()):
            continue
        rooms.append(
            {
                "x": roomView.getX(),
                "y": roomView.getY(),
                "z": roomView.getZ(),
                "roomType": roomView.getRoomType(),
                "biome": roomView.getBiome(),
                "backgroundColor": [int(c) for c in roomView.getBackgroundColor()],
                "tiles": [
                    [indexOf(name) for name in stack] for stack in roomView.getTiles()
                ],
            }
        )
    lights = [
        {
            "room": list(light.getRoom()),
            "x": light.getTileX(),
            "y": light.getTileY(),
            "radiusTiles": light.getRadiusTiles(),
            "entityClass": light.getEntityClass(),
        }
        for light in worldView.getLights()
        if isNear(light.getRoom())
    ]
    return {
        "format": SNAPSHOT_FORMAT,
        "version": SNAPSHOT_VERSION,
        "tick": worldView.getTick(),
        "gridSize": worldView.getGridSize(),
        "radius": radius,
        "dayNight": {
            "enabled": worldView.isDayNightEnabled(),
            "cycleLengthTicks": worldView.getCycleLengthTicks(),
            "overlayOpacity": worldView.getOverlayOpacity(),
            "phase": worldView.getPhase(),
        },
        "player": {
            "room": list(player.getRoom()),
            "x": player.getTileX(),
            "y": player.getTileY(),
            "direction": player.getDirection(),
        },
        "classes": classes,
        "classImages": [images.get(name) for name in classes],
        "rooms": rooms,
        "lights": lights,
    }
