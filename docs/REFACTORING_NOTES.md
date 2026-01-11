# Roam.py Client Refactoring - Server-Backed Architecture

## Overview

The original `roam.py` client has been refactored to use a server-backed architecture, eliminating all local business logic and communicating exclusively with the Spring Boot server via REST APIs.

## Changes Made

### 1. Core Architecture Changes

#### `src/roam.py`
- **Added**: `RoamAPIClient` integration for server communication
- **Added**: Server URL configuration (default: `http://localhost:8080`, can be passed as command-line argument)
- **Added**: Session management (initialization, cleanup on exit)
- **Modified**: Player initialization now fetches state from server instead of creating locally
- **Modified**: Window title now indicates "Server-Backed" mode
- **Modified**: Screens are initialized after server session is established

**Key Changes:**
```python
# Before: Local player creation
self.player = Player(self.tickCounter.getTick())

# After: Server-backed player
self.api_client = RoamAPIClient(server_url)
session_data = self.api_client.init_session()
self.player = Player(self.tickCounter.getTick())
self._updatePlayerFromServerData(session_data['player'])
```

#### `src/screen/serverBackedWorldScreen.py` (NEW FILE)
- **Created**: New simplified world screen that uses server for all game logic
- **Removed**: Local world generation (Map, Room, procedural generation)
- **Removed**: Local entity management (spawning, gathering, placing)
- **Removed**: Local AI for living entities
- **Removed**: Room persistence and transitions

**Server Communication:**
- Player movement → `POST /api/v1/session/{id}/player/action` with action="move"
- Stopping → `POST /api/v1/session/{id}/player/action` with action="stop"
- Gathering → `POST /api/v1/session/{id}/player/action` with action="gather"
- Adding items → `POST /api/v1/session/{id}/inventory/add`
- Consuming food → `POST /api/v1/session/{id}/player/action` with action="consume"
- Tick updates → `POST /api/v1/session/{id}/tick`

### 2. Business Logic Elimination

All of the following logic has been **removed** from the client and delegated to the server:

1. **World Generation**
   - Procedural room generation
   - Entity spawning
   - Biome determination
   
2. **Entity Management**
   - Entity placement and removal
   - Entity collision detection
   - Entity state management
   
3. **Game Mechanics**
   - Movement validation
   - Energy consumption calculation
   - Food consumption logic
   - Inventory slot management
   - Gathering/placing mechanics
   
4. **Living Entity AI**
   - Animal movement
   - Animal reproduction
   - Animal death
   
5. **World Persistence**
   - Room saving/loading
   - Player location persistence
   - Entity state persistence

### 3. Visual Rendering (Maintained)

The following UI elements have been **maintained** or **adapted**:

- ✅ Main menu screen
- ✅ Options screen
- ✅ Stats screen
- ✅ Inventory screen
- ✅ Config screen
- ✅ Status bar at bottom
- ✅ Energy bar visualization
- ✅ Player visualization (simplified - centered player representation)
- ✅ Inventory preview (bottom hotbar)
- ✅ Controls help text
- ✅ Debug information (when enabled)

**Simplified Rendering:**
- No complex world grid with entities
- Simple centered player representation with direction indicator
- Information panels showing server state
- Inventory slots showing server inventory data

### 4. API Integration

All game state mutations now go through REST APIs:

| Action | Endpoint | Method |
|--------|----------|--------|
| Start session | `/api/v1/session/init` | POST |
| Get player state | `/api/v1/session/{id}/player` | GET |
| Move player | `/api/v1/session/{id}/player/action` | POST |
| Update energy | `/api/v1/session/{id}/player/energy` | PUT |
| Get inventory | `/api/v1/session/{id}/inventory` | GET |
| Add item | `/api/v1/session/{id}/inventory/add` | POST |
| Remove item | `/api/v1/session/{id}/inventory/remove` | POST |
| Update tick | `/api/v1/session/{id}/tick` | POST |
| End session | `/api/v1/session/{id}` | DELETE |

## Usage

### Running the Refactored Client

1. **Start the Spring Boot server:**
   ```bash
   cd server
   mvn spring-boot:run
   ```

2. **Run the client:**
   ```bash
   cd src
   python3 roam.py [server_url]
   ```
   
   Example with custom server:
   ```bash
   python3 roam.py http://localhost:8080
   ```

### Controls

The following controls are supported:

| Key | Action |
|-----|--------|
| W/↑ | Move up |
| A/← | Move left |
| S/↓ | Move down |
| D/→ | Move right |
| Space | Stop movement |
| G | Toggle gathering |
| I | Open inventory |
| E | Consume food |
| 1/2/3 | Add test items (apple/banana/stone) |
| Shift | Run (speed modifier) |
| Ctrl | Crouch |
| F3 | Toggle debug info |
| ESC | Open menu |

## Limitations

Due to the current server API capabilities, the following features are **not yet available**:

1. **No World Generation**: The server doesn't generate rooms or worlds yet
2. **No Entity System**: No trees, rocks, animals, or interactive entities
3. **No Room Transitions**: Can't move between rooms
4. **No Entity Gathering**: Can't pick up entities from the world
5. **No Entity Placing**: Can't place entities in the world
6. **Simplified Inventory**: Server inventory is basic (item names and counts only)
7. **No Minimap**: No world map visualization
8. **No Save/Load**: No game state persistence
9. **No Living Entities**: No animals with AI behaviors

These features will be added in **Phase 4** of the architecture migration (server-side world generation).

## Benefits of Server-Backed Architecture

1. ✅ **Separation of Concerns**: UI completely separated from game logic
2. ✅ **No Client-Side Cheating**: All game state is authoritative on server
3. ✅ **Scalability**: Server can handle multiple clients
4. ✅ **Maintainability**: Business logic changes don't affect UI
5. ✅ **Testability**: Server logic can be tested independently
6. ✅ **Future Multiplayer**: Foundation for multiplayer support

## Migration Phases

According to the architecture plan:

- ✅ **Phase 1**: Server infrastructure and core API
- ✅ **Phase 2**: Refactor Python client to use API (THIS PHASE)
- 🔜 **Phase 3**: Add persistence layer
- 🔜 **Phase 4**: Add world generation on server
- 🔜 **Phase 5**: Add multiplayer support

## Testing

To test the refactored client:

1. Ensure the Spring Boot server is running
2. Run the client: `python3 roam.py`
3. Select "Start Game" from main menu
4. Verify:
   - Connection to server succeeds
   - Player info displays correctly
   - Movement keys send actions to server
   - Inventory shows server data
   - Energy updates from server
   - Session ends cleanly on exit

## Code Quality

- ✅ All code follows existing Python conventions
- ✅ Docstrings added for new classes and methods
- ✅ Error handling for network failures
- ✅ Clean separation between rendering and state management
- ✅ No syntax errors (validated with AST parser)

## Next Steps

To fully complete the server-backed client vision:

1. Add server endpoints for world generation
2. Add server endpoints for entity management
3. Add server endpoints for room transitions
4. Enhance rendering to display server world state
5. Add persistence layer on server
6. Add save/load functionality
