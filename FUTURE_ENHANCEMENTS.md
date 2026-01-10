# Future Enhancements for Roam Client-Server Architecture

This document outlines future work items that are intentionally deferred beyond the initial client-server architecture implementation. Each work item represents a significant feature enhancement that builds upon the foundation established in this PR.

---

## 1. Complete Client Refactoring

**Title**: Refactor pygame client to use server APIs exclusively

**Priority**: High  
**Estimated Effort**: 2-3 weeks  
**Dependencies**: None (can start immediately)

### Description

Currently, `roam.py` (the original client) contains all game logic locally and operates independently of the server. This work item would refactor it to become fully server-backed like `roam_client.py`, eliminating all local business logic and making all state changes through REST API calls. 

The goal is to migrate world generation, entity management, and all game mechanics to server-side control while maintaining the rich visual experience that users expect from the full game client.

### Detailed Requirements

- Remove all business logic from `roam.py` client
- Replace local state management with server API calls
- Implement client-side rendering using server-provided world data
- Migrate all game mechanics to use REST endpoints
- Maintain existing visual fidelity and user experience
- Ensure smooth performance with API-driven state updates

### Acceptance Criteria

- [ ] Original `roam.py` client communicates exclusively with server
- [ ] No business logic remains in Python client (zero local game rules)
- [ ] All game state mutations go through REST APIs
- [ ] Visual rendering maintains current quality and features
- [ ] Player actions (move, gather, interact) all call server endpoints
- [ ] Performance is acceptable (no noticeable lag from API calls)
- [ ] Client handles network errors gracefully
- [ ] All existing gameplay features continue to work

### Technical Approach

1. Identify all business logic in `roam.py`
2. For each logical component, create corresponding server endpoints (if not already existing)
3. Replace local logic with API client calls
4. Implement client-side caching where appropriate for performance
5. Add error handling and retry logic for network operations
6. Test thoroughly to ensure no regression in functionality

---

## 2. World Generation System

**Title**: Implement procedural world generation on Spring Boot server

**Priority**: High  
**Estimated Effort**: 3-4 weeks  
**Dependencies**: None (can run in parallel with #1)

### Description

Add comprehensive world generation capabilities to the server including procedural room generation, biome systems, terrain features, and environmental objects. The server should generate and persist world state, exposing it through REST endpoints for client rendering. 

This includes room layouts, terrain types (grass, dirt, water, stone), resource distribution algorithms, and environmental hazards. The system should support configurable world parameters and seed-based generation for reproducibility.

### Detailed Requirements

- Implement procedural world generation algorithms
- Create biome system with multiple terrain types
- Design and implement room generation logic
- Implement resource distribution algorithms (trees, rocks, animals, etc.)
- Create REST API endpoints for world data access
- Implement world state persistence
- Support configurable world parameters (size, seed, density, etc.)
- Generate natural-looking terrain with appropriate transitions

### Acceptance Criteria

- [ ] Server generates procedural worlds with configurable parameters
- [ ] REST endpoints expose world data (`GET /api/v1/session/{id}/world`, `/room/{x}/{y}`)
- [ ] World state persists across sessions
- [ ] Biome system with at least 3 different terrain types (grass, forest, desert)
- [ ] Resource distribution algorithms implemented and tunable
- [ ] Client can fetch and render server-generated worlds
- [ ] Worlds are deterministic given the same seed value
- [ ] Generated worlds are visually coherent and natural-looking
- [ ] Performance is acceptable (world generation < 5 seconds)

### REST API Endpoints

```
GET /api/v1/session/{sessionId}/world
  - Returns: WorldDTO with dimensions, seed, biomes

GET /api/v1/session/{sessionId}/room/{x}/{y}
  - Returns: RoomDTO with terrain, entities, resources

POST /api/v1/session/{sessionId}/world/generate
  - Body: { seed: number, width: number, height: number, biomes: string[] }
  - Returns: WorldDTO
```

---

## 3. Complete Entity System

**Title**: Implement full entity system with all game entities on server

**Priority**: Medium  
**Estimated Effort**: 4-5 weeks  
**Dependencies**: #2 (World Generation System)

### Description

Extend the server to manage all entity types including wildlife (Bear, Chicken, Deer), resources (Apple, Berry, Wood, Stone), consumables (Food items), and interactive objects (Trees, Rocks, Bushes). 

Implement entity lifecycle management, spawning algorithms, behavior patterns (AI for animals), and interaction logic. Expose entity data through REST APIs for client rendering and interaction.

### Detailed Requirements

- Implement Java classes for all entity types
- Create entity type hierarchy and interfaces
- Implement entity spawning system with configurable rates
- Add entity behavior patterns and AI (for animals)
- Implement entity lifecycle management (spawn, update, despawn)
- Create entity interaction system (gather, hunt, harvest)
- Design and implement entity state synchronization
- Add REST endpoints for entity queries and interactions

### Entity Types to Implement

**Wildlife**:
- Bear (hostile, wanders, attacks player)
- Chicken (passive, drops food when harvested)
- Deer (passive, flees from player)

**Resources**:
- Tree (provides wood when chopped)
- Rock (provides stone when mined)
- Bush (provides berries when gathered)

**Consumables**:
- Apple (restores energy)
- Berry (restores energy)
- Cooked Food (restores more energy)

### Acceptance Criteria

- [ ] All entity types implemented as Java classes on server
- [ ] Entity spawning system with configurable rates per biome
- [ ] Entity behavior and AI patterns working (animals move, flee, attack)
- [ ] Entity lifecycle management (spawn, update, despawn) implemented
- [ ] REST endpoints for entity queries (`GET /api/v1/session/{id}/entities`)
- [ ] Entity interaction system (gather, hunt, harvest) functional
- [ ] Entity state synchronization with clients working smoothly
- [ ] Entities respect world boundaries and terrain constraints
- [ ] Entity collisions handled correctly
- [ ] Performance testing with 100+ entities shows acceptable performance

### REST API Endpoints

```
GET /api/v1/session/{sessionId}/entities
  - Returns: List<EntityDTO> for all entities in session

GET /api/v1/session/{sessionId}/entities/{entityId}
  - Returns: EntityDTO for specific entity

POST /api/v1/session/{sessionId}/entities/{entityId}/interact
  - Body: { action: "gather" | "attack" | "harvest" }
  - Returns: InteractionResultDTO
```

---

## 4. Database Persistence Layer

**Title**: Add PostgreSQL/H2 database for session and world persistence

**Priority**: Medium  
**Estimated Effort**: 3-4 weeks  
**Dependencies**: #2 (World Generation), #3 (Entity System)

### Description

Implement a full persistence layer using JPA/Hibernate to store game sessions, world state, player progress, and entity data in a relational database. This enables game state to persist across server restarts, supports save/load functionality, and allows for historical data analysis. 

Includes comprehensive schema design, migration scripts using Flyway or Liquibase, and a complete data access layer with repositories and services.

### Detailed Requirements

- Design normalized database schema for all game entities
- Implement JPA entities with proper relationships
- Create Spring Data JPA repositories
- Add Flyway/Liquibase for schema migrations
- Implement session persistence (save/load game state)
- Add world state storage in database
- Implement player progress tracking
- Configure connection pooling (HikariCP)
- Add transaction management
- Implement backup and restore capabilities

### Database Schema (High-Level)

**Tables**:
- `sessions` - Game session metadata
- `worlds` - World configuration and state
- `rooms` - Individual room data
- `players` - Player state and progress
- `entities` - All game entities
- `inventory_items` - Player inventory
- `world_events` - Historical event log

### Acceptance Criteria

- [ ] Database schema designed and documented for all game entities
- [ ] JPA entities and repositories implemented
- [ ] Session persistence working (save/load game state)
- [ ] World state stored in database with efficient queries
- [ ] Player progress tracking across sessions
- [ ] Flyway/Liquibase migrations for schema versioning
- [ ] Connection pooling configured (HikariCP)
- [ ] Transaction management properly configured
- [ ] Backup and restore capabilities implemented
- [ ] Database queries optimized (no N+1 issues)
- [ ] Support for both PostgreSQL (production) and H2 (development/testing)

### Configuration

```yaml
# application.yml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/roam
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 10
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
  flyway:
    enabled: true
    locations: classpath:db/migration
```

---

## 5. JWT-Based Authentication System

**Title**: Implement JWT authentication and authorization for API security

**Priority**: Medium  
**Estimated Effort**: 2-3 weeks  
**Dependencies**: #4 (Database Persistence) recommended but not required

### Description

Add a comprehensive authentication and authorization system using JWT (JSON Web Tokens). Implement user registration, login, token generation/validation, and role-based access control (RBAC). 

Secure all API endpoints with authentication requirements and ensure proper session isolation between users. Include refresh token mechanism, token revocation support, and proper security headers.

### Detailed Requirements

- Implement user registration and login endpoints
- Add JWT token generation and validation
- Implement secure password hashing using BCrypt
- Add token-based authentication to all protected endpoints
- Implement role-based access control (RBAC)
- Create refresh token mechanism
- Add token revocation/blacklisting capability
- Configure security headers properly
- Integrate with Spring Security framework
- Update CORS configuration for authenticated requests

### User Roles

- `USER` - Standard player (can create and play sessions)
- `MODERATOR` - Can view all sessions, moderate content
- `ADMIN` - Full system access, user management

### Acceptance Criteria

- [ ] User registration endpoint (`POST /api/v1/auth/register`)
- [ ] Login endpoint with JWT token generation (`POST /api/v1/auth/login`)
- [ ] Secure password hashing using BCrypt
- [ ] Token-based authentication on all protected endpoints
- [ ] Role-based access control (RBAC) working correctly
- [ ] Refresh token mechanism implemented (`POST /api/v1/auth/refresh`)
- [ ] Token revocation/blacklisting functional
- [ ] Security headers properly configured (CSRF, XSS protection)
- [ ] Integration with Spring Security complete
- [ ] CORS configuration updated for authenticated requests
- [ ] Token expiration and renewal working correctly
- [ ] Unit and integration tests for security components

### REST API Endpoints

```
POST /api/v1/auth/register
  - Body: { username, password, email }
  - Returns: UserDTO

POST /api/v1/auth/login
  - Body: { username, password }
  - Returns: { accessToken, refreshToken, expiresIn }

POST /api/v1/auth/refresh
  - Body: { refreshToken }
  - Returns: { accessToken, expiresIn }

POST /api/v1/auth/logout
  - Header: Authorization: Bearer {token}
  - Returns: 200 OK
```

---

## 6. Multiplayer Support

**Title**: Add support for multiple players per game session

**Priority**: Low  
**Estimated Effort**: 4-5 weeks  
**Dependencies**: #2 (World Generation), #3 (Entity System), #5 (Authentication) recommended

### Description

Extend the server architecture to support multiple concurrent players in the same game world. Implement player discovery, position synchronization, entity ownership, collaborative gameplay mechanics, and conflict resolution. 

This includes enhanced session management for multiple players, player-to-player visibility system, shared world state management, and graceful handling of player connections and disconnections.

### Detailed Requirements

- Modify session management to support multiple players
- Implement player discovery and visibility system
- Add position synchronization for all players
- Implement shared world state management
- Create entity ownership and interaction rules
- Add player-to-player collision detection
- Implement optional chat/communication system
- Add session capacity limits and management
- Handle player disconnections gracefully
- Implement player join/leave notifications

### Gameplay Features

- Players can see each other in the game world
- Players can interact with the same entities (first-come-first-served)
- Players cannot occupy the same space (collision detection)
- Players can share or compete for resources
- Optional: Players can trade items
- Optional: Players can form groups/parties

### Acceptance Criteria

- [ ] Multiple players (2-10) can join the same session
- [ ] Player position synchronization working smoothly
- [ ] Player discovery and visibility system implemented
- [ ] Shared world state management functional
- [ ] Entity ownership and interaction rules working correctly
- [ ] Player-to-player collision detection implemented
- [ ] Chat/communication system working (if implemented)
- [ ] Session capacity limits enforced
- [ ] Graceful handling of player disconnections (player removed from world)
- [ ] Player join/leave notifications sent to other players
- [ ] Performance testing with 10 concurrent players successful

### REST API Endpoints

```
POST /api/v1/session/{sessionId}/join
  - Returns: PlayerDTO with spawn position

GET /api/v1/session/{sessionId}/players
  - Returns: List<PlayerDTO> of all active players

DELETE /api/v1/session/{sessionId}/leave
  - Returns: 200 OK

GET /api/v1/session/{sessionId}/players/{playerId}
  - Returns: PlayerDTO
```

---

## 7. WebSocket Real-Time Updates

**Title**: Implement WebSocket support for real-time multiplayer updates

**Priority**: Low  
**Estimated Effort**: 2-3 weeks  
**Dependencies**: #6 (Multiplayer Support)

### Description

Add WebSocket communication layer alongside REST APIs to enable real-time state synchronization for multiplayer gameplay. Implement server-push notifications for entity updates, player movements, world changes, and game events. 

This eliminates polling overhead and provides instant updates for smooth multiplayer experience. Includes connection management, heartbeat mechanism, and fallback to polling if WebSocket is unavailable.

### Detailed Requirements

- Implement WebSocket endpoints in Spring Boot
- Add client WebSocket connection management
- Create real-time player position updates
- Implement entity state change notifications
- Add world event broadcasting
- Implement efficient message serialization (JSON)
- Add connection heartbeat mechanism
- Implement reconnection logic
- Add fallback to REST polling if WebSocket unavailable
- Perform load testing for concurrent connections

### WebSocket Message Types

**Client → Server**:
- `PLAYER_MOVE` - Player position update
- `PLAYER_ACTION` - Player action (gather, attack, etc.)
- `CHAT_MESSAGE` - Chat message to other players

**Server → Client**:
- `PLAYER_UPDATE` - Other player position/state update
- `ENTITY_UPDATE` - Entity state change
- `WORLD_EVENT` - World event notification
- `CHAT_BROADCAST` - Chat message from another player
- `PLAYER_JOIN` - Player joined session
- `PLAYER_LEAVE` - Player left session

### Acceptance Criteria

- [ ] WebSocket endpoints implemented in Spring Boot (`/ws/game`)
- [ ] Client WebSocket connection management working
- [ ] Real-time player position updates functioning smoothly
- [ ] Entity state change notifications delivered instantly
- [ ] World event broadcasting operational
- [ ] Message serialization efficient (JSON, < 1KB per message)
- [ ] Connection heartbeat and reconnection logic implemented
- [ ] Fallback to REST polling if WebSocket unavailable
- [ ] Load testing completed (100+ concurrent WebSocket connections)
- [ ] Latency acceptable (< 100ms for message delivery)
- [ ] Memory usage acceptable under load
- [ ] Proper error handling and connection cleanup

### WebSocket Configuration

```java
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
    
    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        config.enableSimpleBroker("/topic", "/queue");
        config.setApplicationDestinationPrefixes("/app");
    }
    
    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws/game")
                .setAllowedOrigins("*")
                .withSockJS();
    }
}
```

### Client Connection Example

```python
# Python WebSocket client
from websocket import WebSocketApp

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'PLAYER_UPDATE':
        update_player_position(data['playerId'], data['x'], data['y'])

ws = WebSocketApp(
    "ws://localhost:8080/ws/game",
    on_message=on_message
)
ws.run_forever()
```

---

## Implementation Order Recommendation

For optimal development flow, we recommend implementing these enhancements in the following order:

1. **World Generation System** (#2) - Foundation for visual gameplay
2. **Complete Entity System** (#3) - Requires world system
3. **Complete Client Refactoring** (#1) - Can leverage #2 and #3
4. **Database Persistence Layer** (#4) - Enables save/load
5. **JWT Authentication** (#5) - Security foundation
6. **Multiplayer Support** (#6) - Requires #2, #3, #4, #5
7. **WebSocket Real-Time Updates** (#7) - Enhances #6

Note that items #1, #2, and #3 can be developed in parallel by different team members.

---

## Effort Summary

| Work Item | Priority | Estimated Effort | Dependencies |
|-----------|----------|------------------|--------------|
| #1 Complete Client Refactoring | High | 2-3 weeks | None |
| #2 World Generation System | High | 3-4 weeks | None |
| #3 Complete Entity System | Medium | 4-5 weeks | #2 |
| #4 Database Persistence Layer | Medium | 3-4 weeks | #2, #3 |
| #5 JWT Authentication | Medium | 2-3 weeks | #4 (recommended) |
| #6 Multiplayer Support | Low | 4-5 weeks | #2, #3, #5 |
| #7 WebSocket Real-Time Updates | Low | 2-3 weeks | #6 |
| **Total** | | **20-27 weeks** | |

---

## Contributing

If you'd like to contribute to any of these work items:

1. Create an issue for the specific work item
2. Reference this document and the specific section number
3. Propose your implementation approach
4. Wait for maintainer approval before starting work
5. Follow the project's contribution guidelines

---

*This document is maintained as part of the Roam client-server architecture project.*
