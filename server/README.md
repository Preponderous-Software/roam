# Roam Server

Spring Boot server for the Roam game providing REST API for game state management.

## Overview

The Roam server is the authoritative source for all game data and business logic. It exposes a versioned REST API that clients can use to interact with the game state.

## Requirements

- Java 17 or higher
- Maven 3.6 or higher

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
  "currentTick": 0,
  "player": { ... }
}
```

#### Get Session
```
GET /api/v1/session/{sessionId}

Response:
{
  "sessionId": "uuid",
  "currentTick": 123,
  "player": { ... }
}
```

#### Update Tick
```
POST /api/v1/session/{sessionId}/tick

Response: Updated session data
```

#### Delete Session
```
DELETE /api/v1/session/{sessionId}

Response: 204 No Content
```

### Player Management

#### Get Player
```
GET /api/v1/session/{sessionId}/player

Response:
{
  "id": "uuid",
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
  "inventory": { ... }
}
```

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

## Testing

```bash
cd server
mvn test
```

## Architecture

- **Models**: Domain entities (Player, Inventory, Entity, etc.)
- **DTOs**: Data transfer objects for API contracts
- **Services**: Business logic layer
- **Controllers**: REST API endpoints
- **Exception Handling**: Centralized error handling with @ControllerAdvice
