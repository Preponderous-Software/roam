from entity.drawableEntity import DrawableEntity


class CaveLadder(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Ladder", "assets/images/caveLadder.png", True)
