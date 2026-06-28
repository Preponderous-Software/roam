from entity.drawableEntity import DrawableEntity


class CaveEntrance(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(
            self, "Cave Entrance", "assets/images/caveEntrance.png", True
        )
