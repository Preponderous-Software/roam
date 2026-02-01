import random
from entity.food import Food


# @author Daniel McCoy Stephenson
# Berry entity for server-backed architecture
class Berry(Food):
    def __init__(self):
        Food.__init__(
            self, "Berry", "assets/images/berry.png", random.randrange(3, 8)
        )
        self.solid = False

    def isSolid(self):
        return self.solid
