import random

from entity.apple import Apple
from entity.banana import Banana
from entity.food import Food
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.living.livingEntity import LivingEntity
from npc.npcBehavior import NpcBehavior, NpcState

_FOOD_TYPES = (Apple, Banana)
_RESOURCE_TYPES = (OakWood, Stone)
_GATHER_TYPES = _FOOD_TYPES + _RESOURCE_TYPES

# OakWood pieces required before the NPC starts placing a shelter wall.
_BUILD_THRESHOLD = 7


# ------------------------------------------------------------------ #
# Module-level helpers (imported by agenticBehavior)                  #
# ------------------------------------------------------------------ #


def _locationOf(npc, room):
    lid = npc.getLocationID()
    if str(lid) == "-1":
        return None
    try:
        return room.getGrid().getLocation(lid)
    except KeyError:
        return None


def _getNeighbor(location, direction, grid):
    """Return the location in `direction` from `location`, or None if at edge."""
    if direction == 0:
        loc = grid.getUp(location)
    elif direction == 1:
        loc = grid.getLeft(location)
    elif direction == 2:
        loc = grid.getDown(location)
    else:
        loc = grid.getRight(location)
    return None if loc == -1 else loc


def _hasSolid(location):
    for entity in location.getEntities().values():
        if entity.isSolid():
            return True
    return False


def _hasLiving(location):
    for entity in location.getEntities().values():
        if isinstance(entity, LivingEntity):
            return True
    return False


def _manhattanDist(loc1, loc2):
    return abs(loc1.getX() - loc2.getX()) + abs(loc1.getY() - loc2.getY())


def _directionToward(current, target):
    """Return the cardinal direction (0-3) that reduces Manhattan distance most."""
    dx = target.getX() - current.getX()
    dy = target.getY() - current.getY()
    if abs(dx) >= abs(dy):
        return 3 if dx > 0 else 1
    return 2 if dy > 0 else 0


# ------------------------------------------------------------------ #
# Behavior                                                             #
# ------------------------------------------------------------------ #


_SCAN_INTERVAL = 30  # ticks between full-room scans for nearest resource


class _RoomKnowledge:
    """Remembers which (roomX, roomY) rooms have food and wood resources."""

    def __init__(self):
        self._data = {}  # (x, y) -> {"food": bool, "wood": bool}

    def record(self, roomX, roomY, hasFood, hasWood):
        self._data[(roomX, roomY)] = {"food": hasFood, "wood": hasWood}

    def hasFood(self, roomX, roomY):
        return self._data.get((roomX, roomY), {}).get("food", True)

    def hasWood(self, roomX, roomY):
        return self._data.get((roomX, roomY), {}).get("wood", True)

    def bestExitDirection(self, currentX, currentY, wantFood):
        """Return a preferred exit direction (0-3) toward a room known to have
        the desired resource, or None if no preference."""
        best = None
        bestDist = float("inf")
        for (rx, ry), info in self._data.items():
            if wantFood and not info.get("food", False):
                continue
            if not wantFood and not info.get("wood", False):
                continue
            dist = abs(rx - currentX) + abs(ry - currentY)
            if dist < bestDist:
                bestDist = dist
                best = (rx, ry)
        if best is None:
            return None
        dx = best[0] - currentX
        dy = best[1] - currentY
        if abs(dx) >= abs(dy):
            return 3 if dx > 0 else 1
        return 2 if dy > 0 else 0


class ProgrammaticBehavior(NpcBehavior):
    """Reactive decision loop — each tick picks the highest-priority action:

    1. Eat food from inventory when hungry.
    2. Gather a resource sitting on the current tile.
    3. Place one OakWood on an adjacent tile when carrying ≥ _BUILD_THRESHOLD.
    4. Step toward the nearest visible resource.
    5. If room is depleted, seek a room exit toward a better room.
    6. Wander (random step).
    """

    def __init__(self):
        self._state = NpcState.WANDERING
        self._lastGoal = ""
        self._nearestCache = None  # cached result of last _findNearest scan
        self._scanCooldown = 0  # ticks until next scan is allowed
        self._knowledge = _RoomKnowledge()
        self._wantsRoomChange = False

    # --- NpcBehavior interface ---

    def getStateName(self):
        return self._state.value

    def getGoalDescription(self):
        return self._lastGoal

    def wantsRoomChange(self) -> bool:
        return self._wantsRoomChange

    def clearRoomChangeRequest(self):
        self._wantsRoomChange = False

    def tick(self, npc, room, tick, config):
        tps = config.ticksPerSecond
        if tick <= npc.getTickLastMoved() + tps / npc.getMovementSpeed():
            return

        location = _locationOf(npc, room)
        if location is None:
            return

        # 1. Eat if hungry.
        if npc.needsEnergy() and self._tryEat(npc, tick):
            self._state = NpcState.EATING
            self._lastGoal = "eating"
            return

        # 2. Gather resource at current tile (skip if inventory full).
        if npc.getInventory().getNumFreeInventorySlots() > 0:
            if self._tryGather(npc, location, room, tick):
                self._state = NpcState.GATHERING
                self._lastGoal = "gathering"
                self._nearestCache = None  # picked something up — rescan next time
                return

        # 3. Place wood if carrying enough.
        woodCount = npc.getInventory().getNumItemsByType(OakWood)
        if woodCount >= _BUILD_THRESHOLD and self._tryPlace(npc, location, room, tick):
            self._state = NpcState.PLACING
            self._lastGoal = "building shelter"
            return

        # 4. Step toward nearest resource (cached scan every _SCAN_INTERVAL ticks).
        if npc.getInventory().getNumFreeInventorySlots() == 0:
            self._state = NpcState.WANDERING
            self._lastGoal = "inventory full"
            self._move(npc, location, room, tick, random.randint(0, 3))
            return

        self._scanCooldown -= 1
        if self._scanCooldown <= 0:
            want = _FOOD_TYPES if npc.needsEnergy() else _RESOURCE_TYPES
            self._nearestCache = self._findNearest(location, room, want)
            # Record what this room has so future cross-room decisions are informed.
            hasFood = self._findNearest(location, room, _FOOD_TYPES) is not None
            hasWood = self._findNearest(location, room, _RESOURCE_TYPES) is not None
            self._knowledge.record(room.getX(), room.getY(), hasFood, hasWood)
            self._scanCooldown = _SCAN_INTERVAL

        target = self._nearestCache
        if target is not None:
            self._state = NpcState.SEEKING_RESOURCE
            self._lastGoal = "moving to resource"
            self._move(npc, location, room, tick, _directionToward(location, target))
            return

        # 5. Room appears depleted — seek an exit toward a better room.
        if npc.needsEnergy():
            self._state = NpcState.SEEKING_EXIT
            self._lastGoal = "leaving room to find food"
            preferredDir = self._knowledge.bestExitDirection(
                room.getX(), room.getY(), wantFood=True
            )
            self._moveTowardExit(npc, location, room, tick, preferredDir)
            return

        # 6. Wander.
        self._state = NpcState.WANDERING
        self._lastGoal = "exploring"
        self._move(npc, location, room, tick, random.randint(0, 3))

    # --- private helpers ---

    def _tryEat(self, npc, tick):
        for slot in npc.getInventory().getInventorySlots():
            if slot.isEmpty():
                continue
            item = slot.getContents()[0]
            if isinstance(item, Food) and item.getEnergy() > 0:
                npc.addEnergy(item.getEnergy())
                npc.getInventory().removeByItem(item)
                npc.setTickLastMoved(tick)
                return True
        return False

    def _tryGather(self, npc, location, room, tick):
        """Pick up the first gatherable entity on the NPC's current tile."""
        for entity in list(location.getEntities().values()):
            if entity is npc or isinstance(entity, LivingEntity):
                continue
            if isinstance(entity, _GATHER_TYPES):
                if npc.getInventory().placeIntoFirstAvailableInventorySlot(entity):
                    room.removeEntity(entity)
                    npc.setTickLastGathered(tick)
                    npc.setTickLastMoved(tick)
                    return True
        return False

    def _tryPlace(self, npc, location, room, tick):
        """Place one OakWood on a random clear adjacent tile."""
        woodSlot = None
        for slot in npc.getInventory().getInventorySlots():
            if not slot.isEmpty() and isinstance(slot.getContents()[0], OakWood):
                woodSlot = slot
                break
        if woodSlot is None:
            return False

        grid = room.getGrid()
        directions = list(range(4))
        random.shuffle(directions)
        for direction in directions:
            neighbor = _getNeighbor(location, direction, grid)
            if neighbor is None or _hasSolid(neighbor) or _hasLiving(neighbor):
                continue
            item = woodSlot.pop()
            if item == -1:
                return False
            room.addEntityToLocation(item, neighbor)
            npc.setTickLastPlaced(tick)
            npc.setTickLastMoved(tick)
            return True
        return False

    def _moveTowardExit(self, npc, location, room, tick, preferredDir):
        """Walk toward the nearest room edge; signal room-change when reached."""
        grid = room.getGrid()
        gridSize = grid.getRows()
        x, y = location.getX(), location.getY()

        # Distance from each edge (direction 0=up=north means y decreases).
        edgeDist = {0: y, 2: gridSize - 1 - y, 1: x, 3: gridSize - 1 - x}

        # Pick preferred direction first, then nearest edge as fallback.
        candidates = sorted(edgeDist, key=edgeDist.get)
        if preferredDir is not None and preferredDir not in candidates[:1]:
            candidates.insert(0, preferredDir)

        for direction in candidates:
            neighbor = _getNeighbor(location, direction, grid)
            if neighbor is None:
                # We are already at this edge — signal the manager to cross rooms.
                self._wantsRoomChange = True
                npc.setTickLastMoved(tick)
                return
            if not _hasSolid(neighbor):
                location.removeEntity(npc)
                neighbor.addEntity(npc)
                npc.setLocationID(neighbor.getID())
                npc.setDirection(direction)
                npc.setTickLastMoved(tick)
                npc.removeEnergy(0.5)
                return

        # Completely boxed in — just wait.
        npc.setTickLastMoved(tick)

    def _findNearest(self, location, room, entityTypes):
        """Return the location of the nearest entity of the given types, or None."""
        best = None
        bestDist = float("inf")
        for lid in room.getGrid().getLocations():
            loc = room.getGrid().getLocation(lid)
            for entity in loc.getEntities().values():
                if isinstance(entity, entityTypes):
                    d = _manhattanDist(location, loc)
                    if d < bestDist:
                        bestDist = d
                        best = loc
        return best

    def _move(self, npc, location, room, tick, direction):
        neighbor = _getNeighbor(location, direction, room.getGrid())
        # Blocked by edge or solid — try perpendicular directions before giving up.
        if neighbor is None or _hasSolid(neighbor):
            for alt in [(direction + 1) % 4, (direction + 3) % 4, (direction + 2) % 4]:
                candidate = _getNeighbor(location, alt, room.getGrid())
                if candidate is not None and not _hasSolid(candidate):
                    neighbor = candidate
                    direction = alt
                    break
            else:
                npc.setTickLastMoved(tick)
                return
        location.removeEntity(npc)
        neighbor.addEntity(npc)
        npc.setLocationID(neighbor.getID())
        npc.setDirection(direction)
        npc.setTickLastMoved(tick)
        npc.removeEnergy(0.5)
