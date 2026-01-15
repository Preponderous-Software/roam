# WebSocket Real-Time Updates

This document describes the WebSocket implementation for real-time multiplayer updates in the Roam game server.

## Overview

The Roam server uses WebSocket with STOMP protocol to provide real-time updates for multiplayer gameplay. This eliminates polling overhead and provides instant updates for smooth multiplayer experience.

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
  "action": "added|removed|updated",
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

### Python with websocket-client

```python
import json
import websocket
from stomp import Connection

# Create WebSocket connection
ws_url = "ws://localhost:8080/ws"
conn = Connection([(ws_url, 8080)])

def on_message(headers, message):
    data = json.loads(message)
    print(f"Received: {data}")
    
    # Handle different message types
    if data.get('type') == 'PLAYER_POSITION':
        # Update player position
        pass
    elif data.get('type') == 'ENTITY_STATE':
        # Update entity state
        pass

conn.set_listener('', on_message)
conn.connect()

# Subscribe to topics
conn.subscribe(destination=f'/topic/session/{session_id}/player', id=1)
conn.subscribe(destination=f'/topic/session/{session_id}/entity', id=2)
conn.subscribe(destination=f'/topic/session/{session_id}/tick', id=3)
```

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

If WebSocket is unavailable:
1. SockJS provides automatic fallback to polling
2. Clients can fall back to REST API polling by:
   - Polling `/api/v1/session/{sessionId}/player` for player updates
   - Polling `/api/v1/session/{sessionId}/entities` for entity updates
   - Polling `/api/v1/session/{sessionId}` for general state

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

- [ ] JWT authentication for WebSocket connections
- [ ] Binary message encoding (Protocol Buffers/MessagePack)
- [ ] Compression for large messages
- [ ] Reconnection with state recovery
- [ ] Bandwidth monitoring and throttling
- [ ] Load testing with many concurrent connections
- [ ] Horizontal scaling with external message broker
