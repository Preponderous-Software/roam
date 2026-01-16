from entity.drawableEntity import DrawableEntity


# @author Copilot
# Client-side representation of Bear entity
class Bear(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Bear", "assets/images/bear.png")
        self.solid = False

    def isSolid(self):
        return self.solid
