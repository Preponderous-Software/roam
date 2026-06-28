from entity.drawableEntity import DrawableEntity


class CaveFloor(DrawableEntity):
    def __init__(self):
        DrawableEntity.__init__(
            self, "Cave Floor", "assets/images/caveFloor.png", False
        )
