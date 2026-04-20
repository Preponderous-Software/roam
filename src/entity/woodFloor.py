from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 14th, 2026
class WoodFloor(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Wood Floor", "assets/images/woodFloor.png")
