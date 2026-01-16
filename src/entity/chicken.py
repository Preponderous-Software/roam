from entity.drawableEntity import DrawableEntity


# @author Copilot
# Client-side representation of Chicken entity
class Chicken(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Chicken", "assets/images/chicken.png")
        self.solid = False

    def isSolid(self):
        return self.solid
