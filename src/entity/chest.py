from entity.drawableEntity import DrawableEntity
from entity.storableInventory import StorableInventory


# @author Claude
# @since June 12th, 2026
class Chest(DrawableEntity, StorableInventory):
    def __init__(self):
        DrawableEntity.__init__(self, "Chest", "assets/images/chest.png", True)
        StorableInventory.__init__(self)
