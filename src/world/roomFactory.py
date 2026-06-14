from math import ceil
import random
from entity.apple import Apple
from entity.banana import Banana
from entity.coalOre import CoalOre
from entity.grass import Grass
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.leaves import Leaves
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.deer import Deer
from entity.living.rabbit import Rabbit
from entity.living.snake import Snake
from entity.living.wolf import Wolf
from entity.stone import Stone
from entity.oakWood import OakWood
from gameLogging.logger import getLogger
from lib.pyenvlib.entity import Entity

from world.room import Room
from world.roomType import RoomType

_logger = getLogger(__name__)


class RoomFactory:
    def __init__(self, gridSize, renderer, tickCounter):
        self.gridSize = gridSize
        self.renderer = renderer
        self.tickCounter = tickCounter
        self.lastRoomTypeCreated = RoomType.GRASSLAND

    def createRoom(self, roomType, x, y):
        if roomType == RoomType.EMPTY:
            room = self.createEmptyRoom((0, 0, 0), x, y)
        elif roomType == RoomType.GRASSLAND:
            room = self.createGrassRoom(x, y)
        elif roomType == RoomType.FOREST:
            room = self.createForestRoom(x, y)
        elif roomType == RoomType.JUNGLE:
            room = self.createJungleRoom(x, y)
        elif roomType == RoomType.MOUNTAIN:
            room = self.createMountainRoom(x, y)
        else:
            room = None
        if room is not None:
            self.lastRoomTypeCreated = roomType
        _logger.debug(
            "room created",
            roomType=str(roomType),
            roomX=x,
            roomY=y,
        )
        return room

    def createRandomRoom(self, x, y):
        number = random.randrange(0, 4)
        if number == 0:
            newRoom = self.createRoom(RoomType.GRASSLAND, x, y)
        elif number == 1:
            newRoom = self.createRoom(RoomType.FOREST, x, y)
        elif number == 2:
            newRoom = self.createRoom(RoomType.JUNGLE, x, y)
        elif number == 3:
            newRoom = self.createRoom(RoomType.MOUNTAIN, x, y)
        else:
            newRoom = self.createRoom(RoomType.EMPTY, x, y)
        return newRoom

    def createEmptyRoom(self, color, x, y):
        newRoom = Room(
            ("(" + str(x) + ", " + str(y) + ")"),
            self.gridSize,
            color,
            x,
            y,
            self.renderer,
        )
        return newRoom

    def createGrassRoom(self, x, y):
        newRoomColor = (
            random.randrange(200, 210),
            random.randrange(130, 140),
            random.randrange(60, 70),
        )
        newRoom = self.createEmptyRoom(newRoomColor, x, y)
        self.spawnGrass(newRoom)
        self.spawnSomeRocks(newRoom)
        self.spawnChickens(newRoom)
        self.spawnRabbits(newRoom)

        return newRoom

    def createForestRoom(self, x, y):
        newRoom = self.createGrassRoom(x, y)
        maxTrees = ceil(self.gridSize / 3)
        for _ in range(maxTrees):
            self.spawnOakTree(newRoom)
        self.spawnDeer(newRoom)
        self.spawnBears(newRoom)
        self.spawnWolves(newRoom)
        return newRoom

    def createJungleRoom(self, x, y):
        newRoom = self.createGrassRoom(x, y)
        self.spawnLeaves(newRoom)
        maxTrees = ceil(self.gridSize / 3)
        for _ in range(maxTrees * 4):
            self.spawnJungleTree(newRoom)
        self.spawnSnakes(newRoom)
        return newRoom

    def createMountainRoom(self, x, y):
        newRoom = self.createEmptyRoom(
            (
                random.randrange(100, 110),
                random.randrange(100, 110),
                random.randrange(100, 110),
            ),
            x,
            y,
        )
        self.spawnSomeOre(newRoom)
        self.fillWithRocks(newRoom)

        return newRoom

    def spawnGrass(self, room: Room):
        for locationId in room.getGrid().getLocations():
            location = room.getGrid().getLocation(locationId)
            if random.randrange(1, 101) > 5:
                room.addEntityToLocation(Grass(), location)

    def spawnSomeRocks(self, room: Room):
        for locationId in room.getGrid().getLocations():
            location = room.getGrid().getLocation(locationId)
            if random.randrange(1, 101) == 1:
                room.addEntityToLocation(Stone(), location)

    def fillWithRocks(self, room: Room):
        for locationId in room.getGrid().getLocations():
            location = room.getGrid().getLocation(locationId)
            room.addEntityToLocation(Stone(), location)

    def spawnSomeOre(self, room: Room):
        for locationId in room.getGrid().getLocations():
            location = room.getGrid().getLocation(locationId)
            if random.randrange(1, 101) == 1:
                if random.randrange(1, 101) > 50:
                    room.addEntityToLocation(CoalOre(), location)
                else:
                    room.addEntityToLocation(IronOre(), location)

    def spawnOakTree(self, room: Room):
        wood = OakWood()
        room.addEntity(wood)

        location = self.getLocationOfEntity(wood, room)

        locationsToSpawnApples = []
        locationsToSpawnApples.append(room.grid.getUp(location))
        locationsToSpawnApples.append(room.grid.getLeft(location))
        locationsToSpawnApples.append(room.grid.getDown(location))
        locationsToSpawnApples.append(room.grid.getRight(location))

        # spawn leaves and apples around the tree
        for appleSpawnLocation in locationsToSpawnApples:
            if appleSpawnLocation == -1 or self.locationContainsEntityType(
                appleSpawnLocation, OakWood
            ):
                continue
            room.addEntityToLocation(Leaves(), appleSpawnLocation)
            if random.randrange(0, 2) == 0:
                room.addEntityToLocation(Apple(), appleSpawnLocation)

    def spawnJungleTree(self, room: Room):
        wood = JungleWood()
        room.addEntity(wood)

        location = self.getLocationOfEntity(wood, room)

        locationsToSpawnLeaves = []
        locationsToSpawnLeaves.append(room.grid.getUp(location))
        locationsToSpawnLeaves.append(room.grid.getLeft(location))
        locationsToSpawnLeaves.append(room.grid.getDown(location))
        locationsToSpawnLeaves.append(room.grid.getRight(location))

        for leavesSpawnLocation in locationsToSpawnLeaves:
            if leavesSpawnLocation == -1 or self.locationContainsEntityType(
                leavesSpawnLocation, JungleWood
            ):
                continue
            room.addEntityToLocation(Leaves(), leavesSpawnLocation)
            room.addEntityToLocation(Leaves(), leavesSpawnLocation)

        for bananaSpawnLocation in locationsToSpawnLeaves:
            if bananaSpawnLocation == -1 or self.locationContainsEntityType(
                bananaSpawnLocation, JungleWood
            ):
                continue
            if random.randrange(0, 2) == 0:
                room.addEntityToLocation(Banana(), bananaSpawnLocation)

    def _spawnLivingEntities(self, room: Room, creatureClass, attempts, spawnChance):
        # Make `attempts` independent rolls, each spawning one creature with
        # probability `spawnChance` (1-100). Shared by every per-creature
        # spawner so spawn density is tuned in one place.
        count = 0
        for _ in range(attempts):
            if random.randrange(1, 101) <= spawnChance:
                creature = creatureClass(self.tickCounter.getTick())
                room.addEntity(creature)
                room.addLivingEntity(creature)
                count += 1
        if count > 0:
            _logger.debug(
                "spawned creatures",
                creature=creatureClass.__name__,
                count=count,
                roomName=room.getName(),
            )

    def spawnChickens(self, room: Room):
        self._spawnLivingEntities(room, Chicken, attempts=5, spawnChance=25)

    def spawnRabbits(self, room: Room):
        self._spawnLivingEntities(room, Rabbit, attempts=5, spawnChance=20)

    def spawnDeer(self, room: Room):
        self._spawnLivingEntities(room, Deer, attempts=3, spawnChance=20)

    def spawnBears(self, room: Room):
        self._spawnLivingEntities(room, Bear, attempts=2, spawnChance=10)

    def spawnWolves(self, room: Room):
        self._spawnLivingEntities(room, Wolf, attempts=2, spawnChance=10)

    def spawnSnakes(self, room: Room):
        self._spawnLivingEntities(room, Snake, attempts=3, spawnChance=15)

    def spawnLeaves(self, room: Room):
        for locationId in room.getGrid().getLocations():
            location = room.getGrid().getLocation(locationId)
            if random.randrange(1, 101) > 5:
                room.addEntityToLocation(Leaves(), location)

    def getLocationOfEntity(self, entity: Entity, room: Room):
        locationID = entity.getLocationID()
        grid = room.getGrid()
        return grid.getLocation(locationID)

    def locationContainsEntityType(self, location, entityType):
        for entityId in location.getEntities():
            entity = location.getEntity(entityId)
            if isinstance(entity, entityType):
                return True
        return False
