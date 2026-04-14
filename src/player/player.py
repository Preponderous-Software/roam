from entity.apple import Apple
from entity.banana import Banana
from entity.bearMeat import BearMeat
from entity.chickenMeat import ChickenMeat
from entity.living.livingEntity import LivingEntity
from inventory.inventory import Inventory


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Player(LivingEntity):
    def __init__(self, tickCreated):
        LivingEntity.__init__(
            self,
            "Player",
            "assets/images/player_down.png",
            100,
            [Apple, Banana, ChickenMeat, BearMeat],
            tickCreated,
        )
        self.direction = -1  # -1 when not moving
        self.lastDirection = -1
        self.inventory = Inventory()
        self.gathering = False
        self.placing = False
        self.tickLastMoved = -1
        self.tickLastGathered = -1
        self.tickLastPlaced = -1
        self.movementSpeed = 30
        self.gatherSpeed = 30
        self.placeSpeed = 30
        self.crouching = False
        self.solid = False

    def getDirection(self):
        return self.direction

    def setDirection(self, direction):
        self.lastDirection = self.direction
        self.direction = direction

        if self.direction == 0:
            self.imagePath = "assets/images/player_up.png"
        elif self.direction == 1:
            self.imagePath = "assets/images/player_left.png"
        elif self.direction == 2:
            self.imagePath = "assets/images/player_down.png"
        elif self.direction == 3:
            self.imagePath = "assets/images/player_right.png"

    def getLastDirection(self):
        return self.lastDirection

    def getInventory(self):
        return self.inventory

    def setInventory(self, inventory):
        self.inventory = inventory

    def isGathering(self):
        return self.gathering

    def setGathering(self, bool):
        self.gathering = bool

    def isPlacing(self):
        return self.placing

    def setPlacing(self, bool):
        self.placing = bool

    def isDead(self):
        return self.energy < 1

    def getTickLastMoved(self):
        return self.tickLastMoved

    def setTickLastMoved(self, tick):
        self.tickLastMoved = tick

    def getMovementSpeed(self):
        return self.movementSpeed

    def setMovementSpeed(self, newSpeed):
        self.movementSpeed = newSpeed

    def getTickLastGathered(self):
        return self.tickLastGathered

    def setTickLastGathered(self, tick):
        self.tickLastGathered = tick

    def getGatherSpeed(self):
        return self.gatherSpeed

    def setGatherSpeed(self, newSpeed):
        self.gatherSpeed = newSpeed

    def getTickLastPlaced(self):
        return self.tickLastPlaced

    def setTickLastPlaced(self, tick):
        self.tickLastPlaced = tick

    def getPlaceSpeed(self):
        return self.placeSpeed

    def setPlaceSpeed(self, newSpeed):
        self.placeSpeed = newSpeed

    def isCrouching(self):
        return self.crouching

    def setCrouching(self, bool):
        self.crouching = bool

    def getTickLastGathered(self):
        return self.tickLastGathered

    def setTickLastGathered(self, tick):
        self.tickLastGathered = tick

    def getTickLastPlaced(self):
        return self.tickLastPlaced

    def setTickLastPlaced(self, tick):
        self.tickLastPlaced = tick

    def isMoving(self):
        return self.direction != -1

    def isSolid(self):
        return self.solid
