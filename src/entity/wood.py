from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# Generic wood entity for server-backed architecture
class Wood(DrawableEntity):
    def __init__(self):
        # Use oak wood image as generic wood
        DrawableEntity.__init__(self, "Wood", "assets/images/oakWood.png")
        self.solid = True

    def isSolid(self):
        return self.solid
