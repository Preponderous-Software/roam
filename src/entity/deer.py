from entity.drawableEntity import DrawableEntity


# @author Copilot
# Client-side representation of Deer entity
# Note: Using chicken.png as placeholder - deer.png doesn't exist yet
class Deer(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Deer", "assets/images/chicken.png")
        self.solid = False

    def isSolid(self):
        return self.solid
