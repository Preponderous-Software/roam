import os
import random
import threading
from config.config import Config
from gameLogging.logger import getLogger
from rendering.renderer import Renderer
from lib.pyenvlib.entity import Entity
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.tickCounter import TickCounter
from world.room import Room

_logger = getLogger(__name__)


# @author Daniel McCoy Stephenson
# @since August 15th, 2022
class Map:
    def __init__(
        self,
        gridSize,
        renderer: Renderer,
        tickCounter: TickCounter,
        config: Config,
        roomFactory: RoomFactory = None,
        roomJsonReaderWriterFactory=None,
    ):
        self.rooms = []
        self._roomIndex = {}
        self._lock = threading.Lock()
        self._freshlyGeneratedRooms = set()
        self.gridSize = gridSize
        self.renderer = renderer
        self.tickCounter = tickCounter
        self.config = config
        self.roomFactory = roomFactory or RoomFactory(
            self.gridSize, self.renderer, self.tickCounter
        )
        self._roomJsonReaderWriterFactory = roomJsonReaderWriterFactory

    def getRooms(self):
        return self.rooms

    def hasRoom(self, x, y, z=0):
        key = (x, y, z)
        with self._lock:
            return key in self._roomIndex

    def getRoom(self, x, y, z=0):
        key = (x, y, z)
        with self._lock:
            if key in self._roomIndex:
                return self._roomIndex[key]

        # attempt to load room if file exists, otherwise generate new room
        nextRoomPath = self.config.getRoomFilePath(x, y, z)
        if os.path.exists(nextRoomPath):
            if self._roomJsonReaderWriterFactory is not None:
                roomJsonReaderWriter = self._roomJsonReaderWriterFactory()
            else:
                roomJsonReaderWriter = RoomJsonReaderWriter(
                    self.gridSize, self.renderer, self.tickCounter, self.config
                )
            room = roomJsonReaderWriter.loadRoom(nextRoomPath)
            if room is None:
                _logger.error(
                    "room file unreadable; generating a fresh room instead",
                    roomX=x,
                    roomY=y,
                    roomZ=z,
                    path=nextRoomPath,
                )
                return -1
            _logger.info(
                "room loaded from file", roomX=x, roomY=y, roomZ=z, path=nextRoomPath
            )
            return self.addRoom(room)

        return -1

    def getLocationOfEntity(self, entity: Entity, room: Room):
        locationID = entity.getLocationID()
        grid = room.getGrid()
        return grid.getLocation(locationID)

    def generateNewRoom(self, x, y, z=0):
        with self._lock:
            if (x, y, z) in self._roomIndex:
                return self._roomIndex[(x, y, z)]
        newRoom = None
        if z < 0:
            newRoom = self.roomFactory.createCaveRoom(x, y, z)
        elif random.randrange(1, 101) > 50:
            newRoom = self.roomFactory.createRoom(
                self.roomFactory.lastRoomTypeCreated, x, y, z
            )
        else:
            newRoom = self.roomFactory.createRandomRoom(x, y, z)
        with self._lock:
            if (x, y, z) in self._roomIndex:
                return self._roomIndex[(x, y, z)]
            self.rooms.append(newRoom)
            self._roomIndex[(x, y, z)] = newRoom
            self._freshlyGeneratedRooms.add((x, y, z))

        _logger.info("room generated", roomX=x, roomY=y, roomZ=z)
        return newRoom

    def consumeIsNewRoom(self, x, y, z=0):
        """Return True and clear the flag if the room at (x, y, z) was freshly
        generated (never existed on disk).  Thread-safe; can be called from
        any thread."""
        key = (x, y, z)
        with self._lock:
            if key in self._freshlyGeneratedRooms:
                self._freshlyGeneratedRooms.discard(key)
                return True
        return False

    def addRoom(self, room):
        key = (room.getX(), room.getY(), room.getZ())
        with self._lock:
            if key in self._roomIndex:
                return self._roomIndex[key]
            self.rooms.append(room)
            self._roomIndex[key] = room
        return room
