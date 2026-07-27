from crafting.recipe import Recipe
from entity.bed import Bed
from entity.campfire import Campfire
from entity.chest import Chest
from entity.coalOre import CoalOre
from entity.fence import Fence
from entity.goldenLantern import GoldenLantern
from entity.goldOre import GoldOre
from entity.grass import Grass
from entity.ironChest import IronChest
from entity.ironOre import IronOre
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.torch import Torch
from entity.wheatSeed import WheatSeed
from entity.wood import Wood
from entity.woodFloor import WoodFloor


# @author Copilot
# @since April 14th, 2026
class RecipeRegistry:
    def __init__(self):
        self.recipes = []
        self.recipes.append(
            Recipe(
                "Wood Floor",
                {Wood: 4},
                WoodFloor,
                "assets/images/woodFloor.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Bed",
                {Wood: 3, Stone: 2},
                Bed,
                "assets/images/bed.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Stone Floor",
                {Stone: 4},
                StoneFloor,
                "assets/images/stoneFloor.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Stone Bed",
                {Stone: 3, Wood: 2},
                StoneBed,
                "assets/images/stoneBed.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Fence",
                {Wood: 3},
                Fence,
                "assets/images/fence.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Campfire",
                {Wood: 2, CoalOre: 1},
                Campfire,
                "assets/images/campfire.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Chest",
                {Wood: 6},
                Chest,
                "assets/images/chest.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Wheat Seed",
                {Grass: 1},
                WheatSeed,
                "assets/images/wheatSeed.png",
                3,
            )
        )
        self.recipes.append(
            Recipe(
                "Torch",
                {Wood: 1, CoalOre: 1},
                Torch,
                "assets/images/torch.png",
                2,
            )
        )
        self.recipes.append(
            Recipe(
                "Iron Chest",
                {Wood: 4, IronOre: 3},
                IronChest,
                "assets/images/ironChest.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Golden Lantern",
                {Wood: 1, GoldOre: 2},
                GoldenLantern,
                "assets/images/goldenLantern.png",
            )
        )

    def getRecipes(self):
        return self.recipes
