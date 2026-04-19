import os
import random
import threading
from config.config import Config
from gameLogging.logger import getLogger
from lib.graphik.src.graphik import Graphik
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
        self, gridSize, graphik: Graphik, tickCounter: TickCounter, config: Config
    ):
        self.rooms = []
        self._roomIndex = {}
        self._lock = threading.Lock()
        self.gridSize = gridSize
        self.graphik = graphik
        self.tickCounter = tickCounter
        self.config = config
        self.roomFactory = RoomFactory(self.gridSize, self.graphik, self.tickCounter)

    def getRooms(self):
        return self.rooms

    def hasRoom(self, x, y):
        key = (x, y)
        with self._lock:
            return key in self._roomIndex

    def getRoom(self, x, y):
        key = (x, y)
        with self._lock:
            if key in self._roomIndex:
                return self._roomIndex[key]

        # attempt to load room if file exists, otherwise generate new room
        nextRoomPath = (
            self.config.pathToSaveDirectory
            + "/rooms/room_"
            + str(x)
            + "_"
            + str(y)
            + ".json"
        )
        if os.path.exists(nextRoomPath):
            roomJsonReaderWriter = RoomJsonReaderWriter(
                self.gridSize, self.graphik, self.tickCounter, self.config
            )
            room = roomJsonReaderWriter.loadRoom(nextRoomPath)
            _logger.info("room loaded from file", roomX=x, roomY=y, path=nextRoomPath)
            return self.addRoom(room)

        return -1

    def getLocationOfEntity(self, entity: Entity, room: Room):
        locationID = entity.getLocationID()
        grid = room.getGrid()
        return grid.getLocation(locationID)

    def generateNewRoom(self, x, y):
        with self._lock:
            if (x, y) in self._roomIndex:
                return self._roomIndex[(x, y)]
        # 50% chance to generate last room type
        newRoom = None
        if random.randrange(1, 101) > 50:
            newRoom = self.roomFactory.createRoom(
                self.roomFactory.lastRoomTypeCreated, x, y
            )
        else:
            newRoom = self.roomFactory.createRandomRoom(x, y)
        with self._lock:
            if (x, y) in self._roomIndex:
                return self._roomIndex[(x, y)]
            self.rooms.append(newRoom)
            self._roomIndex[(x, y)] = newRoom

        _logger.info("room generated", roomX=x, roomY=y)
        return newRoom

    def addRoom(self, room):
        key = (room.getX(), room.getY())
        with self._lock:
            if key in self._roomIndex:
                return self._roomIndex[key]
            self.rooms.append(room)
            self._roomIndex[key] = room
        return room
