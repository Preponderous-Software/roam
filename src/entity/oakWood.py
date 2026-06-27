from entity.wood import Wood


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class OakWood(Wood):
    def __init__(self):
        Wood.__init__(self, "Oak Wood", "assets/images/oakWood.png", True)
