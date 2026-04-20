import random
from entity.food import Food


# @since April 14th, 2026
class ChickenMeat(Food):
    def __init__(self):
        Food.__init__(
            self,
            "Chicken Meat",
            "assets/images/chickenMeat.png",
            random.randrange(15, 26),
        )
