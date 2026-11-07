# Planning Document
This document is a work in progress. It is a place to collect ideas and plan out the development of the game.

## Overview
Roam is a **single-player** 2D survival game where the player explores a procedurally-generated world and interacts with their surroundings. There are currently no plans to add multiplayer.

## Mechanics
### Energy
Energy decreases when the player moves and replenishes when the player eats food.

### Map Generation
The map is generated as the player explores.

### Inventory
The player has an inventory that can hold items. The player can open/close the inventory with the `i` key.

### Crafting
The player can craft items using the items in their inventory. Crafting is implemented via the `Recipe` and `RecipeRegistry` classes (`src/crafting/`). The current recipes are: Wood Floor, Bed, Stone Floor, Stone Bed, Fence, Campfire, Chest, Wheat Seed, Torch, Iron Chest, and Golden Lantern.

### Food
The player can eat food to replenish energy. Food can be found in the world or grown by the player.

## Room Types
Defined by `RoomType` in `src/world/roomType.py`:
- Empty
- Grassland
- Forest
- Jungle
- Mountain
- Cave (generated below ground level by `roomFactory`, reached through a cave entrance)

## Mobs
Living entities are registered in `src/entity/living/livingEntityRegistry.py`:
- Chicken
- Bear
- Rabbit
- Deer
- Wolf
- Snake