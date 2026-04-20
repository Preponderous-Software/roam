from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class OakWood(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(self, "Oak Wood", "assets/images/oakWood.png", True)
