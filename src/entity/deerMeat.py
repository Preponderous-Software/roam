from entity.food import Food


# @author Copilot
# Client-side representation of Deer Meat
class DeerMeat(Food):
    ENERGY_VALUE = 7.5

    def __init__(self):
        Food.__init__(self, "Deer Meat", "assets/images/deerMeat.png", DeerMeat.ENERGY_VALUE)
        self.solid = False

    def isSolid(self):
        return self.solid
