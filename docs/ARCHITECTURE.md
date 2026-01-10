# Roam Client-Server Architecture

## Overview

Roam uses a client-server architecture implemented in **[PR #242 - Implement client-server architecture with Spring Boot backend, REST API, pygame client, and Docker support](https://github.com/Preponderous-Software/roam-prototype/pull/242)** where:
- **Server (Java/Spring Boot)**: Authoritative source for game state and business logic
- **Client (Python)**: Handles presentation, UI rendering, and user interaction

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Python Client                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  UI Layer (pygame)                       │   │
│  │  • Rendering                                             │   │
│  │  • Input handling                                        │   │
│  │  • Screen management                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                     │
│                             ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              API Client Layer                            │   │
│  │  • RoamAPIClient                                        │   │
│  │  • HTTP request/response handling                       │   │
│  │  • Session management                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                     │
└─────────────────────────────┼─────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              │ JSON
                              │
┌─────────────────────────────▼─────────────────────────────────────┐
│                    Java Spring Boot Server                         │
│                                                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               REST Controllers                             │  │
│  │  /api/v1/session/*      SessionController                 │  │
│  │  /api/v1/session/{id}/player/*   PlayerController         │  │
│  │  /api/v1/session/{id}/inventory/* InventoryController     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                      │
│                             ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                Service Layer                               │  │
│  │  • GameService        (session & tick management)         │  │
│  │  • PlayerService      (player actions & state)            │  │
│  │  • MappingService     (DTO ↔ Model conversion)            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                      │
│                             ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               Domain Models                                │  │
│  │  • GameState          (complete session state)            │  │
│  │  • Player            (extends LivingEntity)               │  │
│  │  • Inventory         (player inventory)                   │  │
│  │  • Entity            (base entity class)                  │  │
│  │  • LivingEntity      (entities with energy)               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Session Management
- `POST /api/v1/session/init` - Initialize new game session
- `GET /api/v1/session/{id}` - Get session state
- `DELETE /api/v1/session/{id}` - Delete session
- `POST /api/v1/session/{id}/tick` - Advance game tick

### Player Management
- `GET /api/v1/session/{id}/player` - Get player state
- `POST /api/v1/session/{id}/player/action` - Perform player action
- `PUT /api/v1/session/{id}/player/energy` - Update player energy

### Inventory Management
- `GET /api/v1/session/{id}/inventory` - Get inventory
- `POST /api/v1/session/{id}/inventory/add` - Add item
- `POST /api/v1/session/{id}/inventory/remove` - Remove item
- `PUT /api/v1/session/{id}/inventory/select` - Select slot
- `DELETE /api/v1/session/{id}/inventory` - Clear inventory

## Data Flow

### Session Initialization
```
Client                Server
  │                     │
  ├──POST /init────────►│
  │                     │ Create GameState
  │                     │ Create Player
  │                     │ Initialize Inventory
  │                     │
  │◄──SessionDTO────────┤
  │                     │
```

### Player Action
```
Client                Server
  │                     │
  ├──POST /action──────►│
  │ {action: "move",    │ Validate action
  │  direction: 0}      │ Update player state
  │                     │ Update tick timestamps
  │                     │
  │◄──PlayerDTO─────────┤
  │                     │
```

## Security Considerations

Current implementation (v1):
- No authentication/authorization (development only)
- Sessions stored in-memory (not persisted)
- CORS enabled for all origins

Future enhancements:
- Add authentication (JWT tokens)
- Session persistence (database)
- Rate limiting
- Input validation hardening

## Benefits of This Architecture

1. **Separation of Concerns**: UI logic completely separated from game logic
2. **Scalability**: Server can handle multiple clients
3. **Maintainability**: Changes to business logic don't affect UI code
4. **Testability**: Server logic can be tested independently
5. **Flexibility**: Easy to add new clients (web, mobile, CLI)
6. **Security**: Game state is authoritative on server side

## Migration Path

The architecture is designed to support gradual migration:

1. ✅ **Phase 1**: Server infrastructure and core API
2. **Phase 2**: Refactor Python client to use API
3. **Phase 3**: Add persistence layer
4. **Phase 4**: Add world generation on server
5. **Phase 5**: Add multiplayer support

## Performance Considerations

- REST API overhead is acceptable for turn-based game
- Session state kept in-memory for fast access
- DTOs minimize data transfer
- Future: Consider WebSockets for real-time features
