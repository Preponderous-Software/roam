from entity.apple import Apple
from entity.banana import Banana
from entity.bearMeat import BearMeat
from entity.bed import Bed
from entity.campfire import Campfire
from entity.chickenMeat import ChickenMeat
from entity.coalOre import CoalOre
from entity.fence import Fence
from entity.grass import Grass
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.leaves import Leaves
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.matureCrop import MatureCrop
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.torch import Torch
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
from entity.woodFloor import WoodFloor
from entity.youngCrop import YoungCrop

PICKUPABLE_TYPES = (
    OakWood,
    JungleWood,
    Leaves,
    Grass,
    Apple,
    Stone,
    CoalOre,
    IronOre,
    Chicken,
    Bear,
    Banana,
    ChickenMeat,
    BearMeat,
    WoodFloor,
    Bed,
    StoneFloor,
    StoneBed,
    Fence,
    Campfire,
    Torch,
    WheatSeed,
    YoungCrop,
    MatureCrop,
    Wheat,
)


def canBePickedUp(entity):
    return isinstance(entity, PICKUPABLE_TYPES)
