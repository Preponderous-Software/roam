import random
from entity.food import Food


# @author Daniel McCoy Stephenson
# Berry entity for server-backed architecture
class Berry(Food):
    def __init__(self):
        # Reuse banana image as placeholder for berries
        Food.__init__(
            self, "Berry", "assets/images/banana.png", random.randrange(3, 8)
        )
        self.solid = False

    def isSolid(self):
        return self.solid
