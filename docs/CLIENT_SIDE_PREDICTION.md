# Client-Side Movement Prediction

## Overview

Client-side movement prediction (WI-005) adds optimistic position updates to reduce perceived latency during player movement. When enabled, the client immediately updates the player's visual position before waiting for server confirmation.

## Configuration

The prediction system can be configured in `src/config/config.py`:

```python
# client-side prediction (WI-005)
self.enable_prediction = True              # Enable/disable prediction
self.prediction_snap_threshold = 2         # Tiles difference before snapping
```

### Configuration Options

- **`enable_prediction`** (boolean, default: `True`)
  - When `True`, enables client-side prediction for smoother gameplay
  - When `False`, uses traditional synchronous server-authoritative movement
  
- **`prediction_snap_threshold`** (integer, default: `2`)
  - Maximum allowed distance (in tiles) between predicted and actual server position
  - If prediction error exceeds this threshold, player snaps to server position
  - Lower values = more accurate but more visible corrections
  - Higher values = smoother but may allow temporary desync

## How It Works

### 1. Optimistic Position Update

When a player initiates movement:
1. Client predicts the new position using `_predictPosition()`
2. Client-side collision detection checks:
   - Boundary constraints (room width/height)
   - Solid entity collisions using last known room state
3. If prediction is valid, player sprite moves immediately
4. Player direction updates for visual feedback

### 2. Asynchronous Server Request

Movement request is sent to server in a background thread via `_sendMoveRequest()`:
- Non-blocking operation - player can continue interacting
- Prevents UI freezing on high-latency connections
- Server remains authoritative for actual game state

### 3. Position Reconciliation

When server response arrives:
1. Compare predicted position with server's authoritative position
2. Calculate Manhattan distance: `|pred_x - server_x| + |pred_y - server_y|`
3. If distance < `prediction_snap_threshold`:
   - Accept prediction as "close enough"
   - Clear prediction and use server position
4. If distance >= `prediction_snap_threshold`:
   - Log prediction error with distance
   - Snap player to server position (rubber-banding)
   - Visual correction may be noticeable to player

### 4. Error Handling

On server error or network failure:
- Prediction is immediately reverted
- Player stays at last confirmed server position
- Status message shows error to user
- Prevents client from drifting too far from truth

## Trade-offs

### Responsiveness vs. Anti-Cheat

**Advantages:**
- ✅ Immediate visual feedback (feels responsive)
- ✅ Smoother gameplay on high-latency connections
- ✅ Reduces perceived lag from 200-500ms to ~0ms
- ✅ Better user experience for remote players

**Disadvantages:**
- ❌ Client can temporarily show incorrect state
- ❌ Opens potential for client-side manipulation
- ❌ Requires additional client-side logic and complexity
- ❌ May cause visible "rubber-banding" on prediction errors

### Anti-Cheat Mitigation

The implementation maintains server authority while allowing prediction:

1. **Server Validation**: All movement requests validated server-side
   - Collision detection
   - Movement speed limits  
   - Valid position constraints

2. **Client-Side Collision Prediction**: Uses last known room state
   - Prevents obviously invalid predictions
   - Reduces prediction errors
   - Not authoritative - server can still reject

3. **Prediction Error Logging**: All mismatches are logged
   - Useful for detecting anomalies
   - Can identify potential cheating patterns
   - Helps tune prediction algorithms

4. **Snap-Back on Rejection**: Server rejection causes visible correction
   - Player sees they can't cheat
   - Reinforces server authority
   - Discourages manipulation attempts

### When to Disable Prediction

Consider disabling prediction (`enable_prediction = False`) when:

- **Competitive gameplay** where fairness is critical
- **High-stakes scenarios** (PvP combat, speed runs)
- **Anti-cheat is priority** over responsiveness
- **Server is local** (LAN) where latency is negligible
- **Debugging server logic** to avoid client-side confusion

### When to Enable Prediction

Prediction is beneficial when:

- **High latency connections** (>100ms round-trip)
- **Casual gameplay** where UX matters more than perfect sync
- **Exploration-focused** gameplay (less competitive)
- **Remote players** connecting over internet
- **Turn-based mechanics** where timing is less critical

## Implementation Details

### Threading Model

Movement requests use daemon threads:
```python
threading.Thread(target=self._sendMoveRequest, args=(direction,), daemon=True).start()
```

- **Daemon threads** automatically terminate when main program exits
- **Non-blocking** allows UI to remain responsive
- **Thread-safe** via `pending_move_request` flag prevents concurrent requests

### Collision Prediction

Client-side collision uses last synced room state:
```python
# Check bounds
if predicted_tile_x < 0 or predicted_tile_x >= width:
    return (current_tile_x, current_tile_y)

# Check solid entities
for entity in entities:
    if entity_tile matches predicted_tile and entity.get('solid'):
        return (current_tile_x, current_tile_y)
```

**Limitations:**
- Only knows about entities in last synced room state
- Can't predict other players' movements
- Dynamic obstacles may cause prediction errors
- Server always has final say

### Prediction Error Logging

All prediction errors are logged with distance:
```python
logger.warning(
    f"Prediction error: predicted {self.predicted_position}, "
    f"server {server_position}, distance={distance} tiles"
)
```

**Use cases:**
- Performance monitoring
- Tuning prediction algorithms
- Detecting network issues
- Identifying potential cheating

## Testing

Comprehensive unit tests in `tests/screen/test_serverBackedWorldScreen.py`:

- `test_predict_position_*` - Direction-specific prediction
- `test_predict_position_blocked_by_bounds` - Boundary collision
- `test_predict_position_blocked_by_solid_entity` - Entity collision
- `test_move_player_with_prediction_enabled` - Prediction activation
- `test_send_move_request_*` - Reconciliation scenarios
- `test_render_world_uses_predicted_position` - Rendering integration

## Future Enhancements

Potential improvements for future versions:

1. **Interpolation/Smoothing**: Gradually transition to server position instead of instant snap
2. **Predictive Entity Movement**: Predict other players' positions
3. **Latency-Adaptive Thresholds**: Adjust snap threshold based on measured latency
4. **Prediction History**: Track prediction accuracy per player for anti-cheat
5. **Client-Side Pathfinding**: Predict multi-step movement sequences

## References

- **WORK_ITEMS.md**: WI-005 specification
- **ARCHITECTURE_BOUNDARIES.md**: Client-Server separation principles
- **FINAL_VERIFICATION_DELIVERABLES.md**: Priority 2 UX improvements
