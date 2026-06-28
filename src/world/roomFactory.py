from collections import deque
from math import ceil
import random
from entity.apple import Apple
from entity.banana import Banana
from entity.caveEntrance import CaveEntrance
from entity.caveFloor import CaveFloor
from entity.caveLadder import CaveLadder
from entity.coalOre import CoalOre
from entity.goldOre import GoldOre
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

    def createRoom(self, roomType, x, y, z=0):
        if roomType == RoomType.EMPTY:
            room = self.createEmptyRoom((0, 0, 0), x, y, z)
        elif roomType == RoomType.GRASSLAND:
            room = self.createGrassRoom(x, y, z)
        elif roomType == RoomType.FOREST:
            room = self.createForestRoom(x, y, z)
        elif roomType == RoomType.JUNGLE:
            room = self.createJungleRoom(x, y, z)
        elif roomType == RoomType.MOUNTAIN:
            room = self.createMountainRoom(x, y, z)
        elif roomType == RoomType.CAVE:
            room = self.createCaveRoom(x, y, z)
        else:
            room = None
        if room is not None:
            self.lastRoomTypeCreated = roomType
        _logger.debug(
            "room created",
            roomType=str(roomType),
            roomX=x,
            roomY=y,
            roomZ=z,
        )
        return room

    def createRandomRoom(self, x, y, z=0):
        number = random.randrange(0, 4)
        if number == 0:
            newRoom = self.createRoom(RoomType.GRASSLAND, x, y, z)
        elif number == 1:
            newRoom = self.createRoom(RoomType.FOREST, x, y, z)
        elif number == 2:
            newRoom = self.createRoom(RoomType.JUNGLE, x, y, z)
        elif number == 3:
            newRoom = self.createRoom(RoomType.MOUNTAIN, x, y, z)
        else:
            newRoom = self.createRoom(RoomType.EMPTY, x, y, z)
        return newRoom

    def createEmptyRoom(self, color, x, y, z=0):
        newRoom = Room(
            ("(" + str(x) + ", " + str(y) + ")"),
            self.gridSize,
            color,
            x,
            y,
            self.renderer,
            z,
        )
        return newRoom

    def createGrassRoom(self, x, y, z=0):
        newRoomColor = (
            random.randrange(200, 210),
            random.randrange(130, 140),
            random.randrange(60, 70),
        )
        newRoom = self.createEmptyRoom(newRoomColor, x, y, z)
        self.spawnGrass(newRoom)
        self.spawnSomeRocks(newRoom)
        self.spawnChickens(newRoom)
        self.spawnRabbits(newRoom)
        if random.randrange(1, 101) <= 5:
            self._spawnCaveEntrance(newRoom)
        return newRoom

    def createForestRoom(self, x, y, z=0):
        newRoom = self.createGrassRoom(x, y, z)
        maxTrees = ceil(self.gridSize / 3)
        for _ in range(maxTrees):
            self.spawnOakTree(newRoom)
        self.spawnDeer(newRoom)
        self.spawnBears(newRoom)
        self.spawnWolves(newRoom)
        if random.randrange(1, 101) <= 15:
            self._spawnCaveEntrance(newRoom)
        return newRoom

    def createJungleRoom(self, x, y, z=0):
        newRoom = self.createGrassRoom(x, y, z)
        self.spawnLeaves(newRoom)
        maxTrees = ceil(self.gridSize / 3)
        for _ in range(maxTrees * 4):
            self.spawnJungleTree(newRoom)
        self.spawnSnakes(newRoom)
        return newRoom

    def createMountainRoom(self, x, y, z=0):
        newRoom = self.createEmptyRoom(
            (
                random.randrange(100, 110),
                random.randrange(100, 110),
                random.randrange(100, 110),
            ),
            x,
            y,
            z,
        )
        self._fillMountainWithOpenAreas(newRoom)
        if random.randrange(1, 101) <= 40:
            self._spawnCaveEntrance(newRoom)
        return newRoom

    def _fillMountainWithOpenAreas(self, room: Room):
        """Fill with stone but carve open corridors so the room is traversable.
        Uses a two-pass approach: fill ~70% with stone, then smooth once to
        create natural boulder clusters with walkable paths between them."""
        size = self.gridSize
        grid = room.getGrid()

        # first pass: random stone placement (~70%) with ore mixed in
        stone_grid = [[False] * size for _ in range(size)]
        for row in range(size):
            for col in range(size):
                r = random.random()
                if r < 0.70:
                    stone_grid[row][col] = True

        # smooth once: a cell becomes stone if 5+ of its 8 neighbours are stone
        smoothed = [row[:] for row in stone_grid]
        for row in range(size):
            for col in range(size):
                stone_neighbors = 0
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if nr < 0 or nr >= size or nc < 0 or nc >= size:
                            stone_neighbors += 1
                        elif stone_grid[nr][nc]:
                            stone_neighbors += 1
                smoothed[row][col] = stone_neighbors >= 5
        stone_grid = smoothed

        # keep the centre cell clear so the player always has a landing spot
        if size >= 3:
            centre = size // 2
            stone_grid[centre][centre] = False

        for row in range(size):
            for col in range(size):
                location = grid.getLocationByCoordinates(col, row)
                if location == -1:
                    continue
                if stone_grid[row][col]:
                    # chance to replace stone with ore
                    r = random.random()
                    if r < 0.04:
                        room.addEntityToLocation(CoalOre(), location)
                    elif r < 0.06:
                        room.addEntityToLocation(IronOre(), location)
                    else:
                        room.addEntityToLocation(Stone(), location)

    def createCaveRoom(self, x, y, z):
        depth = abs(z)
        bgIntensity = max(5, 30 - depth * 8)
        bgColor = (bgIntensity, max(3, bgIntensity - 4), max(2, bgIntensity - 6))
        room = self.createEmptyRoom(bgColor, x, y, z)
        self._generateCaveTiles(room, depth)
        return room

    def _generateCaveTiles(self, room, depth):
        size = self.gridSize
        # p_open decreases with depth: shallower caves are more open
        p_open = max(0.30, 0.45 - (depth - 1) * 0.05)

        # build a boolean grid: True = open, False = stone
        grid = [[random.random() < p_open for _ in range(size)] for _ in range(size)]

        # always clear the centre so the player has a guaranteed entry point
        centre = size // 2
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                cx, cy = centre + dx, centre + dy
                if 0 <= cx < size and 0 <= cy < size:
                    grid[cy][cx] = True

        # 4 passes of Moore-neighbourhood cellular automata
        for _ in range(4):
            next_grid = [row[:] for row in grid]
            for row in range(size):
                for col in range(size):
                    stone_count = 0
                    for nr in range(row - 1, row + 2):
                        for nc in range(col - 1, col + 2):
                            if nr == row and nc == col:
                                continue
                            if nr < 0 or nr >= size or nc < 0 or nc >= size:
                                stone_count += 1
                            elif not grid[nr][nc]:
                                stone_count += 1
                    next_grid[row][col] = stone_count < 5
            grid = next_grid

        # flood-fill from centre to find the largest connected open region
        open_cells = self._largestConnectedRegion(grid, size, centre, centre)

        # place cave floor on all open cells, stone on everything else
        for row in range(size):
            for col in range(size):
                location = room.getGrid().getLocationByCoordinates(col, row)
                if location == -1:
                    continue
                if not open_cells[row][col]:
                    room.addEntityToLocation(Stone(), location)
                else:
                    room.addEntityToLocation(CaveFloor(), location)

        # scatter ore on stone cells adjacent to open cells
        self._scatterCaveOre(room, open_cells, size, depth)

        # place a ladder at a random open cell away from centre
        ladder_loc = self._randomOpenCellFarFrom(room, open_cells, size, centre, centre)
        if ladder_loc is not None:
            room.addEntityToLocation(CaveLadder(), ladder_loc)

        # optionally place a deeper cave entrance (not at the deepest level)
        if depth < 3:
            chance = 30 if depth == 1 else 20
            if random.randrange(1, 101) <= chance:
                avoid = self._coordsOf(ladder_loc, room) if ladder_loc else None
                entrance_loc = self._randomOpenCellFarFrom(
                    room, open_cells, size, centre, centre, avoid=avoid
                )
                if entrance_loc is not None:
                    room.addEntityToLocation(CaveEntrance(), entrance_loc)

        _logger.debug("cave room generated", depth=depth, roomName=room.getName())

    def _largestConnectedRegion(self, grid, size, start_col, start_row):
        visited = [[False] * size for _ in range(size)]
        if not grid[start_row][start_col]:
            # centre is stone; find any open cell
            for r in range(size):
                for c in range(size):
                    if grid[r][c]:
                        start_row, start_col = r, c
                        break
                else:
                    continue
                break

        queue = deque([(start_row, start_col)])
        visited[start_row][start_col] = True
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < size
                    and 0 <= nc < size
                    and not visited[nr][nc]
                    and grid[nr][nc]
                ):
                    visited[nr][nc] = True
                    queue.append((nr, nc))

        # seal any open cell not reachable from the starting cell
        result = [[False] * size for _ in range(size)]
        for r in range(size):
            for c in range(size):
                result[r][c] = visited[r][c]
        return result

    def _scatterCaveOre(self, room, open_cells, size, depth):
        ore_chances = {
            1: [(CoalOre, 6), (IronOre, 3)],
            2: [(IronOre, 6), (GoldOre, 2)],
            3: [(GoldOre, 8), (IronOre, 3)],
        }
        ores = ore_chances.get(depth, [(CoalOre, 4)])
        for row in range(size):
            for col in range(size):
                if open_cells[row][col]:
                    continue
                # check if this stone cell borders an open cell
                has_open_neighbor = any(
                    0 <= row + dr < size
                    and 0 <= col + dc < size
                    and open_cells[row + dr][col + dc]
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                )
                if not has_open_neighbor:
                    continue
                for ore_class, chance in ores:
                    if random.randrange(1, 101) <= chance:
                        location = room.getGrid().getLocationByCoordinates(col, row)
                        if location != -1:
                            room.addEntityToLocation(ore_class(), location)
                        break

    def _randomOpenCellFarFrom(self, room, open_cells, size, cx, cy, avoid=None):
        candidates = []
        for row in range(size):
            for col in range(size):
                if not open_cells[row][col]:
                    continue
                dist = abs(col - cx) + abs(row - cy)
                if dist < size // 4:
                    continue
                if avoid and avoid == (col, row):
                    continue
                candidates.append((col, row))
        if not candidates:
            # fall back to any open cell
            for row in range(size):
                for col in range(size):
                    if open_cells[row][col]:
                        candidates.append((col, row))
        if not candidates:
            return None
        col, row = random.choice(candidates)
        return room.getGrid().getLocationByCoordinates(col, row)

    def _coordsOf(self, location, room):
        if location is None:
            return None
        return (location.getX(), location.getY())

    def _spawnCaveEntrance(self, room):
        grid = room.getGrid()
        size = self.gridSize
        # prefer an open (non-solid) cell; clear one stone if none is available
        candidates = []
        fallback = []
        for locationId in grid.getLocations():
            loc = grid.getLocation(locationId)
            entities = list(loc.getEntities().values())
            if not any(e.isSolid() for e in entities):
                candidates.append(loc)
            elif all(isinstance(e, Stone) for e in entities):
                fallback.append(loc)
        if candidates:
            loc = random.choice(candidates)
        elif fallback:
            loc = random.choice(fallback)
            for eid in list(loc.getEntities().keys()):
                loc.removeEntity(loc.getEntity(eid))
        else:
            return
        room.addEntityToLocation(CaveEntrance(), loc)
        # clear a 1-tile radius around the entrance so it's approachable
        ex, ey = loc.getX(), loc.getY()
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                neighbor = grid.getLocationByCoordinates(ex + dc, ey + dr)
                if neighbor == -1:
                    continue
                for eid in list(neighbor.getEntities().keys()):
                    entity = neighbor.getEntity(eid)
                    if isinstance(entity, Stone):
                        neighbor.removeEntity(entity)

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
