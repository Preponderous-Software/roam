import random
from entity.food import Food


# @author Daniel McCoy Stephenson
# Berry entity for server-backed architecture
class Berry(Food):
    def __init__(self):
        # Intentionally reuse banana.png as the Berry sprite as a temporary placeholder
        # (see WI-008 in WORK_ITEMS.md for dedicated berry sprite). This matches
        # the sprite usage in serverBackedWorldScreen.py for consistency.
        Food.__init__(
            self, "Berry", "assets/images/banana.png", random.randrange(3, 8)
        )
        self.solid = False

    def isSolid(self):
        return self.solid
