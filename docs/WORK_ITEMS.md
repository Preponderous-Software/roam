# Work Items - Server-Backed Architecture Hardening

Based on comprehensive architectural verification, these work items address identified gaps and prepare the system for production deployment.

---

## Priority 1: Production Blockers (Critical)

### WI-001: Implement Rate Limiting for Player Actions

**Priority:** Critical  
**Estimated Effort:** 2-3 days  
**Dependencies:** None  
**Labels:** security, production-blocker

**Description:**
Implement rate limiting to prevent client abuse (action spam). Currently, clients can send unlimited requests per second (e.g., 1000 moves/sec), which creates security and performance risks.

**Acceptance Criteria:**
- [ ] Add `@RateLimiter` annotation to PlayerController action endpoints
- [ ] Configure per-user action quotas (e.g., 10 actions/second)
- [ ] Implement WebSocket connection throttling (max 100 messages/sec)
- [ ] Return HTTP 429 (Too Many Requests) when limit exceeded
- [ ] Add Bucket4j or Spring RateLimiter dependency
- [ ] Document rate limits in API documentation
- [ ] Add integration tests verifying rate limiting behavior

**Technical Notes:**
```java
@RateLimiter(name = "playerActions", fallbackMethod = "rateLimitFallback")
@PostMapping("/action")
public ResponseEntity<PlayerDTO> performAction(@RequestBody PlayerActionRequest request) {
    // existing logic
}

private ResponseEntity<PlayerDTO> rateLimitFallback(PlayerActionRequest request, RateLimitExceededException ex) {
    return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
        .body(null);
}
```

**References:**
- FINAL_VERIFICATION_DELIVERABLES.md, section "Security Gaps"
- ARCHITECTURE_BOUNDARIES.md, section "Risk Areas & Mitigations"

---

### WI-002: Implement Auto-Save on Server Tick

**Priority:** High  
**Estimated Effort:** 2-3 days  
**Dependencies:** None  
**Labels:** reliability, data-loss-prevention

**Description:**
Implement periodic auto-save to prevent progress loss on client crash. Currently, game state only saves on explicit logout, meaning crashes lose all unsaved progress.

**Acceptance Criteria:**
- [ ] Add `@Scheduled` method in PersistenceService to auto-save all active sessions
- [ ] Configure auto-save interval (30 seconds or 100 ticks)
- [ ] Implement graceful shutdown hook to save all sessions on server stop
- [ ] Add save trigger on menu navigation (client calls save API before leaving world screen)
- [ ] Add logging for auto-save operations (success/failure)
- [ ] Handle save failures gracefully (retry logic, error logging)
- [ ] Add configuration property for auto-save interval
- [ ] Add unit tests for scheduled save logic

**Technical Notes:**
```java
@Scheduled(fixedRate = 30000) // Every 30 seconds
public void autoSaveAllSessions() {
    Map<String, GameState> activeSessions = gameService.getActiveSessions();
    activeSessions.values().forEach(session -> {
        try {
            persistenceService.saveGameState(session);
            logger.debug("Auto-saved session: {}", session.getSessionId());
        } catch (Exception e) {
            logger.error("Auto-save failed for session {}: {}", 
                session.getSessionId(), e.getMessage());
        }
    });
}
```

**Client Changes:**
```python
def switchToMenuScreen(self):
    try:
        self.api_client.save_session()
        logger.info("Session saved before menu navigation")
    except Exception as e:
        logger.warning(f"Failed to save session: {e}")
    
    self.changeScreen = True
    self.nextScreen = ScreenType.MAIN_MENU_SCREEN
```

**References:**
- PERSISTENCE_VALIDATION.md, section "Save Triggers"
- FINAL_VERIFICATION_DELIVERABLES.md, "Priority 1: Gameplay-Blocking"

---

## Priority 2: Gameplay Features (High)

### WI-003: Implement Run Speed Modifier (Shift Key)

**Priority:** High  
**Estimated Effort:** 3-4 days  
**Dependencies:** None  
**Labels:** gameplay, ux

**Description:**
Re-enable run speed modifier (Shift key) by implementing server-side speed action. Currently disabled with comment "speed changes handled server-side" but server has no run action.

**Acceptance Criteria:**
- [ ] Add `running` boolean field to Player model
- [ ] Add `setRunning(boolean)` method to Player
- [ ] Implement `"run"` action in PlayerController
- [ ] Apply speed multiplier (1.5x) to movement cooldown when running
- [ ] Add `isRunning` field to PlayerDTO
- [ ] Update client to send run action on Shift key press/release
- [ ] Update movement cooldown calculation: `baseSpeed / (running ? 1.5 : 1.0)`
- [ ] Persist running state in database
- [ ] Add unit tests for run speed mechanics
- [ ] Update API documentation

**Technical Notes:**

Server (PlayerController.java):
```java
case "run":
    if (request.getRunning() != null) {
        playerService.setRunning(player, request.getRunning());
    }
    break;
```

Server (PlayerService.java):
```java
public void movePlayer(Player player, int direction) {
    double speedMultiplier = player.isRunning() ? 1.5 : 1.0;
    long cooldown = (long) (ticksPerSecond / (player.getMovementSpeed() * speedMultiplier));
    
    if (currentTick < player.getTickLastMoved() + cooldown) {
        return; // Still on cooldown
    }
    
    // existing move logic
}
```

Client (serverBackedWorldScreen.py):
```python
elif key == pygame.K_LSHIFT:
    logger.debug("Shift key pressed - enabling run")
    try:
        self.player_data = self.api_client.perform_player_action(
            "run",
            running=True
        )
        self._updatePlayerFromServerData(self.player_data)
    except Exception as e:
        logger.error(f"Failed to enable run: {e}")
```

**References:**
- FINAL_VERIFICATION_DELIVERABLES.md, "Priority 1: Gameplay-Blocking"
- Feature parity checklist: "Run speed modifier (Shift) - ❌ FAIL"

---

### WI-004: Implement Inventory Drag-and-Drop

**Priority:** High  
**Estimated Effort:** 4-5 days  
**Dependencies:** None  
**Labels:** gameplay, ux

**Description:**
Restore inventory drag-and-drop functionality by implementing server-side inventory slot swapping. Currently removed from client pending server API.

**Acceptance Criteria:**
- [ ] Add `POST /api/v1/session/{id}/inventory/swap` endpoint
- [ ] Accept `{fromSlot: int, toSlot: int}` in request body
- [ ] Implement server-side slot swap logic in Inventory model
- [ ] Return updated InventoryDTO after swap
- [ ] Add validation: slot indices in bounds (0-24)
- [ ] Update client InventoryScreen to call swap API on drag/drop
- [ ] Restore cursor slot UI (temporary item holder during drag)
- [ ] Add click-to-grab, click-to-place interaction
- [ ] Support number keys (1-0) for quick slot swap with cursor
- [ ] Add unit tests for swap logic (empty slots, full slots, same slot)
- [ ] Update API documentation

**Technical Notes:**

Server (InventoryController.java):
```java
@PostMapping("/swap")
public ResponseEntity<InventoryDTO> swapSlots(
    @PathVariable String sessionId,
    @RequestParam int fromSlot,
    @RequestParam int toSlot
) {
    String username = getCurrentUsername();
    GameState gameState = gameService.getSession(sessionId, username);
    
    if (gameState == null) {
        return ResponseEntity.notFound().build();
    }
    
    Inventory inventory = gameState.getPlayer().getInventory();
    
    // Validate slot indices
    if (fromSlot < 0 || fromSlot >= inventory.getNumInventorySlots() ||
        toSlot < 0 || toSlot >= inventory.getNumInventorySlots()) {
        return ResponseEntity.badRequest().build();
    }
    
    // Swap slots
    List<InventorySlot> slots = new ArrayList<>(inventory.getInventorySlots());
    InventorySlot temp = slots.get(fromSlot);
    slots.set(fromSlot, slots.get(toSlot));
    slots.set(toSlot, temp);
    
    InventoryDTO inventoryDTO = mappingService.toInventoryDTO(inventory);
    return ResponseEntity.ok(inventoryDTO);
}
```

Client (inventoryScreen.py):
```python
def handleMouseClickEvent(self, pos):
    slot_index = self._getSlotIndexAtPosition(pos)
    
    if slot_index is None:
        return
    
    if self.cursorSlot.isEmpty():
        # Pick up item from slot
        self.cursorSlot.setContents(
            self.inventory.getInventorySlots()[slot_index].getContents()
        )
        # Call server to swap with empty cursor
        self.api_client.swap_inventory_slots(self.cursor_slot_index, slot_index)
    else:
        # Place item from cursor to slot
        # Call server to swap cursor with target slot
        self.api_client.swap_inventory_slots(self.cursor_slot_index, slot_index)
```

**References:**
- FINAL_VERIFICATION_DELIVERABLES.md, "Priority 1: Gameplay-Blocking"
- Feature parity checklist: "Move items within inventory (drag/drop) - ❌ FAIL"

---

## Priority 3: User Experience (Medium)

### WI-005: Implement Client-Side Movement Prediction

**Priority:** Medium  
**Estimated Effort:** 5-6 days  
**Dependencies:** None  
**Labels:** ux, performance

**Description:**
Add client-side position prediction to reduce perceived latency during movement. Currently, client waits for server response before updating position, which feels sluggish over high-latency connections.

**Acceptance Criteria:**
- [ ] Implement optimistic position update on client (immediate visual feedback)
- [ ] Send movement request to server asynchronously
- [ ] Reconcile client position with server response
- [ ] Handle server rejection (collision, invalid move) by snapping back
- [ ] Add configuration toggle for prediction (on/off)
- [ ] Implement rubber-banding smoothly (interpolation, not instant snap)
- [ ] Add client-side collision prediction (use last known room state)
- [ ] Log prediction errors for debugging
- [ ] Add unit tests for reconciliation logic
- [ ] Document trade-offs (responsiveness vs anti-cheat)

**Technical Notes:**

Client (serverBackedWorldScreen.py):
```python
def movePlayer(self, direction: int):
    if self.config.enable_prediction:
        # Predict new position optimistically
        predicted_tile_x, predicted_tile_y = self._predictPosition(direction)
        
        # Update display immediately
        self.predicted_position = (predicted_tile_x, predicted_tile_y)
        self.player.setDirection(direction)
        
    # Send request to server (async)
    threading.Thread(target=self._sendMoveRequest, args=(direction,)).start()

def _sendMoveRequest(self, direction):
    try:
        player_data = self.api_client.perform_player_action("move", direction=direction)
        
        # Reconcile with server
        server_tile_x = player_data.get('tileX')
        server_tile_y = player_data.get('tileY')
        
        if self.predicted_position != (server_tile_x, server_tile_y):
            logger.warning(f"Prediction error: predicted {self.predicted_position}, server {(server_tile_x, server_tile_y)}")
            # Snap to server position
            self.predicted_position = None
            self._updatePlayerFromServerData(player_data)
    except Exception as e:
        logger.error(f"Move request failed: {e}")
        # Revert prediction
        self.predicted_position = None
```

**Config:**
```ini
[Gameplay]
enable_prediction = true
prediction_snap_threshold = 2  # tiles difference before snapping
```

**References:**
- FINAL_VERIFICATION_DELIVERABLES.md, "Priority 2: User Experience"
- ARCHITECTURE_BOUNDARIES.md, section "Client-Side Prediction"

---

### WI-006: Implement Auto-Reconnect with Exponential Backoff

**Priority:** Medium  
**Estimated Effort:** 3-4 days  
**Dependencies:** None  
**Labels:** reliability, ux

**Description:**
Add automatic reconnection logic when server connection is lost. Currently, server restart or network interruption crashes the client.

**Acceptance Criteria:**
- [ ] Implement connection health checks (heartbeat every 5 seconds)
- [ ] Detect connection loss (timeout on heartbeat or API call)
- [ ] Show "Reconnecting..." UI overlay when connection lost
- [ ] Implement exponential backoff retry (1s, 2s, 4s, 8s, max 30s)
- [ ] Attempt reconnection up to 10 times before giving up
- [ ] Restore session on successful reconnection (fetch player state)
- [ ] Show "Connection lost" error after max retries
- [ ] Add manual "Retry" button on final failure screen
- [ ] Log reconnection attempts and results
- [ ] Add unit tests for reconnection logic

**Technical Notes:**

Client (api_client.py):
```python
def connect_with_retry(self, max_retries=10):
    for attempt in range(max_retries):
        try:
            # Attempt to fetch player state (health check)
            player_data = self.get_player()
            logger.info(f"Reconnection successful on attempt {attempt + 1}")
            return player_data
        except (ConnectionError, requests.exceptions.RequestException) as e:
            if attempt < max_retries - 1:
                backoff = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                logger.warning(f"Connection failed (attempt {attempt + 1}/{max_retries}), retrying in {backoff}s: {e}")
                self.show_reconnecting_ui(attempt + 1, max_retries, backoff)
                time.sleep(backoff)
            else:
                logger.error(f"Reconnection failed after {max_retries} attempts")
                raise ConnectionError("Failed to reconnect to server")
```

Client (reconnectScreen.py - new):
```python
class ReconnectScreen:
    def __init__(self, graphik, config, status):
        self.graphik = graphik
        self.config = config
        self.status = status
        
    def draw(self, attempt, max_retries, wait_time):
        # Dark overlay
        overlay = pygame.Surface(self.graphik.getGameDisplay().get_size())
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.graphik.getGameDisplay().blit(overlay, (0, 0))
        
        # Reconnecting message
        font = pygame.font.Font(None, 48)
        text = font.render("Reconnecting...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.graphik.getGameDisplay().get_width() // 2, 
                                          self.graphik.getGameDisplay().get_height() // 2 - 50))
        self.graphik.getGameDisplay().blit(text, text_rect)
        
        # Attempt info
        small_font = pygame.font.Font(None, 24)
        info = small_font.render(f"Attempt {attempt}/{max_retries} - Retrying in {wait_time}s", True, (200, 200, 200))
        info_rect = info.get_rect(center=(self.graphik.getGameDisplay().get_width() // 2,
                                          self.graphik.getGameDisplay().get_height() // 2 + 20))
        self.graphik.getGameDisplay().blit(info, info_rect)
        
        pygame.display.update()
```

**References:**
- PERSISTENCE_VALIDATION.md, section "Scenario 2: Server Restart"
- FINAL_VERIFICATION_DELIVERABLES.md, "Priority 2: User Experience"

---

## Priority 4: Code Cleanup (Low)

### WI-007: Remove Dead Code (1,200 LOC)

**Priority:** Low  
**Estimated Effort:** 2-3 days  
**Dependencies:** None  
**Labels:** maintenance, tech-debt

**Description:**
Remove identified dead code from client codebase to reduce maintenance burden and confusion. Total 1,200+ LOC across multiple directories.

**Acceptance Criteria:**
- [ ] Verify no test dependencies on worldScreen.py
- [ ] Remove `src/screen/worldScreen.py` (1,128 LOC)
- [ ] Remove `src/world/` directory except `tickCounter.py` (300+ LOC)
- [ ] Remove `src/lib/pyenvlib/` directory (400+ LOC)
- [ ] Remove `src/mapimage/` directory (200+ LOC)
- [ ] Audit and remove `src/inventory/inventoryJsonReaderWriter.py` if unused
- [ ] Remove unused entity AI classes (Bear, Chicken from entity/living/)
- [ ] Run full test suite after each removal to verify no breakage
- [ ] Update imports in any remaining files if needed
- [ ] Update documentation to reflect removed code

**Technical Notes:**

**Step 1: Verify no dependencies**
```bash
cd /home/runner/work/roam-prototype/roam-prototype
grep -r "from.*worldScreen import WorldScreen" src/ tests/
grep -r "from world import\|from world." src/ --exclude-dir=world | grep -v tickCounter
```

**Step 2: Remove directories**
```bash
# Remove old world screen
rm src/screen/worldScreen.py

# Remove world generation (keep tickCounter)
cd src/world/
ls | grep -v tickCounter.py | xargs rm

# Remove environment lib
rm -rf src/lib/pyenvlib/

# Remove minimap
rm -rf src/mapimage/
```

**Step 3: Run tests**
```bash
pytest tests/ -v
```

**References:**
- DEAD_CODE_AUDIT.md - Complete audit results
- FINAL_VERIFICATION_DELIVERABLES.md, "Priority 3: Polish"

---

### WI-008: Create Dedicated Sprite Assets

**Priority:** Low  
**Estimated Effort:** 2-3 days  
**Dependencies:** None  
**Labels:** art, polish

**Description:**
Create dedicated sprite assets for entities currently using placeholders. Improves visual clarity and polish.

**Acceptance Criteria:**
- [ ] Create `assets/images/berry.png` (purple/blue berries, 32x32)
- [ ] Create `assets/images/deer.png` (tan deer, 32x32)
- [ ] Create `assets/images/stone_item.png` (dedicated stone item sprite, 32x32)
- [ ] Update sprite mappings in serverBackedWorldScreen.py
- [ ] Verify all sprites load correctly (test on actual game)
- [ ] Ensure sprites are visually distinct from similar entities
- [ ] Use consistent art style with existing sprites
- [ ] Test sprite rendering at different tile sizes (16px, 32px, 64px)

**Technical Notes:**

Updated sprite mappings (serverBackedWorldScreen.py):
```python
entity_sprite_paths = {
    'Bear': "assets/images/bear.png",
    'Chicken': "assets/images/chicken.png",
    'Deer': "assets/images/deer.png",  # NEW: dedicated sprite
    'Tree': "assets/images/oakWood.png",
    'Rock': "assets/images/stone.png",
    'Bush': "assets/images/leaves.png",
    'Apple': "assets/images/apple.png",
    'Berry': "assets/images/berry.png",  # NEW: dedicated sprite
    'Wood': "assets/images/jungleWood.png",
    'Stone': "assets/images/stone_item.png",  # NEW: dedicated sprite
    'Grass': "assets/images/grass.png"
}
```

**Art Guidelines:**
- 32x32 pixel sprites (tile size)
- Transparent background (PNG with alpha)
- Visible at small scale (clear silhouette)
- Match existing color palette
- Berry: Purple/blue berries in cluster
- Deer: Tan/brown, side profile, antlers visible
- Stone item: Gray stone chunk, distinct from rock (resource node)

**References:**
- ENTITY_RENDERING_VALIDATION.md, section "Recommendations for Future Work"
- FINAL_VERIFICATION_DELIVERABLES.md, "Priority 3: Polish"

---

## Priority 5: Future Enhancements (Backlog)

### WI-009: Implement Multiplayer Player Rendering

**Priority:** Low (Future)  
**Estimated Effort:** 5-7 days  
**Dependencies:** WI-006 (Auto-reconnect)  
**Labels:** multiplayer, enhancement

**Description:**
Add visual representation of other players in the same room. Enables true multiplayer experience.

**Acceptance Criteria:**
- [ ] Subscribe to PlayerPositionUpdate WebSocket broadcasts
- [ ] Store other players' positions in local cache
- [ ] Render other player sprites at their positions
- [ ] Display player names above avatars (text label)
- [ ] Update other players' positions on WebSocket message
- [ ] Remove other players from display when they leave room
- [ ] Show different sprite for other players vs current player (e.g., different color)
- [ ] Add configuration for max visible players (performance limit)
- [ ] Handle room transitions (clear/update player list)
- [ ] Add integration tests for multiplayer rendering

**Technical Notes:**

Client (serverBackedWorldScreen.py):
```python
class ServerBackedWorldScreen:
    def __init__(self, ...):
        # existing init
        self.other_players = {}  # username -> {tile_x, tile_y, direction}
        self.websocket_client.subscribe("PlayerPositionUpdate", self._onPlayerPositionUpdate)
    
    def _onPlayerPositionUpdate(self, message):
        username = message.get('username')
        if username == self.current_username:
            return  # Ignore own updates
        
        self.other_players[username] = {
            'tile_x': message.get('tileX'),
            'tile_y': message.get('tileY'),
            'direction': message.get('direction'),
            'room_x': message.get('roomX'),
            'room_y': message.get('roomY')
        }
    
    def render_world(self):
        # existing rendering
        
        # Render other players
        for username, player_data in self.other_players.items():
            if player_data['room_x'] == self.current_room_x and \
               player_data['room_y'] == self.current_room_y:
                screen_x = world_view_x + player_data['tile_x'] * self.tile_size
                screen_y = world_view_y + player_data['tile_y'] * self.tile_size
                
                # Draw other player sprite (different color)
                self.graphik.getGameDisplay().blit(
                    self.other_player_sprites[player_data['direction']],
                    (screen_x, screen_y)
                )
                
                # Draw name label
                font = pygame.font.Font(None, 16)
                name_text = font.render(username, True, (255, 255, 255))
                self.graphik.getGameDisplay().blit(
                    name_text,
                    (screen_x, screen_y - 18)
                )
```

**References:**
- FINAL_VERIFICATION_DELIVERABLES.md, section "Future Enhancements"
- WebSocket documentation (WEBSOCKET.md)

---

### WI-010: Implement World Minimap

**Priority:** Low (Future)  
**Estimated Effort:** 4-5 days  
**Dependencies:** None  
**Labels:** ux, enhancement

**Description:**
Add minimap UI overlay showing explored rooms and player position. Helps with navigation in large worlds.

**Acceptance Criteria:**
- [ ] Server provides explored room data via API
- [ ] Client fetches explored rooms on world screen init
- [ ] Render minimap overlay in corner (toggle with M key)
- [ ] Show explored rooms as small colored squares
- [ ] Highlight current room with border
- [ ] Show player position as dot within current room
- [ ] Update minimap in real-time as player explores
- [ ] Add zoom in/out controls (+/- keys)
- [ ] Persist minimap position and zoom in config
- [ ] Add configuration for minimap size and opacity

**Technical Notes:**

Server (SessionController.java):
```java
@GetMapping("/{sessionId}/explored-rooms")
public ResponseEntity<List<RoomCoordinatesDTO>> getExploredRooms(@PathVariable String sessionId) {
    String username = getCurrentUsername();
    GameState gameState = gameService.getSession(sessionId, username);
    
    if (gameState == null) {
        return ResponseEntity.notFound().build();
    }
    
    List<RoomCoordinatesDTO> exploredRooms = gameState.getWorld().getRooms().stream()
        .map(room -> new RoomCoordinatesDTO(room.getX(), room.getY(), room.getBiomeType()))
        .collect(Collectors.toList());
    
    return ResponseEntity.ok(exploredRooms);
}
```

Client (minimapOverlay.py - new):
```python
class MinimapOverlay:
    def __init__(self, graphik, config):
        self.graphik = graphik
        self.config = config
        self.visible = False
        self.scale = 10  # pixels per room
        self.explored_rooms = {}  # (x, y) -> biome_type
        
    def draw(self, current_room_x, current_room_y, player_tile_x, player_tile_y):
        if not self.visible:
            return
        
        # Draw minimap background
        minimap_width = 200
        minimap_height = 200
        minimap_x = self.graphik.getGameDisplay().get_width() - minimap_width - 10
        minimap_y = 10
        
        overlay = pygame.Surface((minimap_width, minimap_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.graphik.getGameDisplay().blit(overlay, (minimap_x, minimap_y))
        
        # Draw explored rooms
        center_x = minimap_width // 2
        center_y = minimap_height // 2
        
        for (room_x, room_y), biome in self.explored_rooms.items():
            rel_x = (room_x - current_room_x) * self.scale + center_x
            rel_y = (room_y - current_room_y) * self.scale + center_y
            
            if 0 <= rel_x < minimap_width and 0 <= rel_y < minimap_height:
                color = self._getBiomeColor(biome)
                pygame.draw.rect(
                    overlay,
                    color,
                    (rel_x, rel_y, self.scale, self.scale)
                )
        
        # Draw current room border
        pygame.draw.rect(
            overlay,
            (255, 255, 0),
            (center_x, center_y, self.scale, self.scale),
            2
        )
        
        # Draw player position dot
        player_rel_x = center_x + (player_tile_x / 20) * self.scale
        player_rel_y = center_y + (player_tile_y / 20) * self.scale
        pygame.draw.circle(
            overlay,
            (255, 0, 0),
            (int(player_rel_x), int(player_rel_y)),
            3
        )
```

**References:**
- FINAL_VERIFICATION_DELIVERABLES.md, section "Future Enhancements"
- Original minimap code in src/mapimage/ (removed)

---

## Work Item Summary

| Priority | Count | Effort (days) | Description |
|----------|-------|---------------|-------------|
| **Critical** | 2 | 4-6 | Production blockers (rate limiting, auto-save) |
| **High** | 2 | 7-9 | Gameplay features (run speed, drag/drop) |
| **Medium** | 2 | 8-10 | UX improvements (prediction, reconnect) |
| **Low** | 2 | 4-6 | Code cleanup (dead code, sprites) |
| **Future** | 2 | 9-12 | Enhancements (multiplayer UI, minimap) |
| **Total** | 10 | 32-43 | ~6-9 weeks total effort |

**Recommended Sprint Plan:**

**Sprint 1 (2 weeks):** Critical + High priority
- WI-001: Rate limiting
- WI-002: Auto-save
- WI-003: Run speed modifier

**Sprint 2 (2 weeks):** High + Medium priority
- WI-004: Drag/drop inventory
- WI-005: Client-side prediction
- WI-006: Auto-reconnect

**Sprint 3 (1 week):** Code cleanup
- WI-007: Remove dead code
- WI-008: Create sprite assets

**Backlog:** Future enhancements
- WI-009: Multiplayer player rendering
- WI-010: World minimap

---

## References

All work items derived from comprehensive architectural verification documented in:
- FINAL_VERIFICATION_DELIVERABLES.md
- DEAD_CODE_AUDIT.md
- ENTITY_RENDERING_VALIDATION.md
- ARCHITECTURE_BOUNDARIES.md
- PERSISTENCE_VALIDATION.md
