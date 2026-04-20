from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 14th, 2026
class Fence(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Fence", "assets/images/fence.png", True)
