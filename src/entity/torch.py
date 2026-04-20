from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 20th, 2026
class Torch(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Torch", "assets/images/torch.png")
        self.solid = False
        self.lightRadius = 3

    def isSolid(self):
        return self.solid

    def getLightRadius(self):
        return self.lightRadius
