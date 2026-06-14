import random
from entity.grass import Grass
from entity.living.livingEntity import LivingEntity


# A small, timid grassland herbivore. Grazes on grass like the chicken.
class Rabbit(LivingEntity):
    def __init__(self, tickCreated):
        LivingEntity.__init__(
            self,
            "Rabbit",
            "assets/images/rabbit.png",
            random.randrange(20, 30),
            [Grass],
            tickCreated,
        )
