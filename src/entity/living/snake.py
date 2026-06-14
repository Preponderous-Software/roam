import random
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from entity.living.rabbit import Rabbit


# A jungle predator that preys on the smaller grazers.
class Snake(LivingEntity):
    def __init__(self, tickCreated):
        LivingEntity.__init__(
            self,
            "Snake",
            "assets/images/snake.png",
            random.randrange(20, 30),
            [Chicken, Rabbit],
            tickCreated,
        )
