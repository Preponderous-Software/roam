import os
import random
from lib.graphik.src.graphik import Graphik
from lib.pyenvlib.entity import Entity
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.tickCounter import TickCounter
from world.room import Room


# @author Daniel McCoy Stephenson
# @since August 15th, 2022
class Map:
    def __init__(self, gridSize, graphik: Graphik, tickCounter: TickCounter, config):
        self.rooms = []
        self._roomIndex = {}
        self.gridSize = gridSize
        self.graphik = graphik
        self.tickCounter = tickCounter
        self.config = config
        self.roomFactory = RoomFactory(self.gridSize, self.graphik, self.tickCounter)

    def getRooms(self):
        return self.rooms

    def getRoom(self, x, y):
        key = (x, y)
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
            self.addRoom(room)
            return room

        return -1

    def getLocationOfEntity(self, entity: Entity, room: Room):
        locationID = entity.getLocationID()
        grid = room.getGrid()
        return grid.getLocation(locationID)

    def generateNewRoom(self, x, y):
        # 50% chance to generate last room type
        newRoom = None
        if random.randrange(1, 101) > 50:
            newRoom = self.roomFactory.createRoom(
                self.roomFactory.lastRoomTypeCreated, x, y
            )
        else:
            newRoom = self.roomFactory.createRandomRoom(x, y)
        self.rooms.append(newRoom)
        self._roomIndex[(x, y)] = newRoom

        return newRoom

    def addRoom(self, room):
        self.rooms.append(room)
        self._roomIndex[(room.getX(), room.getY())] = room
