# @author Copilot
# @since April 20th, 2026
from appContainer import component

# All known living entity types for the codex.
ALL_LIVING_ENTITY_TYPES = ["Bear", "Chicken"]

# Maps entity class names to their asset image paths.
ENTITY_IMAGE_PATHS = {
    "Bear": "assets/images/bear.png",
    "Chicken": "assets/images/chicken.png",
}


@component
class Codex:
    def __init__(self):
        self.discovered = set()

    def discover(self, entityClassName: str):
        """Add the entity class name to the discovered set.
        Returns True if this is a new discovery, False otherwise."""
        if entityClassName in self.discovered:
            return False
        self.discovered.add(entityClassName)
        return True

    def hasDiscovered(self, entityClassName: str) -> bool:
        return entityClassName in self.discovered

    def getDiscoveredEntities(self) -> list:
        return sorted(self.discovered)

    def reset(self):
        self.discovered = set()

    def setDiscovered(self, entities):
        self.discovered = set(entities)
