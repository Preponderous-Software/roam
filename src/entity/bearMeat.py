from entity.food import Food
import random


# @author Copilot
# Client-side representation of Bear Meat
class BearMeat(Food):
    def __init__(self):
        Food.__init__(
            self, "Bear Meat", "assets/images/bear.png", random.randrange(5, 11)
        )
        self.solid = False

    def isSolid(self):
        return self.solid
