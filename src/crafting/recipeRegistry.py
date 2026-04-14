from crafting.recipe import Recipe
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.woodFloor import WoodFloor
from entity.bed import Bed


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

    def getRecipes(self):
        return self.recipes
