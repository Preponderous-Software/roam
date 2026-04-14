import random
from entity.food import Food


# @since April 14th, 2026
class BearMeat(Food):
    def __init__(self):
        Food.__init__(
            self,
            "Bear Meat",
            "assets/images/bearMeat.png",
            random.randrange(25, 36),
        )
        self.solid = False

    def isSolid(self):
        return self.solid
