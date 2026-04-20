from src.crafting.recipeRegistry import RecipeRegistry


def test_recipeRegistry_has_wheat_seed_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    wheatSeedRecipes = [r for r in recipes if r.getName() == "Wheat Seed"]
    assert len(wheatSeedRecipes) == 1
    recipe = wheatSeedRecipes[0]
    ingredients = recipe.getIngredients()
    ingredientNames = {cls.__name__: count for cls, count in ingredients.items()}
    assert ingredientNames == {"Grass": 1}
    assert recipe.getResultCount() == 3
