from entity.wood import Wood


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class JungleWood(Wood):
    def __init__(self):
        Wood.__init__(self, "Jungle Wood", "assets/images/jungleWood.png", True)
