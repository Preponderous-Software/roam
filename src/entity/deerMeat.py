from entity.food import Food
import random


# @author Copilot
# Client-side representation of Deer Meat
class DeerMeat(Food):
    def __init__(self):
        # Using chicken.png as placeholder since deer.png doesn't exist
        Food.__init__(self, "Deer Meat", "assets/images/chicken.png", random.randrange(5, 11))
        self.solid = False

    def isSolid(self):
        return self.solid
