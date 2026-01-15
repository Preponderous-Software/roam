from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# Generic wood entity for server-backed architecture
class Wood(DrawableEntity):
    def __init__(self):
        # Use oak wood image as generic wood placeholder.
        # Note: This is a generic "Wood" entity distinct from the specific "Oak Wood" entity.
        # Both temporarily share the same sprite (see WI-008 in WORK_ITEMS.md).
        DrawableEntity.__init__(self, "Wood", "assets/images/oakWood.png")
        self.solid = True

    def isSolid(self):
        return self.solid
