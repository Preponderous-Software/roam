# Server-Backed Client Implementation

This document describes the new server-backed Python client application created for the Roam game.

## Overview

A complete Python client application (`client/roam_client.py`) has been implemented that demonstrates the client-server architecture. The client uses pygame for UI rendering and communicates exclusively with the Spring Boot backend for all game logic.

## Location

```
/client/
├── __init__.py
├── README.md
├── roam_client.py      # Main client application
├── run_client.sh       # Shell script to start client
└── test_client.py      # API communication test script
```

## Architecture

### Client Responsibilities (UI Only)

The client handles **only presentation** and user input:

- **Display Rendering**:
  - Player status (energy, direction, movement state)
  - Inventory display
  - Controls reference
  - Server connection status
  - Status messages

- **Input Handling**:
  - Keyboard input (WASD/arrows for movement)
  - Action keys (gather, consume, etc.)
  - Translates user input to API calls

- **State Display**:
  - Shows server-provided state
  - No local game logic or state mutations

### Server Responsibilities (All Business Logic)

The server handles **all game logic**:

- Player state management
- Inventory operations
- Energy calculations
- Movement validation
- Game tick progression
- State persistence (per session)

## Key Features

### 1. Session Management

```python
# Initialize session on server
session_data = self.api_client.init_session()
self.session_id = session_data['sessionId']
```

Each client creates a unique session on the server. Sessions are independent and can coexist.

### 2. Player Actions

All player actions are sent to the server:

```python
# Move player
self.api_client.perform_player_action("move", direction=0)

# Toggle gathering
self.api_client.perform_player_action("gather", gathering=True)

# Consume food
self.api_client.perform_player_action("consume", item_name="apple")
```

### 3. Inventory Management

```python
# Add item
self.api_client.add_item_to_inventory("apple")

# Get inventory state
inventory = self.api_client.get_inventory()

# Items are removed via consume action
```

### 4. Energy System

```python
# Update energy
self.api_client.update_player_energy(10, "add")
self.api_client.update_player_energy(5, "remove")

# Energy restored when consuming food
player = self.api_client.perform_player_action("consume", item_name="apple")
```

### 5. Real-Time Synchronization

- Client updates server tick every 60 frames
- Player state refreshed after each action
- UI reflects server state immediately

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move player (up/left/down/right) |
| Space | Stop movement |
| G | Toggle gathering |
| 1, 2, 3 | Add test items (apple/banana/stone) |
| E | Consume first food item |
| ESC | Quit application |

## UI Components

### Main Display

1. **Title Bar**: Shows application name and server URL
2. **Session Info**: Displays session ID and current game tick
3. **Player Status**: Shows energy (with visual bar), direction, and state flags
4. **Inventory**: Lists items with quantities
5. **Controls**: Reference guide for keyboard controls
6. **Status Bar**: Shows recent actions and messages

### Visual Elements

- **Energy Bar**: Visual representation of player energy (0-100)
- **Color Coding**: Different colors for different UI sections
- **Real-time Updates**: UI updates every frame (60 FPS)

## Code Structure

### RoamClient Class

```python
class RoamClient:
    def __init__(self, config, server_url):
        # Initialize pygame, API client, UI components
        
    def start_session(self):
        # Create session on server
        
    def handle_input(self):
        # Process keyboard input, send to server
        
    def render(self):
        # Draw UI based on server state
        
    def run(self):
        # Main game loop
```

### Key Methods

- `start_session()`: Initializes game session with server
- `update_local_state_from_player_data()`: Syncs local display with server state
- `move_player()`, `stop_player()`, `toggle_gathering()`: Player actions
- `add_item()`, `consume_food()`: Inventory operations
- `update_tick()`: Advance game tick on server
- `render()`: Draw UI elements

## API Usage

The client uses `RoamAPIClient` from `src/client/api_client.py`:

```python
from client.api_client import RoamAPIClient

client = RoamAPIClient("http://localhost:8080")

# Session management
session = client.init_session()
client.delete_session()

# Player operations
player = client.get_player()
player = client.perform_player_action("move", direction=0)

# Inventory operations
inventory = client.get_inventory()
client.add_item_to_inventory("apple")
```

## Running the Client

### Prerequisites

1. Spring Boot server running on `http://localhost:8080`
2. Python 3.8+ with required packages:
   - pygame
   - requests

### Start Client

```bash
cd client
python3 roam_client.py
```

Or with custom server URL:

```bash
python3 roam_client.py http://localhost:8080
```

Or using the shell script:

```bash
./run_client.sh
```

## Testing

A test script (`test_client.py`) validates API communication without pygame:

```bash
cd client
python3 test_client.py
```

Tests cover:
- Session initialization
- Player state retrieval
- Movement actions
- Inventory operations
- Food consumption
- Energy management
- Session cleanup

## Differences from Original Client

| Aspect | Original Client | New Server-Backed Client |
|--------|----------------|-------------------------|
| **Game Logic** | Embedded in Python | All on Spring Boot server |
| **State Storage** | Local Python objects | Server-side sessions |
| **World Generation** | Python procedural generation | (Future: server-side) |
| **Persistence** | Local file save/load | Server manages sessions |
| **Architecture** | Monolithic | Client-server |
| **UI Focus** | Game + UI mixed | Pure UI layer |
| **Scalability** | Single instance | Multi-client capable |

## Benefits

1. **Separation of Concerns**: UI completely decoupled from game logic
2. **Server Authority**: Server validates all actions, prevents cheating
3. **Scalability**: Multiple clients can connect to same server
4. **Testability**: Server logic testable without UI
5. **Flexibility**: Easy to create alternative clients (web, mobile, CLI)
6. **Maintainability**: Changes to game rules don't affect client code

## Future Enhancements

The current client demonstrates core architecture. Future additions could include:

- **World Rendering**: Display server-provided world/room state
- **Multi-Player**: Show other players in same session
- **Advanced UI**: Menus, maps, more sophisticated graphics
- **WebSocket Support**: Real-time push updates from server
- **Touch Controls**: Mobile client support
- **3D Rendering**: Upgrade to 3D graphics
- **Sound Effects**: Audio feedback for actions

## Development Notes

### Design Decisions

1. **Stateless Client**: Client maintains only ephemeral display state
2. **API-First**: All actions go through REST API
3. **Error Handling**: Graceful degradation when server unavailable
4. **Frame Rate**: 60 FPS for smooth UI
5. **Tick Frequency**: Server tick updated every 60 frames (1 per second)

### Known Limitations

1. **Display Only**: Cannot run in headless/server environments
2. **Simple UI**: Focused on demonstrating architecture, not polish
3. **No Persistence**: Client state lost on restart (server session persists)
4. **No World View**: Doesn't render world/rooms (only player status)

### Code Quality

- Type hints for clarity
- Docstrings for all methods
- Error handling throughout
- Clean separation of concerns
- Follows Python conventions

## Conclusion

The new server-backed client successfully demonstrates the client-server architecture transition. It proves that:

✅ Client can operate with **zero business logic**
✅ Server maintains **authoritative game state**
✅ Communication via **REST API works seamlessly**
✅ **Separation of concerns** is maintained
✅ Architecture is **scalable and maintainable**

The implementation serves as a reference for future client development and validates the architectural decisions made in the server design.
