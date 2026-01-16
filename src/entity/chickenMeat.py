from entity.food import Food
import random


# @author Copilot
# Client-side representation of Chicken Meat
class ChickenMeat(Food):
    def __init__(self):
        Food.__init__(self, "Chicken Meat", "assets/images/chicken.png", random.randrange(5, 11))
        self.solid = False

    def isSolid(self):
        return self.solid
