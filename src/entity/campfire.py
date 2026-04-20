from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 14th, 2026
class Campfire(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Campfire", "assets/images/campfire.png")
        self.solid = False
        self.lightRadius = 8

    def isSolid(self):
        return self.solid

    def getLightRadius(self):
        return self.lightRadius
