from entity.drawableEntity import DrawableEntity
from entity.storableInventory import StorableInventory


# @author Copilot
# @since April 21st, 2026
class Gravestone(DrawableEntity, StorableInventory):
    def __init__(self):
        DrawableEntity.__init__(self, "Gravestone", "assets/images/gravestone.png", True)
        StorableInventory.__init__(self)
