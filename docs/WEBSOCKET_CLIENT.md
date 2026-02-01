# WebSocket Client Configuration Guide

This document describes the WebSocket client implementation and configuration for the Python Roam client.

## Overview

The Python client uses WebSocket connections for real-time server-to-client state updates, providing immediate feedback and significantly reducing network overhead. REST API is still used for client-initiated actions.

## Quick Start

WebSocket is enabled by default. No configuration needed for basic usage:

```python
# Start the client - WebSocket connects automatically
python roam.py
```

To disable WebSocket and use REST-only mode:
```python
# In src/config/config.py
self.use_websocket = False
```

## Configuration

### Config Options (src/config/config.py)

```python
# Enable/disable WebSocket (default: True)
use_websocket = True

# Initial reconnection delay in seconds (default: 1.0)
websocket_reconnect_base_delay = 1.0

# Maximum reconnection delay in seconds (default: 60.0)  
websocket_reconnect_max_delay = 60.0
```

### Runtime Configuration

```python
from config.config import Config

config = Config()

# Disable WebSocket
config.use_websocket = False

# Adjust reconnection timing
config.websocket_reconnect_base_delay = 2.0  # Start with 2s delay
config.websocket_reconnect_max_delay = 120.0  # Cap at 2 minutes
```

## Architecture

### Components

**WebSocketClient** (`src/client/websocket_client.py`):
- Manages WebSocket connection lifecycle
- Handles STOMP protocol communication
- Provides automatic reconnection with exponential backoff
- Thread-safe operation

**ServerBackedWorldScreen Integration** (`src/screen/serverBackedWorldScreen.py`):
- Initializes WebSocket on screen startup
- Registers message handlers
- Falls back to REST polling on connection failure
- Monitors connection health

### Message Handlers

Four types of real-time updates are handled:

1. **Tick Updates** (`TICK_UPDATE`):
   - Updates `server_tick` counter
   - Keeps client synchronized with server

2. **Player Position** (`PLAYER_POSITION`):
   - Updates player position and state
   - Triggers room change if player moved rooms
   - Updates player direction

3. **Entity State** (`ENTITY_STATE`):
   - Marks room for refresh
   - Shows updated entity positions

4. **World Events** (`WORLD_EVENT`):
   - Displays event description to player
   - Logs important world changes

## Connection Lifecycle

### 1. Initialization

When game screen starts:
```
ServerBackedWorldScreen.initialize()
  ↓
Create WebSocketClient
  ↓
Register message handlers
  ↓
ws_client.connect(session_id)
  ↓
Connect to ws://server:port/ws/websocket
  ↓
Send STOMP CONNECT frame
  ↓
Receive STOMP CONNECTED frame
  ↓
Subscribe to 4 session topics:
  - /topic/session/{id}/tick
  - /topic/session/{id}/player
  - /topic/session/{id}/entity
  - /topic/session/{id}/world
```

### 2. Active Connection

While connected:
- Server pushes updates via subscribed topics
- Client processes messages via registered handlers
- REST API used only for player actions
- No periodic tick polling needed
- Connection health monitored every frame

### 3. Connection Loss

If connection lost:
```
Detect disconnection
  ↓
Log warning
  ↓
Set using_websocket = False
  ↓
Fall back to REST tick polling
  ↓
Attempt reconnection with exponential backoff
  ↓
If reconnected:
  - Resume WebSocket mode
  - Stop REST polling
```

### 4. Cleanup

When screen exits:
```
ws_client.disconnect()
  ↓
Send STOMP DISCONNECT frame
  ↓
Close WebSocket connection
  ↓
Clean up subscriptions
  ↓
Stop background thread
```

## Reconnection Logic

Exponential backoff with configurable parameters:

```
delay = min(base_delay * (2 ** attempts), max_delay)

Example (base=1s, max=60s):
Attempt 1: 1s
Attempt 2: 2s
Attempt 3: 4s
Attempt 4: 8s
Attempt 5: 16s
Attempt 6: 32s
Attempt 7+: 60s (capped)
```

Reset on successful connection:
- Attempts counter resets to 0
- Next failure starts from base delay again

## Performance Impact

### Network Requests Comparison

| Mode | Scenario | Requests/sec |
|------|----------|--------------|
| REST Only | Idle | 8 |
| REST Only | Moving | 12 |
| REST Only | Gathering | 14 |
| **WebSocket** | **Idle** | **1-2** |
| **WebSocket** | **Moving** | **1-2** |
| **WebSocket** | **Gathering** | **2-3** |

### Benefits

✅ **75-91% reduction** in network requests
✅ **Immediate** state updates (no polling delay)
✅ **Real-time** entity movements
✅ **Lower** server load
✅ **Reduced** bandwidth usage

## Troubleshooting

### Connection Fails

**Symptoms**:
- Status shows "Connected to server (REST)"
- Logs show "WebSocket connection failed"

**Solutions**:
1. Verify server is running: `curl http://localhost:8080/actuator/health`
2. Check WebSocket endpoint: `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8080/ws`
3. Check firewall allows WebSocket
4. Review logs: `tail -f roam.log`

### Frequent Reconnections

**Symptoms**:
- Repeated "connection lost" messages
- Status flickers between REST and WebSocket

**Solutions**:
1. Check network stability
2. Increase max delay: `config.websocket_reconnect_max_delay = 120`
3. Check server logs for connection issues
4. Consider using REST-only if network is unstable

### Falls Back to REST

**Symptoms**:
- Higher network requests
- Status shows "Connection lost - using REST mode"

**Expected Behavior**:
- This is normal when WebSocket unavailable
- Game continues functioning via REST polling
- Automatic reconnection attempts continue

**To Accept REST Mode**:
```python
config.use_websocket = False  # Disable reconnection attempts
```

## Testing

### Unit Tests

```bash
# Run WebSocket client tests
python -m pytest tests/client/test_websocket_client.py -v
```

Tests cover:
- Connection/disconnection
- Message handling
- Reconnection logic
- Thread safety
- STOMP protocol

### Manual Testing

1. **Basic Connection**:
```bash
python roam.py
# Check logs for "WebSocket connection established successfully"
```

2. **Message Reception**:
```bash
# Enable debug logging
export PYTHONPATH=src
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# ... run game
"
# Check logs for "Received tick update via WebSocket"
```

3. **Reconnection**:
```bash
# While game running:
# 1. Stop server
# 2. Watch client fall back to REST
# 3. Restart server
# 4. Watch client reconnect to WebSocket
```

### Network Monitoring

Monitor WebSocket traffic:

```bash
# Install tcpdump
sudo tcpdump -i lo -A 'port 8080'

# Or use Wireshark with filter:
tcp.port == 8080 && websocket
```

## Advanced Usage

### Custom Message Handler

```python
from client.websocket_client import WebSocketClient

ws_client = WebSocketClient("http://localhost:8080")

def my_handler(message_data):
    print(f"Custom handler: {message_data}")

ws_client.register_handler("CUSTOM_TYPE", my_handler)
```

### Multiple Connections

```python
# Connect to multiple servers (not recommended)
ws_client1 = WebSocketClient("http://server1:8080")
ws_client2 = WebSocketClient("http://server2:8080")

ws_client1.connect("session-1")
ws_client2.connect("session-2")
```

### Manual Connection Control

```python
# Disable auto-connect
config.use_websocket = False

# Manual connection later
from client.websocket_client import WebSocketClient
ws_client = WebSocketClient(api_client.base_url)
if ws_client.connect(session_id):
    # Handle messages manually
    pass
```

## Implementation Details

### STOMP Protocol

Client implements STOMP 1.1/1.2:
- CONNECT: Initial handshake
- SUBSCRIBE: Topic subscriptions
- MESSAGE: Incoming messages
- DISCONNECT: Clean shutdown

### Threading Model

WebSocket runs in background thread:
- Main thread: Game loop
- WebSocket thread: Message processing
- Thread-safe message handlers
- Lock-protected state updates

### Error Handling

Comprehensive error handling:
- Connection failures: Auto-retry
- Message parsing errors: Log and continue
- Handler exceptions: Isolate and log
- Clean disconnection: Graceful cleanup

## See Also

- [WEBSOCKET.md](./WEBSOCKET.md) - Server WebSocket documentation
- [PERFORMANCE.md](./PERFORMANCE.md) - Performance metrics and comparisons
- [src/client/websocket_client.py](../src/client/websocket_client.py) - Implementation
- [tests/client/test_websocket_client.py](../tests/client/test_websocket_client.py) - Test suite
