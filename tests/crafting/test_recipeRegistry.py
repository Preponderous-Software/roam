from src.crafting.recipeRegistry import RecipeRegistry
from entity.coalOre import CoalOre
from entity.stone import Stone
from entity.wood import Wood


def test_recipeRegistry_has_wood_floor_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    woodFloorRecipes = [r for r in recipes if r.getName() == "Wood Floor"]
    assert len(woodFloorRecipes) == 1
    recipe = woodFloorRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Wood: 4}


def test_recipeRegistry_has_bed_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    bedRecipes = [r for r in recipes if r.getName() == "Bed"]
    assert len(bedRecipes) == 1
    recipe = bedRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Wood: 3, Stone: 2}


def test_recipeRegistry_has_stone_floor_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    stoneFloorRecipes = [r for r in recipes if r.getName() == "Stone Floor"]
    assert len(stoneFloorRecipes) == 1
    recipe = stoneFloorRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Stone: 4}


def test_recipeRegistry_has_stone_bed_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    stoneBedRecipes = [r for r in recipes if r.getName() == "Stone Bed"]
    assert len(stoneBedRecipes) == 1
    recipe = stoneBedRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Stone: 3, Wood: 2}


def test_recipeRegistry_has_fence_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    fenceRecipes = [r for r in recipes if r.getName() == "Fence"]
    assert len(fenceRecipes) == 1
    recipe = fenceRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Wood: 3}


def test_recipeRegistry_has_campfire_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    campfireRecipes = [r for r in recipes if r.getName() == "Campfire"]
    assert len(campfireRecipes) == 1
    recipe = campfireRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Wood: 2, CoalOre: 1}


def test_recipeRegistry_has_chest_recipe():
    registry = RecipeRegistry()
    recipes = registry.getRecipes()
    chestRecipes = [r for r in recipes if r.getName() == "Chest"]
    assert len(chestRecipes) == 1
    recipe = chestRecipes[0]
    ingredients = recipe.getIngredients()
    assert ingredients == {Wood: 6}
