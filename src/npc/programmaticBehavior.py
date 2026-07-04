import random

from entity.apple import Apple
from entity.banana import Banana
from entity.food import Food
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.woodFloor import WoodFloor
from entity.living.livingEntity import LivingEntity
from npc.npcBehavior import NpcBehavior, NpcState

# Relative (dx, dy) offsets for the 4-direction movement
_DIRS = {0: (0, -1), 1: (-1, 0), 2: (0, 1), 3: (1, 0)}

# 3×3 shelter outline (walls only, no floor, open south doorway)
# Each entry is (dx, dy) relative to chosen build origin
_SHELTER_PLAN = [
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (1, 1),
]

_FOOD_TYPES = (Apple, Banana)
_RESOURCE_TYPES = (OakWood, Stone)


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


def _scanRoom(room, entityTypes):
    """Return list of (location, entity) for the first matching entity of each type found."""
    results = []
    for lid in room.getGrid().getLocations():
        loc = room.getGrid().getLocation(lid)
        for entity in loc.getEntities().values():
            if isinstance(entity, entityTypes):
                results.append((loc, entity))
    return results


def _manhattanDist(loc1, loc2):
    return abs(loc1.getX() - loc2.getX()) + abs(loc1.getY() - loc2.getY())


def _directionToward(current, target):
    """Return the cardinal direction (0-3) that reduces Manhattan distance most."""
    dx = target.getX() - current.getX()
    dy = target.getY() - current.getY()
    if abs(dx) >= abs(dy):
        return 3 if dx > 0 else 1
    return 2 if dy > 0 else 0


class ProgrammaticBehavior(NpcBehavior):
    """Goal-directed FSM: gather food when hungry, collect wood, build a shelter."""

    def __init__(self):
        self._state = NpcState.IDLE
        self._targetLocation = None  # grid location the NPC is walking toward
        self._targetEntity = None  # entity to gather
        self._buildOrigin = None  # (x, y) chosen build-site origin
        self._buildQueue = []  # remaining (dx, dy) slots to place
        self._scanCooldown = 0  # ticks until next room scan
        self._idleTicks = 0  # ticks spent wandering/idle
        self._lastGoal = ""

    # --- public API ---

    def getStateName(self):
        return self._state.value

    def getGoalDescription(self):
        return self._lastGoal

    def tick(self, npc, room, tick, config):
        if not self._checkCooldown(npc, tick, config):
            return

        location = _locationOf(npc, room)
        if location is None:
            return

        # Priority 1: eat if hungry
        if npc.needsEnergy():
            if self._tryEatFromInventory(npc):
                self._state = NpcState.EATING
                npc.setTickLastGathered(tick)
                return
            # nothing to eat in inventory – seek food
            self._state = NpcState.SEEKING_RESOURCE
            self._lastGoal = "seek food"

        if self._state == NpcState.IDLE:
            self._decideNextGoal(npc, room)

        elif self._state == NpcState.WANDERING:
            self._wander(npc, location, room, tick)
            self._idleTicks += 1
            if self._idleTicks > 60:
                self._state = NpcState.IDLE
                self._idleTicks = 0

        elif self._state == NpcState.SEEKING_RESOURCE:
            self._seekResource(npc, location, room, tick)

        elif self._state == NpcState.GATHERING:
            self._gather(npc, location, room, tick)

        elif self._state == NpcState.SEEKING_BUILD_SITE:
            self._seekBuildSite(npc, location, room, tick)

        elif self._state == NpcState.PLACING:
            self._placeNext(npc, location, room, tick)

        elif self._state == NpcState.EATING:
            self._state = NpcState.IDLE

    # --- private helpers ---

    def _checkCooldown(self, npc, tick, config):
        tps = config.ticksPerSecond
        speed = npc.getMovementSpeed()
        return tick > npc.getTickLastMoved() + tps / speed

    def _decideNextGoal(self, npc, room):
        # Need energy? seek food.
        if npc.needsEnergy():
            self._state = NpcState.SEEKING_RESOURCE
            self._lastGoal = "find food"
            return

        # Have enough wood to start building?
        woodCount = npc.getInventory().getNumItemsByType(OakWood)
        if woodCount >= len(_SHELTER_PLAN):
            self._state = NpcState.SEEKING_BUILD_SITE
            self._lastGoal = "build shelter"
            self._buildOrigin = None
            return

        # Gather wood or stone
        self._state = NpcState.SEEKING_RESOURCE
        self._lastGoal = "gather resources"

    def _seekResource(self, npc, location, room, tick):
        self._scanCooldown -= 1
        if self._scanCooldown <= 0:
            self._scanCooldown = 30
            want = _FOOD_TYPES if npc.needsEnergy() else _RESOURCE_TYPES
            candidates = _scanRoom(room, want)
            if candidates:
                # pick closest
                candidates.sort(key=lambda x: _manhattanDist(location, x[0]))
                self._targetLocation, self._targetEntity = candidates[0]

        if self._targetLocation is None:
            self._wander(npc, location, room, tick)
            return

        if location == self._targetLocation:
            self._state = NpcState.GATHERING
            return

        direction = _directionToward(location, self._targetLocation)
        self._move(npc, location, room, tick, direction)

    def _gather(self, npc, location, room, tick):
        target = self._targetLocation
        if target is None:
            self._state = NpcState.IDLE
            return

        # Pick up a pickupable entity at the target
        for entity in list(target.getEntities().values()):
            if entity is npc:
                continue
            if isinstance(entity, LivingEntity):
                continue
            if isinstance(entity, (_FOOD_TYPES + _RESOURCE_TYPES)):
                if npc.getInventory().placeIntoFirstAvailableInventorySlot(entity):
                    room.removeEntity(entity)
                    npc.setTickLastGathered(tick)
                break

        self._targetLocation = None
        self._targetEntity = None
        self._state = NpcState.IDLE

    def _seekBuildSite(self, npc, location, room, tick):
        if self._buildOrigin is None:
            # Find a clear 3x3 area
            origin = self._findBuildOrigin(location, room)
            if origin is None:
                self._state = NpcState.WANDERING
                return
            self._buildOrigin = (origin.getX(), origin.getY())
            self._buildQueue = list(_SHELTER_PLAN)

        ox, oy = self._buildOrigin
        targetX, targetY = ox, oy

        if location.getX() == targetX and location.getY() == targetY:
            self._state = NpcState.PLACING
            return

        targetLoc = room.getGrid().getLocationByCoordinates(targetX, targetY)
        if targetLoc == -1:
            self._buildOrigin = None
            self._state = NpcState.IDLE
            return

        direction = _directionToward(location, targetLoc)
        self._move(npc, location, room, tick, direction)

    def _placeNext(self, npc, location, room, tick):
        if not self._buildQueue:
            self._state = NpcState.IDLE
            self._buildOrigin = None
            self._lastGoal = "idle (shelter done)"
            return

        woodInInventory = [
            s
            for s in npc.getInventory().getInventorySlots()
            if not s.isEmpty() and isinstance(s.getContents()[0], OakWood)
        ]
        if not woodInInventory:
            self._buildQueue = []
            self._state = NpcState.SEEKING_RESOURCE
            self._lastGoal = "gather more wood"
            return

        dx, dy = self._buildQueue[0]
        ox, oy = self._buildOrigin
        targetX, targetY = ox + dx, oy + dy
        targetLoc = room.getGrid().getLocationByCoordinates(targetX, targetY)

        if targetLoc == -1 or _hasSolid(targetLoc) or _hasLiving(targetLoc):
            # Skip this slot if it's occupied or out of range
            self._buildQueue.pop(0)
            return

        # Move to adjacent tile of the target and face it
        if _manhattanDist(location, targetLoc) > 1:
            direction = _directionToward(location, targetLoc)
            self._move(npc, location, room, tick, direction)
            return

        # Place the item
        slot = woodInInventory[0]
        item = slot.pop()
        if item == -1:
            self._buildQueue.pop(0)
            return
        room.addEntityToLocation(item, targetLoc)
        npc.setTickLastPlaced(tick)
        self._buildQueue.pop(0)

        if not self._buildQueue:
            self._state = NpcState.IDLE
            self._lastGoal = "idle (shelter done)"

    def _wander(self, npc, location, room, tick, direction=None):
        if direction is None:
            direction = random.randint(0, 3)
        self._move(npc, location, room, tick, direction)

    def _move(self, npc, location, room, tick, direction):
        neighbor = _getNeighbor(location, direction, room.getGrid())
        if neighbor is None:
            # At room edge – bounce: try perpendicular directions
            for alt in [(direction + 1) % 4, (direction + 3) % 4, (direction + 2) % 4]:
                neighbor = _getNeighbor(location, alt, room.getGrid())
                if neighbor is not None and not _hasSolid(neighbor):
                    direction = alt
                    break
            else:
                return
        if _hasSolid(neighbor):
            return
        location.removeEntity(npc)
        neighbor.addEntity(npc)
        npc.setLocationID(neighbor.getID())
        npc.setDirection(direction)
        npc.setTickLastMoved(tick)
        npc.removeEnergy(0.5)

    def _tryEatFromInventory(self, npc):
        for slot in npc.getInventory().getInventorySlots():
            if slot.isEmpty():
                continue
            item = slot.getContents()[0]
            if isinstance(item, Food) and item.getEnergy() > 0:
                npc.addEnergy(item.getEnergy())
                npc.getInventory().removeByItem(item)
                return True
        return False

    def _findBuildOrigin(self, location, room):
        """Find a clear cell at least 3 tiles from current location."""
        grid = room.getGrid()
        candidates = []
        for lid in grid.getLocations():
            loc = grid.getLocation(lid)
            if _hasSolid(loc) or _hasLiving(loc):
                continue
            dist = _manhattanDist(location, loc)
            if dist < 3:
                continue
            # Check the 3×3 region around this candidate is reasonably open
            clear = True
            for dx, dy in _SHELTER_PLAN:
                nx, ny = loc.getX() + dx, loc.getY() + dy
                nloc = grid.getLocationByCoordinates(nx, ny)
                if nloc == -1 or _hasSolid(nloc):
                    clear = False
                    break
            if clear:
                candidates.append((dist, loc))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        # pick a mid-range candidate (not too close, not too far)
        idx = min(len(candidates) - 1, len(candidates) // 3)
        return candidates[idx][1]
