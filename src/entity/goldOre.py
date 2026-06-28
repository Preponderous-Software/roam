from entity.drawableEntity import DrawableEntity


class GoldOre(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Gold Ore", "assets/images/goldOre.png", True)
