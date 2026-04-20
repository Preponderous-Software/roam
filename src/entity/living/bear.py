import random
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from player.player import Player


# @author Daniel McCoy Stephenson
# @since December 24th, 2022
class Bear(LivingEntity):
    def __init__(self, tickCreated):
        LivingEntity.__init__(
            self,
            "Bear",
            "assets/images/bear.png",
            random.randrange(20, 30),
            [Chicken, Player],
            tickCreated,
        )
