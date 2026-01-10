# Roam Client Application

This is a client-server implementation of Roam where the Python client communicates with a Spring Boot backend via REST API.

## Architecture

- **Server**: Spring Boot application managing all game state and business logic
- **Client**: Python/Pygame application handling only UI rendering and user input

The client contains **no business logic** - all game state mutations happen on the server.

## Prerequisites

1. **Java 17+** and **Maven** (for server)
2. **Python 3.8+** (for client)
3. **Required Python packages**:
   ```bash
   pip install -r ../requirements.txt
   ```

## Running the Application

### 1. Start the Server

From the `server` directory:

```bash
cd ../server
mvn spring-boot:run
```

The server will start on `http://localhost:8080`.

### 2. Start the Client

From the `client` directory:

```bash
python3 roam_client.py
```

Or specify a custom server URL:

```bash
python3 roam_client.py http://localhost:8080
```

## Controls

- **WASD** or **Arrow Keys**: Move player
- **Space**: Stop movement
- **G**: Toggle gathering
- **1/2/3**: Add test items (apple/banana/stone)
- **E**: Consume first item in inventory
- **ESC**: Quit

## Features

### Implemented

- ✅ Session management (create/delete sessions)
- ✅ Player movement (4 directions)
- ✅ Inventory management (add/remove items)
- ✅ Energy system (consume food to restore energy)
- ✅ Player state synchronization with server
- ✅ Real-time UI updates
- ✅ Game tick progression

### Client Responsibilities

The client handles **only**:
- Rendering UI (player status, inventory, controls)
- Capturing user input
- Sending API requests to server
- Displaying server responses

### Server Responsibilities

The server handles **all business logic**:
- Player state management
- Inventory operations
- Energy calculations
- Game tick management
- State validation

## API Communication

The client uses the `RoamAPIClient` class (from `src/client/api_client.py`) to communicate with the server:

- **Session Management**: `/api/v1/session/*`
- **Player Actions**: `/api/v1/session/{id}/player/*`
- **Inventory Operations**: `/api/v1/session/{id}/inventory/*`

## Differences from Original Client

This server-backed client differs from the original Roam application:

1. **No Local Game Logic**: All game rules, state, and progression managed by server
2. **Simplified UI**: Focuses on core player status and inventory display
3. **Stateless Client**: Client maintains only ephemeral display state
4. **Session-Based**: Each client session is tracked independently on server
5. **API-Driven**: All actions result in REST API calls

## Development

The client is intentionally simple to demonstrate the client-server architecture. Future enhancements could include:

- World/room rendering (using server-provided world state)
- Multi-player support (using server's session management)
- More sophisticated UI (menus, maps, etc.)
- WebSocket support for real-time updates

## Troubleshooting

**"Failed to connect to server"**
- Ensure the Spring Boot server is running on port 8080
- Check server logs for errors

**pygame.error**
- Install pygame: `pip install pygame`
- Ensure display is available (may not work in headless environments)

**Import errors**
- Run from the `client` directory
- Ensure parent src directory is accessible

## Architecture Benefits

This client-server architecture provides:

1. **Separation of Concerns**: UI completely decoupled from game logic
2. **Scalability**: Server can handle multiple clients
3. **Testability**: Server logic can be tested independently
4. **Flexibility**: Easy to create alternative clients (web, mobile, CLI)
5. **Security**: Server validates all actions and maintains authoritative state
