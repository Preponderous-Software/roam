from enum import Enum


class NpcState(Enum):
    IDLE = "idle"
    WANDERING = "wandering"
    SEEKING_RESOURCE = "seeking_resource"
    GATHERING = "gathering"
    SEEKING_BUILD_SITE = "seeking_build_site"
    PLACING = "placing"
    EATING = "eating"


class NpcBehavior:
    """Abstract base for NPC behavior drivers."""

    def tick(self, npc, room, tick, config):
        """Drive one tick of NPC behavior. May mutate npc position/inventory/state."""
        raise NotImplementedError

    def getStateName(self):
        return "unknown"

    def getGoalDescription(self):
        return ""
