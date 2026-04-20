from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 20th, 2026
class MatureCrop(DrawableEntity):
    def __init__(self, tickPlanted):
        DrawableEntity.__init__(self, "Mature Crop", "assets/images/matureCrop.png")
        self.solid = False
        self.tickPlanted = tickPlanted

    def isSolid(self):
        return self.solid

    def getTickPlanted(self):
        return self.tickPlanted

    def setTickPlanted(self, tickPlanted):
        self.tickPlanted = tickPlanted
