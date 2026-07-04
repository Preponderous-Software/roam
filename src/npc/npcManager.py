"""Manages all NPC instances in the current room."""
from entity.apple import Apple
from entity.oakWood import OakWood


class NpcManager:
    """Instantiates behaviors, drives NPC ticks, and exposes mode toggle."""

    def __init__(self, config):
        self._config = config
        self._mode = getattr(config, "npcMode", "npc")
        self._behaviors = {}  # UUID -> NpcBehavior

    # ------------------------------------------------------------------ #
    # Mode management                                                      #
    # ------------------------------------------------------------------ #

    def getMode(self):
        return self._mode

    def getModeDisplay(self):
        return "CPC" if self._mode == "cpc" else "NPC"

    def toggleMode(self):
        self._mode = "cpc" if self._mode == "npc" else "npc"
        self._behaviors.clear()

    # ------------------------------------------------------------------ #
    # Spawning                                                             #
    # ------------------------------------------------------------------ #

    def spawnNpc(self, room, tick):
        from entity.living.npc import Npc, randomNpcName

        npc = Npc(randomNpcName(), tick)
        npc.setMode(self._mode)
        for _ in range(3):
            npc.getInventory().placeIntoFirstAvailableInventorySlot(OakWood())
        for _ in range(3):
            npc.getInventory().placeIntoFirstAvailableInventorySlot(Apple())
        spawnLoc = self._findOpenSpawnLocation(room)
        if spawnLoc is not None:
            room.addEntityToLocation(npc, spawnLoc)
        else:
            room.addEntity(npc)
        room.addLivingEntity(npc)
        return npc

    def dropInventoryAtDeath(self, npc, room):
        """Scatter NPC inventory items at its current location when it dies."""
        from npc.programmaticBehavior import _locationOf

        location = _locationOf(npc, room)
        if location is None:
            return
        for slot in npc.getInventory().getInventorySlots():
            while not slot.isEmpty():
                item = slot.pop()
                if item and item != -1:
                    room.addEntityToLocation(item, location)

    # ------------------------------------------------------------------ #
    # Per-tick update                                                      #
    # ------------------------------------------------------------------ #

    def tickActiveRooms(self, map, roomX, roomY, z, radius, tick):
        """Tick NPCs in every loaded room within *radius* of (roomX, roomY, z).

        Returns a set of Room objects that were dirtied by NPC activity so the
        caller can persist non-current rooms asynchronously.
        """
        from entity.living.npc import Npc

        dirtyRooms = set()
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                room = map.getRoom(roomX + dx, roomY + dy, z)
                if room == -1 or room is None:
                    continue
                wantingExit = []
                for entityId in list(room.getLivingEntities().keys()):
                    entity = room.getLivingEntities().get(entityId)
                    if entity is None or not isinstance(entity, Npc):
                        continue
                    behavior = self._getBehavior(entity)
                    behavior.tick(entity, room, tick, self._config)
                    if behavior.wantsRoomChange():
                        behavior.clearRoomChangeRequest()
                        wantingExit.append(entity)
                if wantingExit:
                    dirtyRooms.add(room)
                for npc in wantingExit:
                    targetRoom = self._handleRoomCrossing(npc, room, map, z)
                    if targetRoom is not None:
                        dirtyRooms.add(targetRoom)
        return dirtyRooms

    def _handleRoomCrossing(self, npc, fromRoom, map, z):
        """Move npc from fromRoom into the adjacent room it walked into.

        Only moves to rooms that are already loaded or saved to disk; returns
        the target Room on success, None if the crossing could not be completed.
        """
        locationId = npc.getLocationID()
        try:
            location = fromRoom.getGrid().getLocation(locationId)
        except Exception:
            return None

        x, y = location.getX(), location.getY()
        gridEdge = fromRoom.getGrid().getRows() - 1

        # Skip corners (same limitation as player movement).
        if (x == 0 or x == gridEdge) and (y == 0 or y == gridEdge):
            return None

        fromRoomX, fromRoomY = fromRoom.getX(), fromRoom.getY()

        if x == 0:
            targetRoomX, targetRoomY = fromRoomX - 1, fromRoomY
            targetLocX, targetLocY = gridEdge, y
        elif x == gridEdge:
            targetRoomX, targetRoomY = fromRoomX + 1, fromRoomY
            targetLocX, targetLocY = 0, y
        elif y == 0:
            targetRoomX, targetRoomY = fromRoomX, fromRoomY - 1
            targetLocX, targetLocY = x, gridEdge
        elif y == gridEdge:
            targetRoomX, targetRoomY = fromRoomX, fromRoomY + 1
            targetLocX, targetLocY = x, 0
        else:
            return None

        targetRoom = map.getRoom(targetRoomX, targetRoomY, z)
        if targetRoom == -1 or targetRoom is None:
            return None

        targetLoc = targetRoom.getGrid().getLocationByCoordinates(
            targetLocX, targetLocY
        )
        if targetLoc == -1:
            return None

        fromRoom.removeEntity(npc)
        fromRoom.removeLivingEntity(npc)
        targetRoom.addEntityToLocation(npc, targetLoc)
        targetRoom.addLivingEntity(npc)
        return targetRoom

    # ------------------------------------------------------------------ #
    # Introspection for HUD / tooltip                                     #
    # ------------------------------------------------------------------ #

    def getBehaviorInfo(self, npc):
        """Return (stateName, goalDescription) for the given NPC."""
        behavior = self._behaviors.get(npc.getID())
        if behavior is None:
            return (self._mode, "")
        return (behavior.getStateName(), behavior.getGoalDescription())

    def _findOpenSpawnLocation(self, room):
        """Return a random non-solid location, or None if all are occupied."""
        import random

        grid = room.getGrid()
        lids = list(grid.getLocations())
        random.shuffle(lids)
        for lid in lids:
            loc = grid.getLocation(lid)
            if not any(e.isSolid() for e in loc.getEntities().values()):
                return loc
        return None

    def cleanupDeadNpcs(self, room):
        """Discard behavior records for NPCs no longer in the room."""
        living = set(room.getLivingEntities().keys())
        dead = [bid for bid in list(self._behaviors.keys()) if bid not in living]
        for bid in dead:
            del self._behaviors[bid]

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _getBehavior(self, npc):
        npcId = npc.getID()
        if npcId not in self._behaviors:
            if npc.getMode() == "cpc" or self._mode == "cpc":
                from npc.agenticBehavior import AgenticBehavior

                self._behaviors[npcId] = AgenticBehavior()
            else:
                from npc.programmaticBehavior import ProgrammaticBehavior

                self._behaviors[npcId] = ProgrammaticBehavior()
        return self._behaviors[npcId]
