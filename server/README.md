# Roam Server

Spring Boot server for the Roam game providing REST API for game state management with full database persistence.

## Overview

The Roam server is the authoritative source for all game data and business logic. It exposes a versioned REST API that clients can use to interact with the game state. Game sessions, world state, player progress, and entity data are persisted in a relational database (PostgreSQL or H2) using JPA/Hibernate.

## Key Features

- RESTful API for game state management
- Database persistence with JPA/Hibernate
- PostgreSQL support for production
- H2 database for development and testing
- Flyway database migrations
- Docker Compose support
- Automatic and manual save functionality
- Backup and restore capabilities
- **Multiplayer support**: Multiple players can join the same game session
- **Player-to-player collision detection**: Players cannot occupy the same tile
- **Session capacity management**: Up to 10 players per session
- **Player discovery**: API to list all players in a session

## Requirements

- Java 17 or higher
- Maven 3.6 or higher
- Docker and Docker Compose (optional, for running PostgreSQL)

## Quick Start

### With H2 (Development)

```bash
cd server
mvn spring-boot:run
```

The server will start on `http://localhost:8080` using an embedded H2 database.

### With PostgreSQL (Production)

**Security Note**: Set a secure password before starting:

```bash
# Copy and configure environment file
cp .env.example .env
# Edit .env and set POSTGRES_PASSWORD

# Start PostgreSQL with Docker Compose
docker-compose -f compose-db-only.yml up -d

# Run server with PostgreSQL profile
cd server
export DATABASE_PASSWORD=your_secure_password
mvn spring-boot:run -Dspring.profiles.active=postgresql
```

### Full Stack with Docker

**Security Note**: Set a secure password before starting:

```bash
# Copy and configure environment file
cp .env.example .env
# Edit .env and set POSTGRES_PASSWORD

# Start both server and PostgreSQL
docker-compose up -d
```

## Database Documentation

For detailed information about database setup, configuration, migrations, backups, and troubleshooting, see:

- **[DATABASE.md](../docs/DATABASE.md)** - Complete database documentation
- **[STORAGE_ARCHITECTURE.md](../docs/STORAGE_ARCHITECTURE.md)** - Storage abstraction layer and future storage options
- **[DATABASE_IMPLEMENTATION_SUMMARY.md](../docs/DATABASE_IMPLEMENTATION_SUMMARY.md)** - Implementation architecture and design decisions

## Storage Architecture

The server uses an interface-based storage architecture that allows different storage backends (database, JSON files, cloud storage) to be used interchangeably. The current implementation uses JPA/Hibernate with PostgreSQL or H2, but the design supports future implementations like JSON file storage.

## Building

```bash
cd server
mvn clean install
```

## Running

```bash
cd server
mvn spring-boot:run
```

The server will start on `http://localhost:8080` by default.

## API Endpoints

### Session Management

#### Initialize Session
```
POST /api/v1/session/init
Content-Type: application/json

Response:
{
  "sessionId": "uuid",
  "ownerId": "username",
  "currentTick": 0,
  "player": { ... },  // Deprecated: use players map instead
  "players": {
    "username": { ... }  // Map of userId -> PlayerDTO
  },
  "playerCount": 1,
  "maxPlayers": 10,
  "full": false
}
```

#### Get Session
```
GET /api/v1/session/{sessionId}

Response:
{
  "sessionId": "uuid",
  "ownerId": "username",
  "currentTick": 123,
  "player": { ... },  // Deprecated: use players map instead
  "players": {
    "username1": { ... },
    "username2": { ... }
  },
  "playerCount": 2,
  "maxPlayers": 10,
  "full": false
}
```

#### Join Session
```
POST /api/v1/session/{sessionId}/join

Response: Updated session data (same as GET /api/v1/session/{sessionId})

Status Codes:
- 200 OK: Successfully joined session
- 409 CONFLICT: Failed to join session (session does not exist, is full, or is otherwise unavailable)
```

Adds the authenticated user as a new player to an existing game session.
Note: Returns 409 CONFLICT for all failure cases to avoid leaking which session IDs are valid.

#### Leave Session
```
POST /api/v1/session/{sessionId}/leave

Response:
{
  "message": "Successfully left session",
  "sessionId": "uuid"
}

Status Codes:
- 200 OK: Successfully left session
- 403 FORBIDDEN: Session owner cannot leave
- 404 NOT FOUND: Session does not exist
```

Removes the authenticated user from the game session. Session owners cannot leave.

#### Get All Players
```
GET /api/v1/session/{sessionId}/players

Response:
{
  "username1": {
    "id": "uuid",
    "userId": "username1",
    "name": "Player",
    "energy": 100.0,
    "roomX": 0,
    "roomY": 0,
    "tileX": 5,
    "tileY": 5,
    ...
  },
  "username2": { ... }
}
```

Returns all players currently in the session.

#### Update Tick
```
POST /api/v1/session/{sessionId}/tick

Response: Updated session data
```

Updates all players' positions and game state by one tick.

#### Delete Session
```
DELETE /api/v1/session/{sessionId}

Response: 204 No Content
```

#### Save Session
```
POST /api/v1/session/{sessionId}/save

Response:
{
  "message": "Session saved successfully",
  "sessionId": "uuid"
}
```

Manually saves the game session to the database for persistence across server restarts.
Note: Currently only saves the session owner's player state.

#### Load Session
```
POST /api/v1/session/{sessionId}/load

Response: Complete session data (same as GET /api/v1/session/{sessionId})
```

Loads a previously saved game session from the database into memory.

### Player Management

#### Get Player
```
GET /api/v1/session/{sessionId}/player

Response:
{
  "id": "uuid",
  "userId": "username",
  "name": "Player",
  "energy": 100.0,
  "targetEnergy": 100.0,
  "direction": -1,
  "lastDirection": -1,
  "gathering": false,
  "placing": false,
  "crouching": false,
  "moving": false,
  "dead": false,
  "tickLastMoved": -1,
  "tickLastGathered": -1,
  "tickLastPlaced": -1,
  "movementSpeed": 30,
  "gatherSpeed": 30,
  "placeSpeed": 30,
  "roomX": 0,
  "roomY": 0,
  "tileX": 10,
  "tileY": 10,
  "inventory": { ... }
}
```

Gets the authenticated user's player state in the session.

#### Perform Player Action
```
POST /api/v1/session/{sessionId}/player/action
Content-Type: application/json

{
  "action": "move",
  "direction": 0,
  "gathering": true,
  "placing": false,
  "crouching": false,
  "itemName": "apple"
}

Actions: move, stop, gather, place, crouch, consume

Response: Updated player data
```

Note: Movement now includes player-to-player collision detection. Players cannot move into tiles occupied by other players.

#### Update Player Energy
```
PUT /api/v1/session/{sessionId}/player/energy?amount=10&operation=add

Response: Updated player data
```

### Inventory Management

#### Get Inventory
```
GET /api/v1/session/{sessionId}/inventory

Response:
{
  "slots": [
    {
      "itemName": "apple",
      "numItems": 3,
      "maxStackSize": 64,
      "empty": false
    },
    ...
  ],
  "selectedSlotIndex": 0,
  "numFreeSlots": 20,
  "numTakenSlots": 5,
  "numItems": 15
}
```

#### Add Item
```
POST /api/v1/session/{sessionId}/inventory/add?itemName=apple

Response: Updated inventory data
```

#### Remove Item
```
POST /api/v1/session/{sessionId}/inventory/remove?itemName=apple

Response: Updated inventory data
```

#### Select Slot
```
PUT /api/v1/session/{sessionId}/inventory/select?slotIndex=2

Response: Updated inventory data
```

#### Clear Inventory
```
DELETE /api/v1/session/{sessionId}/inventory

Response: Updated inventory data
```

## Error Handling

All errors return a standardized JSON response:

```json
{
  "timestamp": "2024-01-10T12:00:00",
  "status": 404,
  "error": "Session Not Found",
  "message": "Session not found: abc123",
  "path": "/api/v1/session/abc123"
}
```

## Multiplayer Features

The Roam server supports multiple players in the same game session, enabling collaborative gameplay.

### Session Management

- **Session Capacity**: Each session can host up to 10 players (configurable via `GameState.MAX_PLAYERS_PER_SESSION`)
- **Session Owner**: The user who creates the session is the owner and cannot leave
- **Other Players**: Can join and leave sessions freely via the join/leave endpoints

### Player Discovery

- Use `GET /api/v1/session/{sessionId}/players` to list all players in a session
- Each player has a unique `userId` and position in the world
- The session DTO includes a `players` map with all player states

### Collision Detection

- **Player-to-Player Collisions**: Players cannot move into tiles occupied by other players
- **Entity Collisions**: Players also cannot move into tiles with solid entities (trees, rocks, etc.)
- Collision detection is performed server-side during the `tick` update

### Position Synchronization

- All player positions are synchronized on each tick update
- Use `POST /api/v1/session/{sessionId}/tick` to update all players' positions
- Players can be in different rooms and at different positions

### Access Control

- Only players who are part of a session can access its data
- Non-participants receive a 404 error when trying to access a session
- Session owner and participants have equal access to session data

### Limitations

- **Persistence**: Currently, only the session owner's player state is persisted to the database
- **Full multiplayer persistence** (saving all players) is planned for a future enhancement

### Typical Multiplayer Flow

1. Player 1 creates a session: `POST /api/v1/session/init`
2. Player 2 joins the session: `POST /api/v1/session/{sessionId}/join`
3. Both players can now:
   - Get session state: `GET /api/v1/session/{sessionId}`
   - Perform actions: `POST /api/v1/session/{sessionId}/player/action`
   - View all players: `GET /api/v1/session/{sessionId}/players`
4. Game ticks update all players: `POST /api/v1/session/{sessionId}/tick`
5. Player 2 can leave: `POST /api/v1/session/{sessionId}/leave`

## Testing

```bash
cd server
mvn test
```

The test suite includes comprehensive multiplayer tests:
- `MultiplayerGameServiceTest`: Tests for session management and player join/leave
- `PlayerCollisionTest`: Tests for player-to-player collision detection
- `MultiplayerSessionControllerTest`: Integration tests for multiplayer API endpoints

## Architecture

- **Models**: Domain entities (Player, Inventory, Entity, etc.)
- **DTOs**: Data transfer objects for API contracts
- **Services**: Business logic layer
- **Controllers**: REST API endpoints
- **Exception Handling**: Centralized error handling with @ControllerAdvice
