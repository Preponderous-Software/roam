from src.crafting.recipeRegistry import RecipeRegistry


def test_recipeRegistry_has_torch_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    torchRecipes = [r for r in recipes if r.getName() == "Torch"]
    assert len(torchRecipes) == 1
    recipe = torchRecipes[0]
    ingredients = recipe.getIngredients()
    ingredientNames = {cls.__name__: count for cls, count in ingredients.items()}
    assert ingredientNames == {"OakWood": 1, "CoalOre": 1}
    assert recipe.getResultCount() == 2
