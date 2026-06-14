import random
from entity.grass import Grass
from entity.living.livingEntity import LivingEntity


# A forest herbivore that grazes on grass.
class Deer(LivingEntity):
    def __init__(self, tickCreated):
        LivingEntity.__init__(
            self,
            "Deer",
            "assets/images/deer.png",
            random.randrange(20, 30),
            [Grass],
            tickCreated,
        )
