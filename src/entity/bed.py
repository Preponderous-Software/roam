from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 14th, 2026
class Bed(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Bed", "assets/images/bed.png", True)
