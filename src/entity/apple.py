import random
from entity.food import Food


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Apple(Food):
    def __init__(self):
        Food.__init__(self, "Apple", "assets/images/apple.png", random.randrange(5, 11))
