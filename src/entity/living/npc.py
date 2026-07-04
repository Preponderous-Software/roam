import random

from entity.apple import Apple
from entity.banana import Banana
from entity.living.livingEntity import LivingEntity
from inventory.inventory import Inventory

_NPC_NAMES = [
    "Alex",
    "Blair",
    "Casey",
    "Drew",
    "Ellis",
    "Finn",
    "Gray",
    "Harper",
    "Indra",
    "Jordan",
    "Kai",
    "Lane",
    "Morgan",
    "Noel",
    "Payton",
]

_DIR_IMAGES = {
    0: "assets/images/npc_up.png",
    1: "assets/images/npc_left.png",
    2: "assets/images/npc_down.png",
    3: "assets/images/npc_right.png",
    -1: "assets/images/npc_down.png",
}


class Npc(LivingEntity):
    """An autonomous agent that mimics player capabilities.

    Supports two modes:
      "npc" — driven by a deterministic finite-state machine (programmatic)
      "cpc" — driven by Claude AI (Co-Player Character; requires ANTHROPIC_API_KEY)
    """

    def __init__(self, name, tickCreated):
        LivingEntity.__init__(
            self,
            name,
            _DIR_IMAGES[-1],
            100,
            [Apple, Banana],
            tickCreated,
        )
        self.direction = -1
        self.lastDirection = -1
        self.inventory = Inventory()
        self.movementSpeed = 15
        self.gatherSpeed = 20
        self.placeSpeed = 20
        self.tickLastMoved = -1
        self.tickLastGathered = -1
        self.tickLastPlaced = -1
        self.solid = False
        self.mode = "npc"

    # --- direction / facing ---

    def setDirection(self, direction):
        self.lastDirection = self.direction
        self.direction = direction
        self.imagePath = _DIR_IMAGES.get(direction, _DIR_IMAGES[-1])

    def getDirection(self):
        return self.direction

    def getLastDirection(self):
        return self.lastDirection

    # --- inventory ---

    def getInventory(self):
        return self.inventory

    def setInventory(self, inventory):
        self.inventory = inventory

    # --- physics ---

    def isSolid(self):
        return self.solid

    # --- speeds & cooldowns ---

    def getMovementSpeed(self):
        return self.movementSpeed

    def getGatherSpeed(self):
        return self.gatherSpeed

    def getPlaceSpeed(self):
        return self.placeSpeed

    def getTickLastMoved(self):
        return self.tickLastMoved

    def setTickLastMoved(self, tick):
        self.tickLastMoved = tick

    def getTickLastGathered(self):
        return self.tickLastGathered

    def setTickLastGathered(self, tick):
        self.tickLastGathered = tick

    def getTickLastPlaced(self):
        return self.tickLastPlaced

    def setTickLastPlaced(self, tick):
        self.tickLastPlaced = tick

    # --- mode (npc vs cpc) ---

    def getMode(self):
        return self.mode

    def setMode(self, mode):
        self.mode = mode


def randomNpcName():
    return random.choice(_NPC_NAMES)
