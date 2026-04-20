import random
from entity.food import Food


# @author Daniel McCoy Stephenson
# @since January 28th, 2023
class Banana(Food):
    def __init__(self):
        Food.__init__(
            self, "Banana", "assets/images/banana.png", random.randrange(10, 20)
        )
