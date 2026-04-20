from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 14th, 2026
class StoneFloor(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Stone Floor", "assets/images/stoneFloor.png")
