from entity.drawableEntity import DrawableEntity


# @author Copilot
# Client-side representation of Deer entity
class Deer(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Deer", "assets/images/deer.png")
        self.solid = False

    def isSolid(self):
        return self.solid
