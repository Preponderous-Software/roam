import random
from entity.grass import Grass
from entity.living.livingEntity import LivingEntity


# @author Daniel McCoy Stephenson
# @since July 7th, 2022
class Chicken(LivingEntity):
    def __init__(self, tickCreated):
        LivingEntity.__init__(
            self,
            "Chicken",
            "assets/images/chicken.png",
            random.randrange(20, 30),
            [Grass],
            tickCreated,
        )
