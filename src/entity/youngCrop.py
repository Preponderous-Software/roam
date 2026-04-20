from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 20th, 2026
class YoungCrop(DrawableEntity):
    def __init__(self, tickPlanted):
        DrawableEntity.__init__(self, "Young Crop", "assets/images/youngCrop.png")
        self.tickPlanted = tickPlanted

    def getTickPlanted(self):
        return self.tickPlanted

    def setTickPlanted(self, tickPlanted):
        self.tickPlanted = tickPlanted
