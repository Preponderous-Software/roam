from src.crafting.recipeRegistry import RecipeRegistry
from entity.coalOre import CoalOre
from entity.wood import Wood


def test_recipeRegistry_has_torch_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    torchRecipes = [r for r in recipes if r.getName() == "Torch"]
    assert len(torchRecipes) == 1
    recipe = torchRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Wood: 1, CoalOre: 1}
    assert recipe.getResultCount() == 2
