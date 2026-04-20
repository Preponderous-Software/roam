import random
from entity.food import Food


# @author Copilot
# @since April 20th, 2026
class Wheat(Food):
    def __init__(self):
        Food.__init__(self, "Wheat", "assets/images/wheat.png", random.randrange(10, 21))
        self.solid = False

    def isSolid(self):
        return self.solid
