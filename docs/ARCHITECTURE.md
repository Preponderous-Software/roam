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
│  │  • Login/Registration UI                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                     │
│                             ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              API Client Layer                            │   │
│  │  • RoamAPIClient                                        │   │
│  │  • HTTP request/response handling                       │   │
│  │  • JWT token management                                 │   │
│  │  • WebSocket connection                                 │   │
│  │  • Session management                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                     │
└─────────────────────────────┼─────────────────────────────────────┘
                              │
                              │ HTTP/REST + WebSocket
                              │ JSON + JWT
                              │
┌─────────────────────────────▼─────────────────────────────────────┐
│                    Java Spring Boot Server                         │
│                                                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               REST Controllers                             │  │
│  │  /api/v1/auth/*               AuthController              │  │
│  │  /api/v1/session/*            SessionController           │  │
│  │  /api/v1/session/{id}/player/*   PlayerController        │  │
│  │  /api/v1/session/{id}/inventory/* InventoryController    │  │
│  │  /ws/**                       WebSocketController         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                      │
│                             ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                Service Layer                               │  │
│  │  • GameService          (session & tick management)       │  │
│  │  • PlayerService        (player actions & state)          │  │
│  │  • PersistenceService   (database save/load)              │  │
│  │  • WebSocketService     (real-time broadcasts)            │  │
│  │  • MappingService       (DTO ↔ Model conversion)          │  │
│  │  • RateLimitingService  (action throttling)               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                      │
│                             ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               Domain Models                                │  │
│  │  • GameState          (complete session state)            │  │
│  │  • Player            (extends LivingEntity)               │  │
│  │  • Inventory         (player inventory)                   │  │
│  │  • Entity            (base entity class)                  │  │
│  │  • Room, Tile        (world structure)                    │  │
│  │  • User, Role        (authentication)                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                      │
│                             ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Persistence Layer (JPA/Hibernate)              │  │
│  │  • GameSessionEntity                                      │  │
│  │  • PlayerEntity                                           │  │
│  │  • RoomEntity, TileEntity                                 │  │
│  │  • UserEntity, RefreshTokenEntity                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                      │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Database (Postgres) │
                    │  or H2 (dev/test)    │
                    └──────────────────────┘
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout and revoke tokens

### Session Management
- `POST /api/v1/session/init` - Initialize new game session
- `GET /api/v1/session/{id}` - Get session state
- `DELETE /api/v1/session/{id}` - Delete session
- `POST /api/v1/session/{id}/tick` - Advance game tick
- `POST /api/v1/session/{id}/save` - Save session to database
- `POST /api/v1/session/{id}/load` - Load session from database

### Player Management
- `GET /api/v1/session/{id}/player` - Get player state
- `POST /api/v1/session/{id}/player/action` - Perform player action (rate limited)
- `PUT /api/v1/session/{id}/player/energy` - Update player energy (rate limited)

### Inventory Management
- `GET /api/v1/session/{id}/inventory` - Get inventory
- `POST /api/v1/session/{id}/inventory/add` - Add item
- `POST /api/v1/session/{id}/inventory/remove` - Remove item
- `PUT /api/v1/session/{id}/inventory/select` - Select slot
- `DELETE /api/v1/session/{id}/inventory` - Clear inventory

### WebSocket Topics (Real-time Updates)
- `/topic/session/{id}/player` - Player position updates
- `/topic/session/{id}/entity` - Entity state changes
- `/topic/session/{id}/world` - World events
- `/topic/session/{id}/tick` - Game tick updates

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

#### Supported Actions
- **move**: Move player in specified direction (0=up, 1=left, 2=down, 3=right)
  - Request: `{action: "move", direction: <0-3>}`
- **gather**: Toggle gathering mode on/off
  - Request: `{action: "gather", gathering: <true|false>}`
- **crouch**: Toggle crouching on/off
  - Request: `{action: "crouch", crouching: <true|false>}`
- **run**: Toggle running mode on/off (1.5x speed multiplier)
  - Request: `{action: "run", running: <true|false>}`
  - Effect: Reduces movement cooldown by applying 1.5x speed multiplier
  - Cooldown formula: `ticksPerSecond / (movementSpeed * (running ? 1.5 : 1.0))`

## Security Considerations

Current implementation includes:
- ✅ JWT-based authentication and authorization
- ✅ BCrypt password hashing
- ✅ Token refresh mechanism
- ✅ Token blacklisting on logout
- ✅ Rate limiting (10 actions/sec, 100 WebSocket msgs/sec)
- ✅ CORS configuration via environment variables
- ✅ Session isolation (users can only access their own sessions)
- ✅ Input validation via Bean Validation
- ✅ Database connection security

Production recommendations:
- Use HTTPS in production
- Set strong JWT secret via environment variable
- Configure restrictive CORS origins
- Enable database SSL/TLS
- Monitor rate limit violations
- Implement additional authorization rules as needed

## Benefits of This Architecture

1. **Separation of Concerns**: UI logic completely separated from game logic
2. **Scalability**: Server can handle multiple clients
3. **Maintainability**: Changes to business logic don't affect UI code
4. **Testability**: Server logic can be tested independently
5. **Flexibility**: Easy to add new clients (web, mobile, CLI)
6. **Security**: Game state is authoritative on server side

## Migration Status

The architecture has been successfully implemented with the following completed phases:

1. ✅ **Phase 1**: Server infrastructure and core REST API
2. ✅ **Phase 2**: Python client refactored to use server API
3. ✅ **Phase 3**: Database persistence layer with PostgreSQL/H2
4. ✅ **Phase 4**: World generation and entity management on server
5. ✅ **Phase 5**: Authentication (JWT), WebSocket real-time updates, rate limiting

Current capabilities:
- Full client-server separation with REST API
- JWT authentication and authorization
- Database persistence with Flyway migrations
- WebSocket support for real-time multiplayer updates
- Rate limiting for player actions and WebSocket messages
- Docker containerization for easy deployment
- Backup and restore functionality

## Performance Considerations

- REST API provides good performance for turn-based actions
- WebSocket eliminates polling overhead for real-time updates (player movement, entity changes)
- Session state kept in database with optional in-memory caching
- DTOs minimize data transfer between client and server
- Rate limiting prevents abuse (10 actions/sec, 100 WebSocket messages/sec)
- Connection pooling (HikariCP) for efficient database access
