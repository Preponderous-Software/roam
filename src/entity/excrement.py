from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 16th, 2026
class Excrement(DrawableEntity):
    def __init__(self, tickCreated):
        DrawableEntity.__init__(self, "Excrement", "assets/images/excrement.png")
        self.tickCreated = tickCreated

    def getTickCreated(self):
        return self.tickCreated

    def setTickCreated(self, tickCreated):
        self.tickCreated = tickCreated
