from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# @since August 18th, 2022
class CoalOre(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Coal Ore", "assets/images/coalOre.png", True)
