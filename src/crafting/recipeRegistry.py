from crafting.recipe import Recipe
from entity.bed import Bed
from entity.campfire import Campfire
from entity.coalOre import CoalOre
from entity.fence import Fence
from entity.grass import Grass
from entity.jungleWood import JungleWood
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.wheatSeed import WheatSeed
from entity.woodFloor import WoodFloor


# @author Copilot
# @since April 14th, 2026
class RecipeRegistry:
    def __init__(self):
        self.recipes = []
        self.recipes.append(
            Recipe(
                "Wood Floor",
                {OakWood: 4},
                WoodFloor,
                "assets/images/woodFloor.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Bed",
                {OakWood: 3, Stone: 2},
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
                {Stone: 3, OakWood: 2},
                StoneBed,
                "assets/images/stoneBed.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Fence",
                {JungleWood: 3},
                Fence,
                "assets/images/fence.png",
            )
        )
        self.recipes.append(
            Recipe(
                "Campfire",
                {OakWood: 2, CoalOre: 1},
                Campfire,
                "assets/images/campfire.png",
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

    def getRecipes(self):
        return self.recipes
