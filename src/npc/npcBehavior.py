from enum import Enum


class NpcState(Enum):
    IDLE = "idle"
    WANDERING = "wandering"
    SEEKING_RESOURCE = "seeking_resource"
    GATHERING = "gathering"
    SEEKING_BUILD_SITE = "seeking_build_site"
    PLACING = "placing"
    EATING = "eating"
    SEEKING_EXIT = "seeking_exit"


class NpcBehavior:
    """Abstract base for NPC behavior drivers."""

    def tick(self, npc, room, tick, config):
        """Drive one tick of NPC behavior. May mutate npc position/inventory/state."""
        raise NotImplementedError

    def getStateName(self):
        return "unknown"

    def getGoalDescription(self):
        return ""

    def wantsRoomChange(self) -> bool:
        """Return True if the NPC has reached a room edge and wants to cross."""
        return False

    def clearRoomChangeRequest(self):
        """Reset the room-change flag after the manager has handled it."""
        pass
