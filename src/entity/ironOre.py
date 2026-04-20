from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# @since August 18th, 2022
class IronOre(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Iron Ore", "assets/images/ironOre.png", True)
