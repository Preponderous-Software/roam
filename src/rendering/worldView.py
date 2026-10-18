# @author Claude
# @since October 18th, 2026
#
# The WorldView seam (RFC 0017 stage 2): an immutable, per-tick, read-only
# snapshot of the part of the world a frontend may show. Game logic publishes
# it next to the pixel-shaped Renderer output; a 3D frontend (or the REST
# spectator) draws from it.
#
# Every part holds only primitives and tuples. They are COPIES, never live
# Entity/Room references, so a consumer cannot change game state through them.
# Attributes cannot be reassigned after construction, and each is read through
# an explicit getter (the repo does not use @property).


class _Frozen:
    __slots__ = ()

    def __setattr__(self, name, value):
        raise AttributeError(type(self).__name__ + " is immutable")

    def __delattr__(self, name):
        raise AttributeError(type(self).__name__ + " is immutable")

    def _init(self, **values):
        for name, value in values.items():
            object.__setattr__(self, name, value)


class RoomView(_Frozen):
    __slots__ = (
        "_x",
        "_y",
        "_z",
        "_biome",
        "_roomType",
        "_backgroundColor",
        "_revision",
        "_tiles",
    )

    def __init__(self, x, y, z, biome, roomType, backgroundColor, revision, tiles):
        # tiles: row-major tuple of gridSize² tuples of entity-class names,
        # bottom to top. revision changes whenever any tile's stack changes.
        self._init(
            _x=x,
            _y=y,
            _z=z,
            _biome=biome,
            _roomType=roomType,
            _backgroundColor=tuple(backgroundColor),
            _revision=revision,
            _tiles=tiles,
        )

    def getX(self):
        return self._x

    def getY(self):
        return self._y

    def getZ(self):
        return self._z

    def getKey(self):
        return (self._x, self._y, self._z)

    def getBiome(self):
        return self._biome

    def getRoomType(self):
        return self._roomType

    def getBackgroundColor(self):
        return self._backgroundColor

    def getRevision(self):
        return self._revision

    def getTiles(self):
        return self._tiles


class ActorView(_Frozen):
    __slots__ = (
        "_entityId",
        "_entityClass",
        "_room",
        "_tileX",
        "_tileY",
        "_direction",
        "_spriteKey",
    )

    def __init__(self, entityId, entityClass, room, tileX, tileY, direction, spriteKey):
        self._init(
            _entityId=entityId,
            _entityClass=entityClass,
            _room=tuple(room),
            _tileX=tileX,
            _tileY=tileY,
            _direction=direction,
            _spriteKey=spriteKey,
        )

    def getEntityId(self):
        return self._entityId

    def getEntityClass(self):
        return self._entityClass

    def getRoom(self):
        return self._room

    def getTileX(self):
        return self._tileX

    def getTileY(self):
        return self._tileY

    def getDirection(self):
        return self._direction

    def getSpriteKey(self):
        return self._spriteKey


class LightView(_Frozen):
    __slots__ = ("_room", "_tileX", "_tileY", "_radiusTiles", "_entityClass")

    def __init__(self, room, tileX, tileY, radiusTiles, entityClass):
        self._init(
            _room=tuple(room),
            _tileX=tileX,
            _tileY=tileY,
            _radiusTiles=radiusTiles,
            _entityClass=entityClass,
        )

    def getRoom(self):
        return self._room

    def getTileX(self):
        return self._tileX

    def getTileY(self):
        return self._tileY

    def getRadiusTiles(self):
        return self._radiusTiles

    def getEntityClass(self):
        return self._entityClass


class CameraHint(_Frozen):
    __slots__ = ("_followPlayer", "_focusRoom", "_focusTile", "_visibleRadiusRooms")

    def __init__(self, followPlayer, focusRoom, focusTile, visibleRadiusRooms):
        self._init(
            _followPlayer=followPlayer,
            _focusRoom=tuple(focusRoom),
            _focusTile=tuple(focusTile),
            _visibleRadiusRooms=visibleRadiusRooms,
        )

    def getFollowPlayer(self):
        return self._followPlayer

    def getFocusRoom(self):
        return self._focusRoom

    def getFocusTile(self):
        return self._focusTile

    def getVisibleRadiusRooms(self):
        return self._visibleRadiusRooms


class WorldView(_Frozen):
    __slots__ = (
        "_tick",
        "_gridSize",
        "_dayNightEnabled",
        "_cycleLengthTicks",
        "_overlayOpacity",
        "_phase",
        "_player",
        "_rooms",
        "_actors",
        "_lights",
        "_cameraHint",
        "_classImages",
    )

    def __init__(
        self,
        tick,
        gridSize,
        dayNightEnabled,
        cycleLengthTicks,
        overlayOpacity,
        phase,
        player,
        rooms,
        actors,
        lights,
        cameraHint,
        classImages,
    ):
        # classImages: tuple of (entityClassName, imagePath) pairs, one per
        # class seen in the view, so a frontend can load each class's sprite.
        self._init(
            _tick=tick,
            _gridSize=gridSize,
            _dayNightEnabled=dayNightEnabled,
            _cycleLengthTicks=cycleLengthTicks,
            _overlayOpacity=overlayOpacity,
            _phase=phase,
            _player=player,
            _rooms=tuple(rooms),
            _actors=tuple(actors),
            _lights=tuple(lights),
            _cameraHint=cameraHint,
            _classImages=tuple(classImages),
        )

    def getTick(self):
        return self._tick

    def getGridSize(self):
        return self._gridSize

    def isDayNightEnabled(self):
        return self._dayNightEnabled

    def getCycleLengthTicks(self):
        return self._cycleLengthTicks

    def getOverlayOpacity(self):
        return self._overlayOpacity

    def getPhase(self):
        return self._phase

    def getPlayer(self):
        return self._player

    def getRooms(self):
        return self._rooms

    def getActors(self):
        return self._actors

    def getLights(self):
        return self._lights

    def getCameraHint(self):
        return self._cameraHint

    def getClassImages(self):
        return self._classImages
