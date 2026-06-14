import random
from entity.living.chicken import Chicken
from entity.living.deer import Deer
from entity.living.livingEntity import LivingEntity
from entity.living.rabbit import Rabbit
from player.player import Player


# A forest predator. Hunts the smaller grazers and the player.
class Wolf(LivingEntity):
    def __init__(self, tickCreated):
        LivingEntity.__init__(
            self,
            "Wolf",
            "assets/images/wolf.png",
            random.randrange(20, 30),
            [Chicken, Rabbit, Deer, Player],
            tickCreated,
        )
