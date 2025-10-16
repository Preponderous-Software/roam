# Architecture Documentation: UI and Gameplay Separation

## Overview
This document describes the architectural improvements made to decouple the user interface from gameplay logic in the Roam game.

## Problem Statement
Previously, both `WorldScreen` (pygame UI) and `TextWorldScreen` (text UI) contained duplicate gameplay logic:
- Player movement
- Resource gathering and placing
- Save/load functionality
- Room transitions
- Player death and respawn

This tight coupling made it difficult to:
- Maintain consistent gameplay across different UIs
- Add new UI implementations
- Modify gameplay without touching UI code
- Test gameplay logic independently

## Solution: WorldController

### Architecture
We introduced a `WorldController` class that encapsulates all gameplay logic, creating a clean separation:

```
┌─────────────────────────────────────────────────┐
│                Application Layer                 │
│  (roam.py - Entry point, arg parsing)           │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐    ┌──────▼───────────┐
│  WorldScreen   │    │ TextWorldScreen  │
│  (pygame UI)   │    │  (text UI)       │
└───────┬────────┘    └──────┬───────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │   WorldController   │
        │  (Gameplay Logic)   │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐    ┌──────▼───────┐
│   Game State   │    │  Persistence │
│  (Map, Player, │    │  (Save/Load) │
│   Entities)    │    │              │
└────────────────┘    └──────────────┘
```

### WorldController Responsibilities

The `WorldController` class (`src/world/worldController.py`) handles:

1. **Game State Management**
   - World initialization
   - Current room tracking
   - Player reference management

2. **Gameplay Actions**
   - `movePlayer(direction)` - Handle player movement and room transitions
   - `gatherAtPlayerLocation()` - Pick up items at player's location
   - `placeAtPlayerLocation()` - Place items from inventory
   - `checkForPlayerDeath()` - Death detection
   - `respawnPlayer()` - Player respawn logic

3. **Persistence**
   - `save()` - Save game state
   - `load*FromFile()` - Load various game components
   - `save*ToFile()` - Save various game components

4. **World Updates**
   - `updateWorld()` - Update entity AI, reproduction, energy depletion

### UI Screen Responsibilities

UI screens (both pygame and text) now focus solely on:

1. **Input Handling**
   - Capture user input (keyboard, mouse, etc.)
   - Translate input to gameplay actions
   - Call appropriate WorldController methods

2. **Rendering**
   - Display current game state
   - Show player status, inventory, etc.
   - Handle UI-specific features (animations, effects, etc.)

3. **Screen Management**
   - Handle screen transitions (menu, options, etc.)
   - Manage UI state and layout

### Benefits

1. **Code Reduction**
   - TextWorldScreen: 469 → 177 lines (62% reduction)
   - Eliminated ~300 lines of duplicate code

2. **Maintainability**
   - Gameplay changes only need to be made once in WorldController
   - UI implementations don't need to understand gameplay mechanics
   - Clear separation of concerns

3. **Testability**
   - Gameplay logic can be tested without UI
   - UI can be tested with mock controllers
   - Independent testing of each layer

4. **Extensibility**
   - New UI implementations (web, mobile, VR) can easily be added
   - Only need to implement input handling and rendering
   - All gameplay logic automatically available

## Usage Example

### Before (Tightly Coupled)
```python
class TextWorldScreen:
    def handleInput(self, key):
        if key == 'w':
            # Duplicate movement logic
            location = self.getLocationOfPlayer()
            grid = self.currentRoom.getGrid()
            newLocation = grid.getUp(location)
            if newLocation != -1:
                self.currentRoom.removeEntity(self.player)
                self.currentRoom.addEntityToLocation(self.player, newLocation)
                # ... more logic
```

### After (Decoupled)
```python
class TextWorldScreen:
    def handleInput(self, key):
        if key == 'w':
            # Delegate to controller
            self.worldController.movePlayer(0)  # up
```

## Future Enhancements

With this architecture, future improvements become easier:

1. **New UI Implementations**
   - Web-based UI using WebSockets
   - Mobile touch interface
   - VR/AR interface
   - Voice-controlled interface

2. **Gameplay Modifications**
   - Add multiplayer support (multiple controllers)
   - Implement save states/snapshots
   - Add replay functionality
   - Implement AI for player simulation

3. **Testing & Development**
   - Automated gameplay testing
   - Headless server mode
   - Gameplay simulation for balancing

## Migration Guide

To add a new UI implementation:

1. Create a new screen class (e.g., `WebWorldScreen`)
2. Initialize a `WorldController` instance
3. Implement input handling that calls controller methods
4. Implement rendering using controller's `get*()` methods
5. No gameplay logic needed!

Example:
```python
class WebWorldScreen:
    def __init__(self, config, tickCounter, stats, player):
        self.worldController = WorldController(config, tickCounter, stats, player)
        
    def handleWebSocketMessage(self, message):
        if message['action'] == 'move':
            self.worldController.movePlayer(message['direction'])
        elif message['action'] == 'gather':
            success, msg, item = self.worldController.gatherAtPlayerLocation()
            self.sendWebSocketMessage({'status': msg})
```

## Conclusion

The WorldController abstraction provides a clean separation between UI and gameplay, making the codebase more maintainable, testable, and extensible. This architecture enables easy addition of new UI implementations while ensuring consistent gameplay across all interfaces.
