from appContainer import component
from config.config import Config
from rendering.worldView import ActorView, CameraHint, LightView, RoomView, WorldView
from world.biomeInference import inferBiomeFromClassNames
from world.dayNightCycle import DayNightCycle
from world.lightSources import isLightSource

_DIRECTION_NAMES = {0: "up", 1: "left", 2: "down", 3: "right"}


def directionName(entity):
    """The way an entity faces, as "up"/"left"/"down"/"right": its current
    direction while moving, else the last one it moved in, else "down" (the
    spawn sprite). None for entities that have no direction."""
    getDirection = getattr(entity, "getDirection", None)
    if getDirection is None:
        return None
    direction = getDirection()
    if direction not in _DIRECTION_NAMES:
        getLastDirection = getattr(entity, "getLastDirection", None)
        direction = getLastDirection() if getLastDirection else None
    return _DIRECTION_NAMES.get(direction, "down")


def _imagePathOf(entity):
    getImagePath = getattr(entity, "getImagePath", None)
    return getImagePath() if getImagePath else None


# @author Claude
# @since October 18th, 2026
#
# Builds the per-tick WorldView (RFC 0017 stage 2) from ALREADY-LOADED rooms.
# A pure read: it copies the room list under Map._lock and then only reads
# room grids. It must never call Map.getRoom (that loads from disk),
# Map.generateNewRoom, RoomFactory, WorldScreen.getOrLoadRoom or any
# *JsonReaderWriter: building a view must not change what is saved.
# tests/api/test_snapshotSaveSafety.py enforces this with those patched to
# raise.
@component
class WorldViewBuilder:
    def __init__(self, dayNightCycle: DayNightCycle, config: Config):
        self.dayNightCycle = dayNightCycle
        self.config = config

    def build(self, map, player, tick, radiusRooms=1):
        """Return a WorldView of the loaded rooms within radiusRooms of the
        player's room (on every level), or None when the player is not in a
        loaded room."""
        with map._lock:
            rooms = list(map.getRooms())
        playerRoom = None
        environmentId = player.getEnvironmentID()
        for room in rooms:
            if room.getID() == environmentId:
                playerRoom = room
                break
        if playerRoom is None:
            return None
        gridSize = playerRoom.getGrid().getColumns()
        playerRoomKey = (playerRoom.getX(), playerRoom.getY(), playerRoom.getZ())
        playerLocation = playerRoom.getGrid().getLocation(player.getLocationID())
        playerTile = (playerLocation.getX(), playerLocation.getY())

        classImages = {}
        roomViews = []
        actors = []
        lights = []
        for room in rooms:
            if (
                abs(room.getX() - playerRoomKey[0]) > radiusRooms
                or abs(room.getY() - playerRoomKey[1]) > radiusRooms
            ):
                continue
            roomViews.append(
                self._buildRoomView(room, player, gridSize, classImages, actors, lights)
            )

        playerView = ActorView(
            str(player.getID()),
            player.__class__.__name__,
            playerRoomKey,
            playerTile[0],
            playerTile[1],
            directionName(player),
            _imagePathOf(player),
        )
        dayNightEnabled = self.config.dayNightCycleEnabled
        return WorldView(
            tick=tick,
            gridSize=gridSize,
            dayNightEnabled=dayNightEnabled,
            cycleLengthTicks=self.config.dayNightCycleLengthTicks,
            overlayOpacity=(
                self.dayNightCycle.getOverlayOpacity(tick) if dayNightEnabled else 0
            ),
            phase=self.dayNightCycle.getPhase(tick),
            player=playerView,
            rooms=roomViews,
            actors=actors,
            lights=lights,
            cameraHint=CameraHint(
                self.config.cameraFollowPlayer, playerRoomKey, playerTile, radiusRooms
            ),
            classImages=tuple(classImages.items()),
        )

    def _buildRoomView(self, room, player, gridSize, classImages, actors, lights):
        # One pass over the room's grid collects the tile stacks, the class
        # sprites and the lights; it runs every tick a sink wants a view, so it
        # is kept tight (see the timing note in CHANGELOG.md, 2026-10-18).
        roomKey = (room.getX(), room.getY(), room.getZ())
        stacks = [()] * (gridSize * gridSize)
        grid = room.getGrid()
        for location in list(grid.getLocations().values()):
            entities = location.getEntities()
            if not entities:
                continue
            x, y = location.getX(), location.getY()
            if not (0 <= x < gridSize and 0 <= y < gridSize):
                continue
            names = []
            for entity in list(entities.values()):
                if entity is player:
                    continue
                name = entity.__class__.__name__
                names.append(name)
                if name not in classImages:
                    classImages[name] = _imagePathOf(entity)
                if isLightSource(entity):
                    lights.append(
                        LightView(roomKey, x, y, entity.getLightRadius(), name)
                    )
            stacks[y * gridSize + x] = tuple(names)
        for entity in list(room.getLivingEntities().values()):
            if entity is player:
                continue
            try:
                location = grid.getLocation(entity.getLocationID())
            except KeyError:
                continue
            actors.append(
                ActorView(
                    str(entity.getID()),
                    entity.__class__.__name__,
                    roomKey,
                    location.getX(),
                    location.getY(),
                    directionName(entity),
                    _imagePathOf(entity),
                )
            )
        tiles = tuple(stacks)
        roomType = room.getRoomType()
        if roomType is not None:
            biome = roomType
        else:
            biome = inferBiomeFromClassNames(
                [name for stack in tiles for name in stack], room.getZ()
            )
        return RoomView(
            room.getX(),
            room.getY(),
            room.getZ(),
            biome,
            roomType,
            room.getBackgroundColor(),
            # A signature of the tile stacks: equal stacks give an equal
            # revision, so consumers can skip rebuilding unchanged rooms. It
            # covers every mutation path, including direct Location.addEntity /
            # removeEntity calls, at O(tiles) per build.
            hash(tiles),
            tiles,
        )
