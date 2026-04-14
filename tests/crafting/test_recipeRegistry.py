from src.crafting.recipeRegistry import RecipeRegistry


def test_recipeRegistry_has_wood_floor_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    woodFloorRecipes = [r for r in recipes if r.getName() == "Wood Floor"]
    assert len(woodFloorRecipes) == 1
    recipe = woodFloorRecipes[0]
    ingredients = recipe.getIngredients()
    ingredientNames = {cls.__name__: count for cls, count in ingredients.items()}
    assert ingredientNames == {"OakWood": 4}


def test_recipeRegistry_has_bed_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    bedRecipes = [r for r in recipes if r.getName() == "Bed"]
    assert len(bedRecipes) == 1
    recipe = bedRecipes[0]
    ingredients = recipe.getIngredients()
    ingredientNames = {cls.__name__: count for cls, count in ingredients.items()}
    assert ingredientNames == {"OakWood": 3, "Stone": 2}
