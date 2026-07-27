from entity.chest import Chest
from entity.drawableEntity import DrawableEntity
from entity.storableInventory import StorableInventory


# @author Claude
# @since July 26th, 2026
class IronChest(Chest):
    """A Chest variant crafted from Iron Ore.

    Subclasses Chest (rather than duplicating it) so every place that gates
    chest-opening/pickup behavior on isinstance(entity, Chest) — worldScreen's
    gather/open logic and pickupableEntities' empty-only pickup rule — covers
    this entity for free.
    """

    def __init__(self):
        DrawableEntity.__init__(self, "Iron Chest", "assets/images/ironChest.png", True)
        StorableInventory.__init__(self)
