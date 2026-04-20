from entity.drawableEntity import DrawableEntity


# @author Copilot
# @since April 20th, 2026
class Torch(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Torch", "assets/images/torch.png")
        self.lightRadius = 6

    def getLightRadius(self):
        return self.lightRadius
