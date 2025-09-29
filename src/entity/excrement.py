from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# @since December 2024
class Excrement(DrawableEntity):
    def __init__(self, tickCreated):
        DrawableEntity.__init__(self, "Excrement", "assets/images/excrement.png")
        self.solid = False
        self.tickCreated = tickCreated

    def isSolid(self):
        return self.solid

    def getTickCreated(self):
        return self.tickCreated

    def getAge(self, currentTick):
        return currentTick - self.tickCreated