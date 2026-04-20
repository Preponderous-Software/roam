from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 14th, 2026
class StoneBed(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Stone Bed", "assets/images/stoneBed.png", True)
