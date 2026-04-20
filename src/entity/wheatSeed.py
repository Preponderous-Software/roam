from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 20th, 2026
class WheatSeed(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Wheat Seed", "assets/images/wheatSeed.png")
        self.solid = False

    def isSolid(self):
        return self.solid
