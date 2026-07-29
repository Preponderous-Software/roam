from entity.drawableEntity import DrawableEntity
from entity.torch import Torch


# @author Claude
# @since July 26th, 2026
class GoldenLantern(Torch):
    """A Torch variant crafted from Gold Ore with a larger light radius.

    Subclasses Torch so worldScreen's generic hasattr(entity, "getLightRadius")
    lighting logic picks it up without any additional wiring.
    """

    def __init__(self):
        DrawableEntity.__init__(
            self, "Golden Lantern", "assets/images/goldenLantern.png"
        )
        self.lightRadius = 10
