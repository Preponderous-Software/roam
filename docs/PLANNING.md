# Planning Document
This document provides an overview of Roam's gameplay mechanics and features.

## Overview
Roam is a 2D survival game where the player explores a procedurally-generated world and interacts with their surroundings.

## Architecture
Roam uses a client-server architecture:
- **Server (Java/Spring Boot)**: Manages game state, business logic, provides REST API and WebSocket updates
- **Client (Python/Pygame)**: Handles UI rendering, user input, and communicates with server

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## Mechanics

### Authentication
Players must register and login to play. Authentication uses JWT tokens for secure session management.

### Energy
Energy decreases when the player moves and replenishes when the player eats food. Different movement speeds (walking, running, crouching) consume energy at different rates.

### Map Generation
The map is procedurally generated using simplex noise based on a configurable seed. Different biomes (grass, forest, jungle, desert, mountain, snow) are generated based on noise values and temperature/moisture parameters.

### Inventory
The player has an inventory that can hold items with a hotbar for quick access. The player can:
- Open/close the inventory with the `I` key
- Select hotbar slots with number keys (1-0)
- Move items between slots
- Place items from hotbar into the world

### Crafting
Not yet implemented. Planned feature for combining items to create new items.

### Food
The player can eat food to replenish energy. Food items include:
- Berries
- Apples
- Chicken meat
Food consumption is automatic when energy drops below certain thresholds.

### Stats Tracking
The game tracks player statistics including:
- Kills (animals defeated)
- Deaths (player deaths)
- Items gathered (resources collected)
- Items placed (objects placed in world)

Stats are persisted in the database and viewable in the stats screen.

## World

### Room Types / Biomes
- Grass (temperate, moderate resources)
- Forest (trees, wood resources, animals)
- Jungle (dense vegetation, high moisture)
- Desert (sparse resources, low moisture)
- Mountain (stone, ore resources, high elevation)
- Snow (cold climate, limited resources)

### Resources
- Oak Wood (from trees)
- Stone (from rocks)
- Coal Ore (from mining)
- Berries (foraged from bushes)
- Apples (from apple trees)

## Entities

### Wildlife
- Chicken (peaceful, drops chicken meat)
- Deer (peaceful, fast moving)
- Bear (aggressive, high energy)

### Interactive Objects
- Trees (gather wood)
- Rocks (gather stone)
- Berry bushes (gather berries)
- Apple trees (gather apples)

All entities are server-managed with collision detection and energy/health systems.