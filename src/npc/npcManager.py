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

    def tickRoom(self, room, tick):
        from entity.living.npc import Npc

        for entityId in list(room.getLivingEntities().keys()):
            entity = room.getLivingEntities().get(entityId)
            if entity is None or not isinstance(entity, Npc):
                continue
            behavior = self._getBehavior(entity)
            behavior.tick(entity, room, tick, self._config)

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
