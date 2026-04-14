from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Food(DrawableEntity):
    def __init__(self, name, color, energy):
        DrawableEntity.__init__(self, name, color)
        self.energy = energy

    def getEnergy(self):
        return self.energy

    def setEnergy(self, energy):
        self.energy = energy
