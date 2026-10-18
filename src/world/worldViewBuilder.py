from collections import Counter

from appContainer import component
from config.config import Config
from rendering.worldView import ActorView, CameraHint, LightView, RoomView, WorldView
from world.biomeInference import inferBiomeFromCounts
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


class _RoomCacheEntry:
    # WorldViewBuilder's in-memory cache for one room (never persisted).
    def __init__(self, room, player):
        self.room = room
        self.player = player
        self.revision = None
        self.roomType = None
        self.roomView = None
        self.lights = ()
        self.images = ()
        self.imageMap = {}
        self.stacks = []
        self.counts = Counter()
        # location (by identity) -> lights on it, only for locations with any
        self.lightsByLocation = {}


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
        # (x, y, z) -> _RoomCacheEntry. A room is re-read only when it is a
        # different Room object or its revision (moved by every entity
        # add/remove, world/trackedLocation) or roomType changed, and then only
        # the locations it reports as changed. In-memory only.
        self._roomCache = {}
        # living entity (by identity) -> (locationId, direction, image, view)
        self._actorCache = {}
        self._seenActors = set()

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
        seenKeys = set()
        self._seenActors = set()
        roomViews = []
        actors = []
        lights = []
        for room in rooms:
            if (
                abs(room.getX() - playerRoomKey[0]) > radiusRooms
                or abs(room.getY() - playerRoomKey[1]) > radiusRooms
            ):
                continue
            roomView, roomLights, roomImages = self._getRoomParts(
                room, player, gridSize, seenKeys
            )
            roomViews.append(roomView)
            lights.extend(roomLights)
            for name, imagePath in roomImages:
                classImages.setdefault(name, imagePath)
            self._collectActors(room, player, actors)

        self._pruneCache(seenKeys)
        for entity in [e for e in self._actorCache if e not in self._seenActors]:
            del self._actorCache[entity]

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

    def _getRoomParts(self, room, player, gridSize, seenKeys):
        key = (room.getX(), room.getY(), room.getZ())
        seenKeys.add(key)
        revision = room.getRevision()
        roomType = room.getRoomType()
        entry = self._roomCache.get(key)
        if entry is None or entry.room is not room or entry.player is not player:
            entry = self._roomCache[key] = _RoomCacheEntry(room, player)
        elif entry.revision == revision and entry.roomType == roomType:
            return entry.roomView, entry.lights, entry.images
        self._refreshRoom(entry, gridSize, key, revision, roomType)
        return entry.roomView, entry.lights, entry.images

    def _pruneCache(self, keepKeys):
        """Forget cached rooms whose keys are not in keepKeys."""
        for key in [key for key in self._roomCache if key not in keepKeys]:
            del self._roomCache[key]

    def _refreshRoom(self, entry, gridSize, roomKey, revision, roomType):
        room = entry.room
        changed = None
        if entry.revision is not None and len(entry.stacks) == gridSize * gridSize:
            changed = room.getChangedLocationsSince(entry.revision)
        if changed is None:
            # First build, a change the room could not attribute to a
            # location, or more changes than its log keeps: read everything.
            entry.stacks = [()] * (gridSize * gridSize)
            entry.counts = Counter()
            entry.lightsByLocation = {}
            changed = list(room.getGrid().getLocations().values())
        seen = set()
        for location in changed:
            if location in seen:
                continue
            seen.add(location)
            self._readLocation(entry, location, gridSize, roomKey)
        tiles = tuple(entry.stacks)
        if roomType is not None:
            biome = roomType
        else:
            biome = inferBiomeFromCounts(entry.counts, room.getZ())
        entry.revision = revision
        entry.roomType = roomType
        entry.lights = tuple(
            light
            for _, locationLights in sorted(entry.lightsByLocation.values())
            for light in locationLights
        )
        entry.images = tuple(entry.imageMap.items())
        entry.roomView = RoomView(
            room.getX(),
            room.getY(),
            room.getZ(),
            biome,
            roomType,
            room.getBackgroundColor(),
            # Room.getRevision(): a process-wide sequence value that changes on
            # every entity add/remove in the room and is never reused, so equal
            # revisions mean equal tiles. In-memory only, never saved.
            revision,
            tiles,
        )

    def _readLocation(self, entry, location, gridSize, roomKey):
        x, y = location.getX(), location.getY()
        if not (0 <= x < gridSize and 0 <= y < gridSize):
            return
        index = y * gridSize + x
        player = entry.player
        images = entry.imageMap
        names = []
        lights = []
        for entity in list(location.getEntities().values()):
            if entity is player:
                continue
            name = entity.__class__.__name__
            names.append(name)
            if name not in images:
                images[name] = _imagePathOf(entity)
            if isLightSource(entity):
                lights.append(LightView(roomKey, x, y, entity.getLightRadius(), name))
        names = tuple(names)
        counts = entry.counts
        counts.subtract(entry.stacks[index])
        counts.update(names)
        entry.stacks[index] = names
        if lights:
            # Sorted by tile index, so lights come out in grid order whichever
            # location changed last.
            entry.lightsByLocation[location] = (index, tuple(lights))
        else:
            entry.lightsByLocation.pop(location, None)

    def _collectActors(self, room, player, actors):
        # Living entities move and change sprite (facing, reproduction
        # cooldown) without a tile-class change, so they are checked every
        # build, but an unchanged one reuses its ActorView.
        roomKey = (room.getX(), room.getY(), room.getZ())
        grid = None
        cache = self._actorCache
        for entity in list(room.getLivingEntities().values()):
            if entity is player:
                continue
            self._seenActors.add(entity)
            locationId = entity.getLocationID()
            direction = directionName(entity)
            image = _imagePathOf(entity)
            cached = cache.get(entity)
            if (
                cached is not None
                and cached[0] == locationId
                and cached[1] == direction
                and cached[2] == image
                and cached[3].getRoom() == roomKey
            ):
                actors.append(cached[3])
                continue
            if grid is None:
                grid = room.getGrid()
            try:
                location = grid.getLocation(locationId)
            except KeyError:
                continue
            view = ActorView(
                str(entity.getID()),
                entity.__class__.__name__,
                roomKey,
                location.getX(),
                location.getY(),
                direction,
                image,
            )
            cache[entity] = (locationId, direction, image, view)
            actors.append(view)
