# WebSocket Real-Time Updates

This document describes the WebSocket implementation for real-time multiplayer updates in the Roam game server.

## Overview

The Roam server uses WebSocket with STOMP protocol to provide real-time updates for multiplayer gameplay. This eliminates polling overhead and provides instant updates for smooth multiplayer experience.

## Value Proposition

WebSockets provide significant advantages over REST API polling:

**Real-Time Gameplay Updates:**
- **Player Movements**: Instantly broadcast when players move, stop, crouch, or change states - essential for multiplayer coordination
- **Entity Interactions**: Immediate notifications when entities are gathered, placed, or destroyed - prevents race conditions where multiple players interact with the same entity
- **Game Tick Sync**: All clients stay synchronized with server game state without constant polling
- **Combat Updates**: Real-time damage updates for wildlife hunting (bears, deer, chickens)

**Performance Benefits:**
- **Reduced Server Load**: Eliminates constant REST polling (potentially hundreds of requests per second per client)
- **Lower Latency**: Sub-100ms update delivery vs 1-5 second polling intervals
- **Bandwidth Efficiency**: Only sends updates when state changes occur, not empty responses
- **Scalability**: Single persistent connection per client vs multiple HTTP connections

**Use Cases:**
1. **Multiplayer Coordination**: Players see each other's movements and actions in real-time
2. **Resource Competition**: Multiple players gathering resources get instant feedback when items are taken
3. **Combat Awareness**: Players see when wildlife is damaged or killed by others
4. **World Changes**: Room generation and environment updates broadcast to all players

## Connection

### WebSocket Endpoint

```
ws://localhost:8080/ws
```

The endpoint supports SockJS fallback for browsers that don't support native WebSocket.

### Authentication

WebSocket connections are permitted without authentication for simplicity. In production, consider implementing token-based authentication via STOMP headers.

## Message Topics

### Player Position Updates

**Topic**: `/topic/session/{sessionId}/player`

Broadcasts when a player moves or changes state.

**Message Format**:
```json
{
  "type": "PLAYER_POSITION",
  "sessionId": "uuid",
  "timestamp": 1234567890,
  "username": "player1",
  "roomX": 0,
  "roomY": 0,
  "tileX": 5,
  "tileY": 5,
  "direction": 2,
  "gathering": false,
  "placing": false,
  "crouching": false
}
```

- `direction`: -1 (stopped), 0 (up), 1 (left), 2 (down), 3 (right)

### Entity State Updates

**Topic**: `/topic/session/{sessionId}/entity`

Broadcasts when entities are added, removed, or updated in the world.

**Message Format**:
```json
{
  "type": "ENTITY_STATE",
  "sessionId": "uuid",
  "timestamp": 1234567890,
  "action": "ADDED|REMOVED|UPDATED",
  "entity": {
    "id": "uuid",
    "name": "Tree",
    "imagePath": "assets/images/tree.png",
    "locationId": "0,0,10,10",
    "solid": true,
    "energy": 100.0
  }
}
```

### World Events

**Topic**: `/topic/session/{sessionId}/world`

Broadcasts significant world events like room generation or environment changes.

**Message Format**:
```json
{
  "type": "WORLD_EVENT",
  "sessionId": "uuid",
  "timestamp": 1234567890,
  "eventType": "room_generated",
  "description": "New room generated at coordinates (1, 0)",
  "roomX": 1,
  "roomY": 0
}
```

### Tick Updates

**Topic**: `/topic/session/{sessionId}/tick`

Broadcasts game tick progression.

**Message Format**:
```json
{
  "type": "TICK_UPDATE",
  "sessionId": "uuid",
  "timestamp": 1234567890,
  "currentTick": 1000
}
```

### Heartbeat/Ping-Pong

**Client -> Server**: `/app/heartbeat`  
**Server -> Client**: `/user/queue/heartbeat`

Keep-alive mechanism to maintain connection.

**Request Format**:
```json
{
  "type": "HEARTBEAT",
  "message": "ping"
}
```

**Response Format**:
```json
{
  "type": "HEARTBEAT",
  "message": "pong",
  "timestamp": 1234567890
}
```

## Client Implementation Example

### JavaScript/TypeScript with SockJS and STOMP

```javascript
import SockJS from 'sockjs-client';
import { Client } from '@stomp/stompjs';

// Create WebSocket connection
const socket = new SockJS('http://localhost:8080/ws');
const stompClient = new Client({
  webSocketFactory: () => socket,
  onConnect: (frame) => {
    console.log('Connected:', frame);
    
    // Subscribe to player position updates
    stompClient.subscribe(`/topic/session/${sessionId}/player`, (message) => {
      const update = JSON.parse(message.body);
      console.log('Player position update:', update);
      // Update game state
    });
    
    // Subscribe to entity state updates
    stompClient.subscribe(`/topic/session/${sessionId}/entity`, (message) => {
      const update = JSON.parse(message.body);
      console.log('Entity state update:', update);
      // Update entities in game
    });
    
    // Subscribe to tick updates
    stompClient.subscribe(`/topic/session/${sessionId}/tick`, (message) => {
      const update = JSON.parse(message.body);
      console.log('Tick update:', update);
      // Update game tick
    });
    
    // Send heartbeat
    setInterval(() => {
      stompClient.publish({
        destination: '/app/heartbeat',
        body: JSON.stringify({ message: 'ping' })
      });
    }, 30000); // Every 30 seconds
  },
  onStompError: (frame) => {
    console.error('STOMP error:', frame);
  }
});

stompClient.activate();
```

### Python with websocket-client (IMPLEMENTED)

The Python client now has full WebSocket support via the `WebSocketClient` class:

```python
from client.websocket_client import WebSocketClient

# Create client
ws_client = WebSocketClient(
    base_url="http://localhost:8080",
    reconnect_base_delay=1.0,
    reconnect_max_delay=60.0
)

# Register message handlers
def handle_tick_update(message_data):
    tick = message_data.get('currentTick', 0)
    print(f"Tick: {tick}")

def handle_player_position(message_data):
    x, y = message_data.get('tileX'), message_data.get('tileY')
    print(f"Player at ({x}, {y})")

ws_client.register_handler("TICK_UPDATE", handle_tick_update)
ws_client.register_handler("PLAYER_POSITION", handle_player_position)

# Connect (automatically subscribes to topics)
if ws_client.connect(session_id):
    print("Connected!")
else:
    print("Connection failed, falling back to REST")

# Disconnect when done
ws_client.disconnect()
```

**Features**:
- ✅ STOMP protocol support
- ✅ Automatic topic subscription
- ✅ Exponential backoff reconnection
- ✅ Thread-safe operation
- ✅ Graceful fallback to REST polling

**Integration**:
The `ServerBackedWorldScreen` automatically initializes WebSocket connection on startup. See [WEBSOCKET_CLIENT.md](./WEBSOCKET_CLIENT.md) for configuration details.

## Architecture

### Components

1. **WebSocketConfig**: Configures STOMP over WebSocket with message broker
2. **WebSocketController**: Handles incoming client messages (heartbeat)
3. **WebSocketMessageService**: Service for broadcasting messages to clients
4. **Message DTOs**: Type-safe message structures with polymorphic deserialization

### Message Flow

```
Client Action (REST API)
    ↓
Controller (PlayerController, etc.)
    ↓
Service (PlayerService, GameService, EntityInteractionService)
    ↓
WebSocketMessageService.broadcast*()
    ↓
STOMP Message Broker
    ↓
All Subscribed Clients
```

## Performance Considerations

- **In-Memory Broker**: Uses Spring's SimpleBroker for development. For production with many concurrent users, consider:
  - RabbitMQ STOMP broker
  - ActiveMQ
  - Redis pub/sub

- **Message Rate**: Tick updates are sent every game tick. Consider:
  - Throttling updates for high-frequency changes
  - Batching multiple updates in a single message
  - Client-side interpolation for smooth movement

- **Scalability**: Current implementation is single-server. For horizontal scaling:
  - Use external message broker (RabbitMQ/Redis)
  - Session affinity or session replication
  - Distributed session storage

## Testing

Run WebSocket integration tests:

```bash
mvn test -Dtest=WebSocketIntegrationTest
```

Tests verify:
- Connection establishment
- Heartbeat/ping-pong mechanism
- Topic subscriptions
- Message serialization/deserialization

## Fallback to Polling

The Python client (`WebSocketClient`) automatically handles fallback:

1. **Automatic Detection**: Client detects WebSocket connection failure
2. **Graceful Degradation**: Game continues using REST API polling
3. **Reconnection Attempts**: Periodic attempts to restore WebSocket connection
4. **Status Updates**: User is informed of connection state via status messages

Configuration:
```python
# In config.py
use_websocket = False  # Disable WebSocket, use REST only
```

Manual fallback polling (if WebSocket unavailable):
- Poll `/api/v1/session/{sessionId}/tick` for tick updates
- Poll `/api/v1/session/{sessionId}/player` for player updates
- Poll `/api/v1/session/{sessionId}/entities` for entity updates
- Poll `/api/v1/session/{sessionId}` for general state

See [PERFORMANCE.md](./PERFORMANCE.md) for polling frequency recommendations.

## Security Notes

- WebSocket endpoint (`/ws/**`) is configured to permit all connections in `SecurityConfig`
- For production, implement authentication via:
  - JWT token in STOMP headers
  - Custom handshake interceptor
  - Per-topic authorization

## Troubleshooting

### Connection Refused
- Verify server is running on correct port
- Check firewall rules
- Ensure WebSocket is enabled in reverse proxy (if using one)

### Messages Not Received
- Verify correct topic subscription format
- Check sessionId matches active game session
- Enable debug logging: `logging.level.org.springframework.messaging=DEBUG`

### High Latency
- Check network connection
- Consider reducing message frequency
- Implement message batching
- Use binary protocol instead of JSON

## Future Enhancements

- [x] Python client WebSocket implementation
- [ ] JWT authentication for WebSocket connections
- [ ] Binary message encoding (Protocol Buffers/MessagePack)
- [ ] Compression for large messages
- [ ] Reconnection with state recovery
- [ ] Bandwidth monitoring and throttling
- [ ] Load testing with many concurrent connections
- [ ] Horizontal scaling with external message broker

## Client Documentation

For Python client configuration and troubleshooting, see:
- [WEBSOCKET_CLIENT.md](./WEBSOCKET_CLIENT.md) - Client configuration guide
- [PERFORMANCE.md](./PERFORMANCE.md) - Network performance details
