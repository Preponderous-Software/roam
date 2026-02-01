# Performance Optimizations

This document describes the performance optimizations implemented to improve gameplay over network connections, particularly when hosting the server on a remote machine (VM) and connecting from a client on a different machine.

## Problem Statement

When running the game server on a virtual machine and connecting with a client on a separate machine, gameplay experienced significant lag. This was caused by:

1. **High frequency polling**: The client was updating the game tick every 3 frames (~20 times per second)
2. **Multiple requests per tick**: Each tick update required 3 separate HTTP requests:
   - `POST /api/v1/session/{id}/tick` - Update game state
   - `GET /api/v1/session/{id}/player` - Fetch updated player data
   - `GET /api/v1/session/{id}/room/{x}/{y}` - Reload current room
3. **No connection pooling**: Each HTTP request created a new TCP connection
4. **No response caching**: Full game state was transmitted every time
5. **No request timeouts**: Slow network responses could hang indefinitely

## Implemented Optimizations

### 1. Reduced Tick Update Frequency (5x improvement)

**Before**: Tick updated every 3 frames (~20 times/second at 60 FPS)
**After**: Tick updated every 15 frames (~4 times/second at 60 FPS)

**Impact**: Reduces network requests from ~60/sec to ~12/sec (5x reduction)

```python
# Old: serverBackedWorldScreen.py line 1137
tick_update_frequency = 3  # ~20 ticks/sec

# New: serverBackedWorldScreen.py line 1169
tick_update_frequency = 15  # ~4 ticks/sec
```

### 2. Eliminated Redundant Player Data Request (33% improvement)

**Before**: Fetched player data with separate GET request after each tick
**After**: Uses player data already included in tick update response

**Impact**: Reduces requests per tick from 3 to 2 (33% reduction)

```python
# serverBackedWorldScreen.py updateTick() method
# Now extracts player data from session_data returned by update_tick()
if 'player' in session_data:
    self.player_data = session_data['player']
```

### 3. Smart Room Reloading (90%+ improvement)

**Before**: Reloaded entire room on every tick update
**After**: Only reloads room when player changes rooms

**Impact**: Reduces room loads from ~4/sec to <0.1/sec in normal gameplay (40x reduction)

**Important Tradeoff**: This optimization means that entity movements (wildlife, NPCs) within the same room will not be visible in real-time unless the player changes rooms. The previous implementation reloaded the room every tick specifically to show entity movements. This tradeoff significantly improves network performance but reduces gameplay visibility. For real-time entity tracking, consider implementing WebSocket-based entity position updates or periodic room refreshes at a lower frequency (e.g., every 5 seconds).

```python
# Only reload if player moved to a different room
if player_room_x != self.current_room_x or player_room_y != self.current_room_y:
    self.load_room(player_room_x, player_room_y)
```

### 4. Debounced Room Refresh After Actions

**Before**: Room reloaded immediately after each gather/place action
**After**: Room refresh is debounced with 500ms cooldown

**Impact**: Prevents request spam during rapid gathering/placing

```python
# serverBackedWorldScreen.py
self.room_refresh_cooldown_ms = 500  # Minimum 500ms between refreshes
self.room_needs_refresh = True  # Mark for refresh instead of immediate reload
```

### 5. HTTP Connection Pooling

**Before**: Each request opened a new TCP connection
**After**: Maintains persistent connection pool with keep-alive

**Impact**: Eliminates TCP handshake overhead (~50-200ms per request over network)

```python
# api_client.py
self.session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20
)
self.session.mount('http://', adapter)
```

### 6. Request Timeouts

**Before**: No timeout - slow network could hang indefinitely
**After**: 5-second timeout on all requests

**Impact**: Faster failure detection and better responsiveness

```python
# api_client.py
def __init__(self, base_url: str, timeout: float = 5.0):
    self.timeout = timeout
    # Applied to all requests automatically
```

## Overall Impact

**Estimated network traffic reduction**: ~75-85%
**Estimated latency improvement**: ~60-80% reduction in perceived lag

### Request Frequency Summary

| Scenario | Before (req/sec) | After (req/sec) | Improvement |
|----------|------------------|-----------------|-------------|
| Idle in world | ~60 | ~8 | 87% reduction |
| Moving | ~60 | ~12 | 80% reduction |
| Gathering | ~80+ | ~14 | 82% reduction |
| Placing items | ~80+ | ~14 | 82% reduction |

## Future Optimization Opportunities

### 1. WebSocket Integration (High Priority)

The server already has WebSocket support (`WebSocketMessageService`) but the client doesn't use it.

**Recommended approach**:
- Use WebSocket for server-to-client state updates (push instead of poll)
- Keep REST API for client-to-server actions
- Would eliminate periodic tick polling entirely

**Expected impact**: Additional 30-50% reduction in network overhead

### 2. Delta Updates

Currently, the server sends full game state on every update. Implementing delta updates (only changed data) would significantly reduce bandwidth.

**Expected impact**: 50-70% reduction in response payload sizes

### 3. Client-Side Prediction

Implement optimistic client-side movement prediction with server reconciliation to hide network latency.

**Expected impact**: Perceived latency reduction of 200-500ms

### 4. Response Compression

Enable gzip compression on server responses.

**Expected impact**: 60-80% reduction in bandwidth usage

### 5. Batched Actions

Allow batching multiple player actions into a single request.

**Expected impact**: Reduced overhead during rapid actions

## Testing Recommendations

To verify these optimizations:

1. **Monitor network traffic**: Use browser DevTools or Wireshark to measure request frequency and payload sizes
2. **Measure latency**: Compare ping times and action-to-feedback delays
3. **Test over various networks**: Local network, WiFi, cellular, high-latency VPN
4. **Profile client performance**: Ensure optimizations don't impact frame rate

## Configuration

The following can be tuned based on network conditions:

```python
# Client: serverBackedWorldScreen.py
tick_update_frequency = 15  # Increase for less frequent updates (lower network usage), decrease for more frequent updates (more responsive)
room_refresh_cooldown_ms = 500  # Adjust debounce timing

# Client: api_client.py  
timeout = 5.0  # Adjust based on network latency
```

## Conclusion

These optimizations significantly improve gameplay over network connections without requiring major architectural changes. The game should now be playable with reasonable responsiveness even over higher-latency connections (100-200ms).

For the best long-term solution, implementing WebSocket-based state synchronization is strongly recommended.
