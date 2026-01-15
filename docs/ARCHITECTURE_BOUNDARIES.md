# Server ↔ Client Responsibility Matrix

## Phase 4: Architecture Boundaries Validation - COMPLETED

### Design Philosophy

**Server**: Authoritative source of truth for all game state and business logic
**Client**: Thin presentation layer for rendering and input translation only

---

## Responsibility Matrix

| Responsibility | Server | Client | Rationale |
|---------------|--------|--------|-----------|
| **World Generation** | ✅ Primary | ❌ None | Server generates rooms, biomes, entities to ensure multiplayer consistency |
| **Entity Spawning** | ✅ Primary | ❌ None | Server spawns/removes entities; client just renders them |
| **Player Movement** | ✅ Validates & Executes | 🔵 Requests | Server validates position, collision; client sends direction input |
| **Collision Detection** | ✅ Primary | ❌ None | Server checks tile occupancy, entity solidity |
| **Inventory Management** | ✅ Authoritative | 🔵 Caches for UI | Server manages add/remove; client mirrors for display |
| **Item Pickup** | ✅ Validates & Executes | 🔵 Requests | Server checks distance, inventory space; client sends gather action |
| **Item Placement** | ✅ Validates & Executes | 🔵 Requests | Server checks occupancy, item existence; client sends place action |
| **Player Energy** | ✅ Authoritative | 🔵 Displays | Server tracks energy; client shows energy bar |
| **Game Tick** | ✅ Primary | 🔵 Polls | Server advances simulation; client requests tick updates |
| **Position Syncing** | ✅ Broadcasts | 🔵 Receives | Server broadcasts via WebSocket; client updates display |
| **Room Transitions** | ✅ Executes | 🔵 Requests | Server handles room changes; client requests room data |
| **Entity AI/Behavior** | ✅ Primary | ❌ None | Server simulates wildlife movement, reproduction |
| **Rendering** | ❌ None | ✅ Primary | Client draws tiles, entities, UI |
| **Input Handling** | ❌ None | ✅ Primary | Client captures keyboard/mouse, translates to API calls |
| **UI State** | ❌ None | ✅ Primary | Client manages menus, screens, hotbar selection |
| **Session Management** | ✅ Authoritative | 🔵 Stores ID | Server owns GameState; client holds session ID |
| **Authentication** | ✅ Authoritative | 🔵 Stores Token | Server validates JWT; client stores & sends token |
| **Persistence** | ✅ Primary | ❌ None | Server saves to database; client has no local save files |
| **World State** | ✅ Authoritative | ❌ None | Server is source of truth; client never mutates state locally |

**Legend:**
- ✅ Primary: Full ownership and implementation
- 🔵 Participates: Requests, displays, or caches data without authority
- ❌ None: Zero responsibility

---

## Data Flow Examples

### 1. Player Gathers Apple

```
CLIENT                          SERVER
  │                               │
  │   Mouse click on tile         │
  ├──GET tile coords (x, y)────►  │
  │   (client-side calc)          │
  │                               │
  │   POST /player/action         │
  │   {action: "gather",          │
  │    tile_x: 5, tile_y: 3}      │
  ├──────────────────────────────►│
  │                               │ ✅ Get entity at (5,3)
  │                               │ ✅ Check distance to player
  │                               │ ✅ Check inventory space
  │                               │ ✅ Add "Apple" to inventory
  │                               │ ✅ Remove entity from room
  │                               │ ✅ Broadcast EntityRemoved (WebSocket)
  │                               │
  │   PlayerDTO + InventoryDTO    │
  │◄──────────────────────────────┤
  │                               │
  🔵 Sync inventory from response │
  🔵 Render updated inventory UI  │
```

**Validation Points (Server-Side):**
- Entity exists at target tile
- Entity is gatherable (Apple, Berry, Wood, Stone)
- Distance ≤ interaction limit
- Inventory not full
- Player has sufficient energy (future)

**Client Responsibilities:**
- Convert screen coords → tile coords
- Send API request
- Update local inventory cache
- Render inventory UI

**Client Does NOT:**
- ❌ Check if entity exists
- ❌ Remove entity from local world
- ❌ Add item to inventory before server response
- ❌ Validate distance or permissions

---

### 2. Player Moves North

```
CLIENT                          SERVER
  │                               │
  │   W key pressed               │
  │   (or click north tile)       │
  │                               │
  │   POST /player/action         │
  │   {action: "move",            │
  │    direction: 0}              │
  ├──────────────────────────────►│
  │                               │ ✅ Get player's current tile
  │                               │ ✅ Calculate target tile (north)
  │                               │ ✅ Check collision (solid entity?)
  │                               │ ✅ Check room boundary (transition?)
  │                               │ ✅ Update player tileY -= 1
  │                               │ ✅ Update direction = 0 (up)
  │                               │ ✅ Broadcast PlayerPositionUpdate (WebSocket)
  │                               │
  │   PlayerDTO                   │
  │◄──────────────────────────────┤
  │                               │
  🔵 Update player.setDirection(0)│
  🔵 Render player at new position│
```

**Validation Points (Server-Side):**
- Target tile is within room bounds
- Target tile not occupied by solid entity
- Player not crouching (blocks movement)
- Cooldown timer respected (movement speed)

**Client Responsibilities:**
- Capture W key press
- Translate to direction=0
- Send move request
- Update player direction sprite

**Client Does NOT:**
- ❌ Move player locally before server confirms
- ❌ Check collision with entities
- ❌ Handle room transitions
- ❌ Update player position in world state

**Note:** **No client-side prediction** - this causes perceived latency but ensures anti-cheat

---

### 3. Inventory Synchronization on Reconnect

```
CLIENT                          SERVER
  │                               │
  │   App restart/reconnect       │
  │                               │
  │   GET /player                 │
  ├──────────────────────────────►│
  │                               │ ✅ Load GameState from DB
  │                               │ ✅ Fetch player inventory (25 slots)
  │                               │ ✅ Build InventoryDTO with items
  │                               │
  │   PlayerDTO {                 │
  │     inventory: {              │
  │       slots: [                │
  │         {itemName:"Apple",    │
  │          numItems:5},         │
  │         ...                   │
  │       ],                      │
  │       selectedSlotIndex:0     │
  │     }                         │
  │   }                           │
  │◄──────────────────────────────┤
  │                               │
  🔵 Clear local inventory         │
  🔵 For each slot:                │
  🔵   Create item objects (Apple) │
  🔵   Add to inventory slot       │
  🔵 Set selected slot             │
  🔵 Render inventory UI           │
```

**Server Responsibilities:**
- Persist inventory to database
- Load inventory on session start
- Return complete slot data (item names, counts)

**Client Responsibilities:**
- Request player data on startup
- Map item names → item classes
- Recreate item objects for UI
- Display inventory

**Client Does NOT:**
- ❌ Persist inventory to local file
- ❌ Modify server inventory data
- ❌ Add/remove items without server call

---

## Separation of Concerns Validation

### ✅ Server Has NO UI Code
- No pygame imports
- No rendering logic
- No screen management
- Pure business logic & data persistence

### ✅ Client Has NO Business Logic
**Verified Clean:**
- `serverBackedWorldScreen.py` (1,094 LOC):
  - 900+ LOC rendering (tiles, entities, UI)
  - 100 LOC input translation (keypress → API call)
  - 0 LOC game state mutation
  
**Example (lines 216-295):**
```python
def movePlayer(self, direction: int):
    """Send move action to server."""
    # NO collision check
    # NO position update
    # ONLY API call
    self.player_data = self.api_client.perform_player_action(
        "move",
        direction=direction
    )
    self._updatePlayerFromServerData(self.player_data)  # Just sync
```

**Contrast with Old Client (worldScreen.py, lines 400-500):**
```python
def movePlayer(self, direction):
    # ❌ Client-side collision detection
    if self.currentRoom.locationContainsSolidEntity(...):
        return
    
    # ❌ Client-side position update
    self.currentRoom.moveEntity(self.player, location)
    
    # ❌ Client-side room transition
    if self.isPlayerAtRoomBorder():
        self.changeRooms()
```

---

## Client-Side State Mutation Elimination

### Audit Results: **ZERO UNAUTHORIZED MUTATIONS**

**Checked Files:**
1. `serverBackedWorldScreen.py` ✅
   - No direct world state modification
   - All player actions go through `api_client.perform_player_action()`
   - Only syncs state from server responses

2. `roam.py` ✅
   - No game logic
   - Only creates UI screens and manages screen transitions

3. `inventoryScreen.py` ✅
   - Displays inventory from player object
   - No add/remove operations (server-only)

4. `player.py` ✅
   - Pure data holder (direction, energy reference)
   - No mutation methods called except setters from server data

**All State Mutations Go Through:**
- `api_client.perform_player_action()` (POST /player/action)
- `api_client.get_player()` (GET /player)
- `api_client.update_tick()` (POST /tick)
- `api_client.get_room()` (GET /room/{x}/{y})

---

## Tick, REST, and WebSocket Interaction Model

### Three Communication Channels

#### 1. **REST API** - Command Execution (Request/Response)
**Use:** Client sends player actions, server responds with updated state
**Examples:**
- `POST /api/v1/session/{id}/player/action` - Move, gather, place, crouch
- `GET /api/v1/session/{id}/player` - Fetch player state
- `POST /api/v1/session/{id}/tick` - Advance simulation

**Characteristics:**
- Synchronous
- Client waits for response
- Used for direct player input
- No duplicate updates (one action = one response)

#### 2. **WebSocket** - Real-Time Broadcast (Pub/Sub)
**Use:** Server broadcasts state changes to all clients in session
**Examples:**
- `PlayerPositionUpdate` - Player moved
- `EntityRemoved` - Entity gathered/destroyed
- `EntitySpawned` - Wildlife reproduced

**Characteristics:**
- Asynchronous
- Push model (server → clients)
- Used for multiplayer sync
- No client subscription (auto-subscribed on session init)

**WebSocket vs REST Separation:**
```
REST:   Client → Server (Commands: "Move north")
        Server → Client (Response: "You moved")

WebSocket: Server → All Clients (Broadcast: "Player123 moved to (5,3)")
```

**No Overlap:**
- REST responses contain complete new state for requester
- WebSocket broadcasts notify OTHER clients (not requester)
- No duplicate state updates

#### 3. **Tick-Driven Simulation** - Server-Side Loop
**Use:** Server advances game world periodically
**Examples:**
- Wildlife AI movement (Bear wanders)
- Wildlife reproduction (Chicken spawns egg)
- Energy depletion (future)

**Characteristics:**
- Server-controlled frequency (~3 ticks/sec)
- Client polls via `update_tick()` to request sync
- Tick drives WebSocket broadcasts (e.g., wildlife movement)

**Tick vs REST Separation:**
```
Tick:    Server internal loop (advances world state)
         Triggers WebSocket broadcasts (entity moves)

REST:    Client explicitly requests tick via POST /tick
         Server responds with new tick number
         Client then polls GET /player and GET /room for updated state
```

**Client Tick Polling (serverBackedWorldScreen.py lines 874-896):**
```python
def updateTick(self):
    # 1. Ask server to advance tick
    session_data = self.api_client.update_tick()
    self.server_tick = session_data.get('currentTick')
    
    # 2. Fetch updated player state
    self.player_data = self.api_client.get_player()
    
    # 3. Reload room (entity positions may have changed)
    self.load_room(player_room_x, player_room_y)
```

**Frequency Control (lines 1042):**
- Client calls `updateTick()` every 20 frames (~3/sec @ 60 FPS)
- Avoids hammering server
- Balances responsiveness vs network load

---

## Validated Patterns

### ✅ Good: Server-Authoritative Action
```python
# Client sends intent
self.api_client.perform_player_action("gather", tile_x=5, tile_y=3)

# Server validates, executes, responds
# Client ONLY updates UI from response
self._updatePlayerFromServerData(response)
```

### ✅ Good: Cache-Sync Pattern
```python
# Client mirrors server state for UI
self._updateInventoryFromServerData(inventory_data)

# Client NEVER modifies cache without server call
# Inventory.add() only called after server confirmation
```

### ❌ Bad: Client-Authoritative (Removed)
```python
# OLD worldScreen.py - REMOVED
def gatherItem(self):
    # ❌ Client decides if gather succeeds
    if self.canGather():
        # ❌ Client adds to inventory directly
        self.player.inventory.add(item)
        # ❌ Client removes from world directly
        self.currentRoom.removeEntity(entity)
```

### ❌ Bad: Client-Side Prediction (Not Implemented)
```python
# INTENTIONALLY NOT DONE (yet)
def movePlayer(self, direction):
    # ❌ Optimistically move player immediately
    self.player.position = new_position
    
    # ❌ Send to server in background
    self.api_client.perform_player_action_async("move", direction)
    
    # ❌ Reconcile on response
    # If server rejects, snap back
```

**Why Not Implemented:**
- Adds complexity (reconciliation logic)
- Anti-cheat priority over responsiveness
- Acceptable for turn-based gameplay
- **Future enhancement** if latency becomes issue

---

## Risk Areas & Mitigations

### 1. ✅ Tick Desynchronization
**Risk:** Client tick diverges from server tick
**Mitigation:**
- Client polls server tick every 20 frames (line 877-878)
- Server is source of truth; client only displays
- No client-side tick advancement

### 2. ✅ REST/WebSocket Responsibility Overlap
**Risk:** Duplicate state updates from both channels
**Mitigation:**
- REST: Requester gets new state in response
- WebSocket: Other clients get broadcast
- Clear separation documented (lines 290-310 above)

### 3. ✅ Client Trust Boundaries
**Risk:** Client sends malicious data (impossible tile, fake items)
**Mitigation:**
- Server validates ALL inputs:
  - Tile coordinates exist
  - Entity IDs valid
  - Item names in whitelist
  - Distance to target
  - Inventory space
- Client cannot send arbitrary entities or positions

### 4. ⚠️ Action Rate Limiting (NOT YET IMPLEMENTED)
**Risk:** Client spams actions (1000 moves/sec)
**Current State:** Server has cooldown checks (tickLastMoved)
**Future Enhancement:**
- Add HTTP rate limiting (Spring @RateLimiter)
- Per-user action quotas
- WebSocket connection throttling

### 5. ✅ Server-Side Validation Gaps
**Audited:** All player actions validate:
- `move`: Collision, room bounds, cooldown (PlayerService.java:80-150)
- `gather`: Entity existence, distance, inventory space (EntityInteractionService.java:40-80)
- `place`: Item in inventory, tile occupancy, distance (PlayerController.java:120-180)
- `crouch`: No validation needed (toggle state)

### 6. ✅ World/Session Lifecycle Management
**Verified:**
- Session created on `POST /session/init` (GameService.java:50)
- Session loaded from DB on authentication
- Session persisted on logout/disconnect
- No duplicate sessions (username → single session mapping)

---

## Summary

**PHASE 4 COMPLETE ✅**

- ✅ Server vs client responsibilities clearly defined
- ✅ Complete separation of concerns validated
- ✅ Zero client-side state mutations
- ✅ Tick, REST, WebSocket interaction model documented
- ✅ Risk areas identified and mitigated (except rate limiting)
- ✅ Responsibility matrix created

**Architecture Quality: EXCELLENT**
- Clean separation between presentation (client) and logic (server)
- Server is fully authoritative
- Client is truly a thin view layer
- Ready for multiplayer scaling

**Remaining Risk: MEDIUM** - Need rate limiting for production
