# @author Copilot
# @since April 20th, 2026
from appContainer import component

# Maps every entity class name to its asset image path.
ENTITY_IMAGE_PATHS = {
    # Creatures
    "Bear": "assets/images/bear.png",
    "Chicken": "assets/images/chicken.png",
    "Deer": "assets/images/deer.png",
    "Rabbit": "assets/images/rabbit.png",
    "Snake": "assets/images/snake.png",
    "Wolf": "assets/images/wolf.png",
    # Food
    "Apple": "assets/images/apple.png",
    "Banana": "assets/images/banana.png",
    "BearMeat": "assets/images/bearMeat.png",
    "ChickenMeat": "assets/images/chickenMeat.png",
    "Wheat": "assets/images/wheat.png",
    # Cave
    "CaveEntrance": "assets/images/caveEntrance.png",
    "CaveFloor": "assets/images/caveFloor.png",
    "CaveLadder": "assets/images/caveLadder.png",
    "GoldOre": "assets/images/goldOre.png",
    # Resources
    "CoalOre": "assets/images/coalOre.png",
    "Grass": "assets/images/grass.png",
    "IronOre": "assets/images/ironOre.png",
    "JungleWood": "assets/images/jungleWood.png",
    "Leaves": "assets/images/leaves.png",
    "OakWood": "assets/images/oakWood.png",
    "Stone": "assets/images/stone.png",
    # Structures
    "Bed": "assets/images/bed.png",
    "Campfire": "assets/images/campfire.png",
    "Chest": "assets/images/chest.png",
    "Fence": "assets/images/fence.png",
    "StoneBed": "assets/images/stoneBed.png",
    "StoneFloor": "assets/images/stoneFloor.png",
    "Torch": "assets/images/torch.png",
    "WoodFloor": "assets/images/woodFloor.png",
    # Crops & Seeds
    "MatureCrop": "assets/images/matureCrop.png",
    "WheatSeed": "assets/images/wheatSeed.png",
    "YoungCrop": "assets/images/youngCrop.png",
    # Other
    "Excrement": "assets/images/excrement.png",
    "Gravestone": "assets/images/gravestone.png",
}

# Human-readable display names keyed by class name.
ENTITY_DISPLAY_NAMES = {
    "Apple": "Apple",
    "Banana": "Banana",
    "Bear": "Bear",
    "BearMeat": "Bear Meat",
    "Bed": "Bed",
    "Campfire": "Campfire",
    "Chest": "Chest",
    "Chicken": "Chicken",
    "ChickenMeat": "Chicken Meat",
    "CaveEntrance": "Cave Entrance",
    "CaveFloor": "Cave Floor",
    "CaveLadder": "Ladder",
    "CoalOre": "Coal Ore",
    "Deer": "Deer",
    "Excrement": "Excrement",
    "Fence": "Fence",
    "Grass": "Grass",
    "Gravestone": "Gravestone",
    "GoldOre": "Gold Ore",
    "IronOre": "Iron Ore",
    "JungleWood": "Jungle Wood",
    "Leaves": "Leaves",
    "MatureCrop": "Mature Crop",
    "OakWood": "Oak Wood",
    "Rabbit": "Rabbit",
    "Snake": "Snake",
    "Stone": "Stone",
    "StoneBed": "Stone Bed",
    "StoneFloor": "Stone Floor",
    "Torch": "Torch",
    "Wheat": "Wheat",
    "WheatSeed": "Wheat Seed",
    "Wolf": "Wolf",
    "WoodFloor": "Wood Floor",
    "YoungCrop": "Young Crop",
}

_LIVING_ENTITY_NAMES = {"Bear", "Chicken", "Deer", "Rabbit", "Snake", "Wolf"}

# Subset kept for goal-registry backward compatibility.
ALL_LIVING_ENTITY_TYPES = sorted(_LIVING_ENTITY_NAMES)

# Full sorted list of every entity type tracked by the codex.
ALL_ENTITY_TYPES = sorted(ENTITY_IMAGE_PATHS)


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
