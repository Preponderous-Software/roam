# Changelog

All notable changes to this repository are documented here.
Commits are grouped by date and summarized; AI-agent sessions are
logged in detail below.

## Commit History Summary

| Date | Commits | Summary |
|------|---------|---------|
| 2026-04-19 | 12+ | feat: Add structured logging with structlog — create `src/gameLogging/logger.py` with `getLogger()` and `redact()` helpers, register `LoggerFactory` singleton in DI container, add `LOG_LEVEL`/`LOG_FORMAT` config support, replace all `print()` calls in source files with structured logger calls, add instrumentation across tick counter, save/load operations, map image generation, entity lifecycle, and error handling paths; docs: Create `LOGGING.md` documenting log levels, env vars, field conventions, and redaction policy |
| 2026-04-19 | 11 | refactor: Clean Code refactoring — fix resource leaks (unclosed file handles in stats.py, tickCounter.py, worldScreen.py), remove duplicate player.py methods, refactor 106-line if/elif chain in inventoryJsonReaderWriter.py into entity registry pattern, fix `bool`/`min`/`max` built-in shadowing, remove dead code (unused expressions and assignments in statsScreen.py, dead method calls in worldScreen.py), consolidate duplicate captureScreen/screenshot logic across 3 screen classes into shared screenshotHelper.py, remove redundant comments across roomFactory.py/roomJsonReaderWriter.py/mapImageGenerator.py/worldScreen.py/room.py, rename inconsistent snake_case variables in mapImageGenerator.py, run Black formatter and autoflake; fix: Recreate ThreadPoolExecutors after shutdown() drains them so singleton WorldScreen/RoomPreloader/MapImageUpdater instances survive screen transitions (fixes RuntimeError: cannot schedule new futures after shutdown) |
| 2026-04-19 | 10 | feat: Add lightweight DI container (`src/di/`) with auto-wiring, singleton/transient lifetimes, `@component` decorator, circular dependency detection, and factory function support; feat: Create container singleton (`src/appContainer.py`) and centralized bootstrap (`src/bootstrap.py`); refactor: Migrate `roam.py`, `worldScreen.py`, `map.py` to resolve dependencies via container; fix: Remove dead EnergyBar fallback branch in WorldScreen; fix: Add `resetSingletons()` to prevent stale cached instances across game restarts; refactor: Replace new-instance restart with `Roam.restart()` method that resets state on the existing instance; docs: Document DI strategy in `copilot-instructions.md` for contributors; test: Add 15 DI test cases; perf: Asynchronous room pre-loading to eliminate lag on room transitions — new `RoomPreloader` class using `ThreadPoolExecutor`, thread-safe `Map` with locking, registered in DI container; test: Add 7 `RoomPreloader` test cases; perf: Background map image updates — `MapImageUpdater` now runs Pillow-based map compositing in a background thread to avoid blocking the game loop when the minimap is enabled; test: Add 9 `MapImageUpdater` test cases; fix: Cache last loaded minimap surface so the minimap renders a stale frame instead of flickering when the background thread is writing the map image; perf: Move save() and room file writes to background thread so room transitions are non-blocking; perf: Room PNG capture defers disk I/O to background thread (surface captured on main thread, saved async); perf: Add 60-tick cooldown on minimap image reloads from disk to reduce I/O; fix: Make Map.addRoom() a no-op when key exists to prevent inconsistency between rooms list and index during concurrent preloading; feat: Add WorldScreen.shutdown() to cleanly stop all background thread pools on exit |
| 2026-04-18 | 9 | fix: Status text no longer overlaps with the hotbar — repositioned above the hotbar at all display sizes; fix: Keep minimap square by using game area dimensions instead of full display dimensions; fix: Preserve window dimensions when returning to main menu so maximized windows stay maximized; fix: Room PNG captures for minimap now use game area dimensions and draw unclipped to avoid black letterbox bars in minimap; feat: Allow players to drop item stacks from inventory screen; feat: Make window size persistent across sessions — saved to config.yml and restored on launch; ux: Usability audit applying Nielsen's 10 heuristics — standardized button labels to Title Case, replaced jargon in config/debug text, improved all status messages, added F1 help overlay, added crafting feedback, updated README controls table; feat: Add draggable HUD elements — hotbar, status text, energy bar, and minimap can be repositioned via middle-click drag with screen-edge clamping |
| 2026-04-17 | 2 | feat: Keep game world square and centered upon window resizing — render the game world as a centered square within any-sized window using `Graphik.getGameAreaRect()`; the window itself can be freely resized; test: Add unit tests for getGameAreaRect |
| 2026-04-16 | 5 | feat: Add excrement spawning by living entities that decays into grass over time; test: Add unit tests for world package (RoomType, TickCounter, Room, RoomFactory, Map); feat: Allow player to push stone entities (configurable via `pushableStone` setting) including cross-room pushing; fix: Persist adjacent room after cross-room stone push, re-check solidity after pushing when stacked entities present, remove unused import |
| 2026-04-14 | 1 | feat: Add living entity drops — chickens and bears now drop meat items (ChickenMeat, BearMeat) on death instead of being eaten whole |
| 2026-03-29 | 3 | docs: clarify single-player nature and no multiplayer plans; Initial plan |
| 2025-08-17 | 1 | Merged #232 |
| 2025-08-09 | 4 | Delete COPYRIGHT.md; Update README.md; Update LICENSE |
| 2024-12-19 | 3 | Update COPYRIGHT.md; Create COPYRIGHT.md |
| 2023-08-22 | 3 | Update LICENSE |
| 2023-07-07 | 2 | Update LICENSE |
| 2023-03-12 | 2 | Added tests for InventoryJsonReaderWriter class. |
| 2023-02-26 | 2 | Added unit tests for Inventory & InventorySlot classes.; Added format script & reformatted project files. |
| 2023-02-19 | 1 | Fixed tests not passing due to assets directory reorganization. |
| 2023-02-18 | 2 | Removed generateMapImage config option and printed a warning if ticks take too long to complete.; Moved image assets to 'assets/images' |
| 2023-02-12 | 2 | Added showMiniMap config option toggleable with 'M' |
| 2023-02-10 | 4 | Called tests in run.sh script.; Cleaned up run.sh script.; Added python and pip checks to run.sh script. (+1 more) |
| 2023-02-08 | 9 | Added unit tests for Player class.; Added unit tests for Stats class.; Cleaned up test_livingEntity.py a bit. (+3 more) |
| 2023-02-06 | 7 | Changed version to 0.8.0-SNAPSHOT for development towards next release.; Changed version to 0.7.0 for release.; Added try/except blocks for entity location retrieval in moveLivingEntities() and reproduceLivingEntities() methods in the Room class. (+1 more) |
| 2023-02-05 | 10 | Added 'removeDeadEntities' config option.; Added a check to remove living entities if they have no energy.; Modified requirements.txt (+5 more) |
| 2023-02-04 | 5 | Updated image assets for chickens and bears.; Set the gridSize to 17.; Made the save directory configurable. (+1 more) |
| 2023-02-03 | 7 | Updated requirements.txt; Made entities lose energy when moving/reproducing and required entities to have 50% energy to reproduce.; Made TickCounter measure ticks per second and displayed this in debug mode. (+1 more) |
| 2023-02-02 | 3 | Updated .gitignore to include mapImage.png; Integrated map generation into the project w/ generator & updater classes. |
| 2023-02-01 | 4 | Fixed living entity tracking.; Commented out a print statement in location.py.; Made combine_room_images.py repeat every 30 seconds. |
| 2023-01-31 | 7 | Added launch configuration for combine_room_images.py script.; Optimized image combination functionality.; Modified clear.sh script to account for roompngs. (+4 more) |
| 2023-01-29 | 13 | Changed version to 0.7.0-SNAPSHOT for development towards the next pre-release.; Changed version to 0.6.0; Displayed version at bottom of main menu screen. (+8 more) |
| 2023-01-28 | 9 | Made right clicking inventory slots in the inventory screen select them.; Added click-to-move functionality to inventory screen.; Modified energy bar UI. (+3 more) |
| 2023-01-26 | 13 | Modified needsEnergy() method in Player class.; Incremented rooms explored upon initial player placement in spawn room.; Modified score system. (+5 more) |
| 2023-01-24 | 1 | Added stats json schema and save/load methods for stats. |
| 2023-01-23 | 7 | Made current room and player location persistent.; Moved Player class to its own directory.; Saved current room upon player death. (+2 more) |
| 2023-01-22 | 7 | Attempted to load rooms in before generating them upon moving to a new room.; Added spawn room to list of rooms after generation/loading.; Saved the current room upon changing rooms or leaving the world screen. (+3 more) |
| 2023-01-21 | 2 | Made the player's inventory persistent across multiple games.; Modified PLANNING.md. |
| 2023-01-15 | 18 | Reset the player's age upon death.; Added iron ore to mountain rooms.; Added coal ore to mountain rooms. (+7 more) |
| 2023-01-13 | 17 | Modified PLANNING.md.; Allowed the player to pick up bears.; Added textures for chickens and bears on reproduction cooldowns. (+7 more) |
| 2023-01-12 | 8 | Allowed the player to take screenshots in the stats and inventory screens.; Took into account the direction of the player when handling room changes via corners.; Fixed living entity consumption. (+5 more) |
| 2023-01-11 | 23 | Fixed run.sh script and modified 'how to run' documentation.; Added textures for the player facing up, right and left.; Removed unused import. (+15 more) |
| 2023-01-10 | 5 | Indicated selected inventory slot even if no item is present.; Introduced the concept of inventory slots that may or may not have an item in them.; Allowed the player to cycle through their hotbar with the scroll wheel. (+1 more) |
| 2023-01-09 | 12 | Update README.md; Represented empty hot bar slots with white squares.; Drew white squares to represent empty inventory slots in inventory UI. (+5 more) |
| 2022-12-31 | 5 | Modified main menu text.; Simplified main menu.; Modified player texture. (+2 more) |
| 2022-12-29 | 10 | Modified textures.; Update version.txt; Added assets. (+2 more) |
| 2022-12-28 | 4 | Made the player automatically eat food from their inventory and added the inventory button.; Drew locations slightly bigger than they are supposed to be to resolve a graphical glitch. |
| 2022-12-27 | 3 | Fixed chickens killing the player.; Made the player drop all their items upon death. |
| 2022-12-24 | 14 | Prevented the placement of items on living entities.; Added bears to serve as hostile entities.; Fixed an old reference in the respawnPlayer() method. (+7 more) |
| 2022-12-23 | 20 | Update version.txt; Changed version to 0.1.0 for pre-release.; Added room coordinates to the top left of the screen. (+7 more) |
| 2022-12-19 | 6 | Added shortcuts to the map selection screen.; Updated py_env_lib to 0.0.3; Commented out icon. |
| 2022-12-18 | 2 | Added .gitmodules file. |
| 2022-12-16 | 2 | Reorganized the project. |
| 2022-08-24 | 2 | Limited the speed at which the player can gather and place items. |
| 2022-08-19 | 3 | Made the player able to change direction without moving.; Added a main menu screen. |
| 2022-08-18 | 8 | Added rocks.; Made the player's inventory have a finite size.; Made the player only search for food when below 95% of their maximum energy. (+1 more) |
| 2022-08-17 | 4 | Replaced the next item text with a selected item preview.; Added an options screen. |
| 2022-08-16 | 9 | Replaced the energy display with an energy bar at the bottom of the screen.; Made the player able to run by pressing left shift.; Set tick speed to 1/30 by default. (+2 more) |
| 2022-08-15 | 7 | Changed the name of the AppleTree class to Wood.; Added screenshot button to Controls section of the README.; Made screenshot file names unique. (+1 more) |
| 2022-08-14 | 24 | Made the player respawn upon dying rather than quitting the application.; Made placing items a continuous action.; Made grass have a 95% chance to spawn at a given location. (+9 more) |
| 2022-08-12 | 12 | Added the Grass entity.; Prevented apples from spawning on top of apple trees.; Made apple trees impassable. (+3 more) |
| 2022-08-10 | 2 | Reworked player movement and created the Apple class. |
| 2022-08-09 | 8 | Changed version to 0.0.2.; Placed the player in a sensible location upon entering a new room.; Made the player depend on food entities for energy. (+1 more) |
| 2022-08-08 | 21 | Create version.txt; Update README.md; Modified README. (+9 more) |

## AI Agent Sessions

### 2026-04-19 — Add controls screen for viewing and remapping keybindings
- **New files:**
  - `src/config/keyBindings.py` — `KeyBindings` class managing defaults,
    remapping, conflict detection, save/load to `config.yml`.
  - `src/screen/controlsScreen.py` — `ControlsScreen` UI listing all actions,
    allowing click-to-remap, conflict flagging, reset-to-defaults, save/cancel.
  - `tests/config/test_keyBindings.py` — 16 unit tests covering defaults,
    set/get, conflict detection, save/load round-trip, and reset.
- **Modified files:**
  - `src/screen/screenType.py` — Added `CONTROLS_SCREEN`.
  - `src/screen/optionsScreen.py` — Added "Controls" button and
    `switchToControlsScreen()` method.
  - `src/roam.py` — Imported `KeyBindings` and `ControlsScreen`, registered
    `KeyBindings` instance in DI container with config overrides, resolved
    `ControlsScreen`, handled `CONTROLS_SCREEN` in screen-switching loop.
  - `src/screen/worldScreen.py` — Added `KeyBindings` dependency, replaced all
    hardcoded `pygame.K_*` checks in `handleKeyDownEvent` and `handleKeyUpEvent`
    with `keyBindings.getKey()` calls.
  - `README.md` — Added note that keybindings are configurable in-game.
- **Review follow-up:** Removed `gather` (E) and `place` (Q) from
  `KeyBindings` — gathering and placing are mouse-only actions (left/right
  click) and were never triggered by keyboard keys. Removed corresponding
  dead-code key-up handlers from `worldScreen.py`.
- **Review follow-up (round 2):**
  - Removed unused `Config` import from `keyBindings.py`.
  - Centralized conflict detection: added `getConflictsForBindings(bindings)` to
    `KeyBindings` and refactored `ControlsScreen.getActiveConflicts()` to use it.
  - Fixed `ControlsScreen.resetToDefaults()` to write defaults into
    `pendingBindings` instead of mutating `self.keyBindings` directly, so Cancel
    correctly reverts changes.
  - Removed stray no-op `self.player` statement in `worldScreen.py`.
  - Clarified README tip to note remapping applies only to in-world controls.
- **Review follow-up (round 3):**
  - Extended `KeyBindings` usage to `InventoryScreen`: inventory close key,
    screenshot key, and all hotbar keys now respect remapped bindings.
  - Updated inventory screen "(press I to close)" hint to dynamically show
    the current keybinding name.
  - Extended `KeyBindings` usage to `StatsScreen`: screenshot key now respects
    remapped bindings.
  - Updated `tests/screen/test_inventoryScreen_drop.py` to pass `KeyBindings`
    to the `InventoryScreen` constructor.
  - Updated README tip to reflect that remapping now works across all screens.
- **Tests:** All 319 tests pass (303 original + 16 new).

### 2026-04-19 — Refactor restart mechanism to use `restart()` method
- **Changes:**
  - Refactored `src/roam.py`: extracted shared DI initialization logic into
    `_initializeDependencies()`. `__init__` calls it once; new `restart()`
    method calls it again to reset state on the existing instance.
  - Changed module-level loop from `roam = Roam(config)` to `roam.restart()`,
    so restarts reuse the existing `Roam` instance and pygame display instead
    of constructing a new one. This plays naturally with the singleton container.
  - Updated `copilot-instructions.md` Restart Safety section to document the
    `restart()` approach.
- **Tests:** All 303 tests pass.

### 2026-04-19 — Use `@component` decorator on class definitions
- **Changes:**
  - Created `src/appContainer.py` — module-level container singleton that
    provides a shared `container` instance and a `component` decorator
    importable from any class file.
  - Added `@component` decorator to 12 class definitions: TickCounter,
    Stats, Status, MapImageUpdater, EnergyBar, HudDragManager, WorldScreen,
    OptionsScreen, MainMenuScreen, StatsScreen, ConfigScreen, InventoryScreen.
    These classes now self-register at import time.
  - Simplified `src/bootstrap.py` — imports the shared container from
    `appContainer` instead of creating a new one. Removed all
    `container.component(X)` calls since classes self-register via the
    decorator. Only factory-based and instance registrations remain.
- **Tests:** All 301 tests pass.

### 2026-04-19 — Use `component()` in bootstrap for self-registered types
- **Changes:**
  - Replaced 12 `container.register(X, X)` calls in `src/bootstrap.py` with
    `container.component(X)` for types where the abstract and concrete types
    are the same (TickCounter, Stats, Status, MapImageUpdater, EnergyBar,
    HudDragManager, WorldScreen, OptionsScreen, MainMenuScreen, StatsScreen,
    ConfigScreen, InventoryScreen). Registrations that use factory lambdas or
    custom lifetimes remain as `container.register(...)`.
- **Tests:** All 301 tests pass.

### 2026-04-19 — Third round: split container module, remove manual fallback
- **Changes:**
  - Split `src/di/container.py` into three modules per Clean Code principles:
    `src/di/error.py` (`DIError`), `src/di/registration.py` (`_Registration`),
    and `src/di/container.py` (`Container`). Updated `src/di/__init__.py` to
    re-export from the new locations. Public API unchanged.
  - Removed manual dependency fallback from `WorldScreen.__init__` and
    `WorldScreen.initialize()`. The `container` parameter is now required
    (no default value); if missing, a `DIError` is raised instead of
    silently reverting to manual construction.
- **Tests:** All 301 tests pass.

### 2026-04-19 — Address second round of DI PR review comments
- **Changes:**
  - Moved `tests/test_di.py` → `tests/di/test_container.py` to follow
    repo convention of mirroring `src/` subdirectory structure in `tests/`.
  - Removed redundant `src/di` from `pythonpath` in `pytest.ini` (already
    reachable via `src`).
  - Fixed `_createInstance()` in `src/di/container.py` to raise `DIError`
    with the original exception message when `typing.get_type_hints()` fails,
    instead of silently swallowing the error and continuing with `hints = {}`.
  - Removed `container` parameter from `Map.__init__` in `src/world/map.py`
    — `RoomFactory` and `RoomJsonReaderWriter` are now always constructed
    from the explicit constructor args, eliminating split behavior between
    container and non-container code paths. Updated `src/bootstrap.py`
    accordingly.
- **Tests:** All 301 tests pass.

### 2026-04-18 — Add lightweight dependency injection container
- **Goal:** Replace all manual dependency construction patterns with a
  self-contained DI container, centralizing wiring in a single bootstrap
  module while preserving all business logic unchanged.
- **Changes:**
  - Created `src/di/container.py` — full DI container implementation using
    only Python stdlib (`inspect`, `typing`, `threading`). Supports
    registration by type, singleton/transient lifetimes, auto-wiring via
    type hints, explicit instance registration, `@container.component`
    decorator, and circular dependency detection with `DIError` exceptions.
  - Created `src/di/__init__.py` — re-exports public API (`Container`,
    `DIError`).
  - Created `src/bootstrap.py` — centralized dependency registration for
    Config, TickCounter, Stats, Status, Player, Graphik, all screen
    classes, RoomFactory, RoomJsonReaderWriter, Map, MapImageUpdater,
    EnergyBar, HudDragManager.
  - Migrated `src/roam.py` — all manual constructions replaced with
    `container.resolve(T)`. Runtime dependencies (Graphik, Player,
    Inventory) registered as instances after pygame initialization.
    SaveSelectionScreen registered with factory lambda for callback.
  - Migrated `src/screen/worldScreen.py` — added optional `container`
    parameter; internal service creation (RoomJsonReaderWriter,
    MapImageUpdater, HudDragManager, Map, EnergyBar) uses
    `container.resolve()` when available, falls back to manual
    construction for backward compatibility with tests.
  - Migrated `src/world/map.py` — added optional `container` parameter;
    RoomFactory and RoomJsonReaderWriter creation uses `container.resolve()`
    when available.
  - Added type hints to `TickCounter.__init__` (`config: Config`),
    `Stats.__init__` (`config: Config`), `MapImageUpdater.__init__`
    (`config: Config`) to enable auto-wiring.
  - Created `tests/test_di.py` with 12 test cases covering: no-dependency
    resolution, recursive resolution, singleton lifetime, transient
    lifetime, instance registration, unregistered type error, circular
    dependency error, component decorator, decorator with lifetime,
    default parameters, invalid lifetime error, and instance used in
    auto-wiring.
  - Updated `pytest.ini` to include `src/di` in pythonpath.
- **Tests:** All 300 tests pass (288 existing + 12 new DI tests).

### 2026-04-18 — Allow players to drop item stacks from inventory screen
- **Problem:** Players had no way to quickly discard unwanted items from
  inventory. The only options were placing items one at a time in the world
  or dying.
- **Feature:** Added drop functionality to the inventory screen:
  - Left-click outside the inventory panel while holding items on cursor →
    drops (discards) the entire stack
  - Middle-click outside the inventory panel while holding items on cursor →
    drops (discards) a single item from the cursor stack
- **Changes:**
  - `src/screen/inventoryScreen.py`: Added `isInsideInventoryPanel(pos)`,
    `dropCursorSlot()`, and `dropOneFromCursorSlot()` methods. Modified
    `handleMouseClickEvent` to detect clicks outside the inventory panel
    when cursor slot has items and trigger drop behavior.
  - `README.md`: Added drop controls to the Controls table.
  - `tests/screen/test_inventoryScreen_drop.py`: Added 12 tests covering
    panel bounds checking, full stack drop, single item drop, empty cursor
    handling, and inventory isolation.
- **Validation:** Full test suite passed (254 passed).

### 2026-04-18 — Fix status text overlapping with hotbar
- **Problem:** The status text (rendered by `ui/status.py`) was drawn at a
  position that overlapped with the hotbar (rendered in `worldScreen.py`) at
  larger display sizes. The hotbar painted over the status text making it
  unreadable.
- **Fix:** Changed the status text y-position formula in `src/ui/status.py`
  from `y - y/12 - height/2` (which scaled with display height and overlapped
  the hotbar at ~1080px+) to `hotbarTop - height - 10` using the shared
  `getHotbarTop()` function from `src/ui/hotbarLayout.py`.
- **Refactor:** Centralized hotbar layout constants (`HOTBAR_SLOT_SIZE`,
  `HOTBAR_SLOT_GAP`, `HOTBAR_PADDING`, `HOTBAR_BOTTOM_OFFSET`) into a new
  `src/ui/hotbarLayout.py` module. Updated `status.py`, `worldScreen.py`,
  and tests to reference these shared constants instead of duplicating magic
  numbers.
- **Tests:** Added `tests/ui/test_status.py` with 8 tests covering:
  - No overlap at 720p, 1080p, and 500px display heights
  - Draw skipped when no text is set or after clear
  - Horizontal centering
  - Expiration behavior
- Validation: Full test suite passed (242 passed).

### 2026-04-17 — Follow-up: address PR review coverage threads
- Added targeted tests to `tests/world/test_room.py` to cover refactored logic:
  - `moveLivingEntities()` feeding path (entity movement, energy use, food
    consumption/removal).
  - `reproduceLivingEntities()` cooldown eligibility path (no reproduction while
    on cooldown).
- Added new `tests/world/test_roomJsonReaderWriter.py` with coverage for:
  - Deserialization success across all supported `entityClass` values.
  - `Player` deserialization returning `None`.
  - Unknown `entityClass` raising `ValueError`.
  - Background color parsing from persisted string format via
    `generateRoomFromJson()`.
- Validation:
  - Targeted tests: `tests/world/test_room.py` and
    `tests/world/test_roomJsonReaderWriter.py` passed.
  - Full test suite passed (`231 passed`).

### 2026-04-16 — Clean-code refactor in world modules
- Refactored `src/world/room.py` to improve function clarity and cohesion:
  - Replaced broad `except` blocks with `KeyError`-specific handling.
  - Extracted helper methods for location lookup, feeding behavior, reproduction
    eligibility checks, image updates, and offspring creation.
  - Replaced `== False` / `!= None` style checks with clearer boolean/`is None`
    expressions.
  - Renamed a cryptic local variable (`num`) to `directionIndex` for intent clarity.
- Refactored `src/world/roomJsonReaderWriter.py` to reduce duplication and improve
  naming/error handling:
  - Added context-managed schema loading (`with open(...)`) in `__init__`.
  - Replaced repeated entity-constructor `if/elif` blocks with a constructor map
    and a focused `_createEntity` helper.
  - Replaced generic `Exception` with `ValueError` for unknown entity classes.
  - Removed obsolete commented-out code paths and improved color-parsing naming via
    `_parseBackgroundColor`.
- Ran formatting with Black on modified files.
- Ran full test suite with headless SDL settings; all tests passed.

### 2026-04-16 — Implement limitTps config option to limit TPS
- Added `limitTps` boolean config option (dynamic, default `true`) to
  `src/config/config.py` — when enabled, uses `pygame.time.Clock.tick()` to
  limit the game loop to the configured `ticksPerSecond`.
- Added `limitTps: true` to `config.yml`.
- Created a `pygame.time.Clock` in `WorldScreen.__init__` and used it in the
  game loop (`WorldScreen.run()`) to enforce the TPS cap when limitTps is enabled.
- Removed the `# TODO: implement vsync` comment from the world screen.
- Added a "limit tps" toggle button to `ConfigScreen` so players can enable/disable
  the TPS cap in-game.
- Added unit tests for the `limitTps` config option: default value, toggle, and
  config-file read.
- Renamed from `vsync` to `limitTps` per review feedback — the feature caps
  tick rate via `Clock.tick()`, not true GPU/display vertical synchronization.

### 2026-04-16 — Config Loading Review Follow-up
- Hardened `src/config/config.py` config-file loading:
  - Gracefully falls back to defaults when `config.yml` cannot be opened/decoded.
  - Treats empty values as `None`.
  - Uses typed/coerced getters with fallback defaults for booleans, numbers,
    strings, and color tuples to avoid crashes on malformed values.
  - Stopped stripping inline `#` text from values so quoted strings containing
    `#` are preserved.
- Updated `tests/config/test_config.py`:
  - Added an autouse fixture to isolate all config tests from repo-root
    `config.yml` (hermetic tests).
  - Added tests for unreadable config-file fallback behavior.
  - Added tests for malformed/empty config values falling back to defaults.
- Updated `config.yml` with documented `displayWidth`/`displayHeight` examples.

### 2026-04-16 — Read Config Values from `config.yml`
- Added root-level `config.yml` with default configuration values.
- Updated `src/config/config.py` to load configuration values from
  `config.yml` at startup with fallback defaults when values/files are missing.
- Added config parsing helpers to support booleans, numbers, lists/tuples, and
  strings from the config file.
- Added `test_reads_values_from_config_file` in `tests/config/test_config.py`
  to verify file-based configuration loading.

### 2026-04-16 — Excrement Spawning and Grass Decay
- Created `src/entity/excrement.py` (Excrement entity, `solid=False`,
  stores `tickCreated` for decay tracking).
- Created placeholder asset `assets/images/excrement.png` (32×32 RGBA).
- Added `excrementDecayTicks` config option to `src/config/config.py`
  (default: `30 * 60 * 2` — 2 minutes at 30 tps).
- Added `tickExcrement(tick, config)` method to `src/world/room.py`:
  - Living entities have a 0.1% chance per tick to produce Excrement at
    their current location.
  - Expired Excrement is replaced by Grass unless the location contains a
    solid entity, existing Grass, StoneFloor, or WoodFloor.
- Added `locationContainsEntityOfType(location, entityType)` helper to Room.
- Called `tickExcrement` from the world screen tick loop in
  `src/screen/worldScreen.py` alongside `moveLivingEntities` and
  `reproduceLivingEntities`.
- Added Excrement serialization/deserialization to
  `src/world/roomJsonReaderWriter.py` with `tickCreated` persistence.
- Added 3 unit tests in `tests/entity/test_excrement.py` covering
  initialization, `solid=False`, and `tickCreated` getter/setter.
- Updated `CHANGELOG.md`.

### 2026-04-14 — Meat Drops on Entity Death
- Created `src/entity/chickenMeat.py` (ChickenMeat food entity, energy 15–25).
- Created `src/entity/bearMeat.py` (BearMeat food entity, energy 25–35).
- Created placeholder assets: `assets/images/chickenMeat.png` and
  `assets/images/bearMeat.png` (32×32 RGBA sprites).
- Updated `src/screen/worldScreen.py`:
  - `checkForLivingEntityDeaths()` spawns meat at dying entity location.
  - Added ChickenMeat/BearMeat to `canBePickedUp()`.
- Updated `src/player/player.py`: replaced Chicken in `edibleEntityTypes`
  with ChickenMeat and BearMeat.
- Updated `src/inventory/inventoryJsonReaderWriter.py`: added
  ChickenMeat/BearMeat handling with energy persistence on load for all
  Food entities (Apple, Banana, ChickenMeat, BearMeat).
- Updated `src/world/roomJsonReaderWriter.py`: added ChickenMeat/BearMeat
  handling with energy persistence on load for all Food entities.
- Added `Food.setEnergy()` method with negative-value clamping.
- Fixed `drawLocation` in `src/world/room.py` to always draw the room
  background color before blitting entity textures, ensuring transparent
  entity images render correctly per room.
- Added unit tests: `tests/entity/test_chickenMeat.py`,
  `tests/entity/test_bearMeat.py`, and `setEnergy` tests in
  `tests/entity/test_food.py`.
- Updated `CHANGELOG.md`.

### 2026-04-14 — Crafting System
- Created `src/entity/woodFloor.py` (WoodFloor entity, solid=False).
- Created `src/entity/bed.py` (Bed entity, solid=True).
- Created `src/crafting/recipe.py` (Recipe class with canCraft/craft methods).
- Created `src/crafting/recipeRegistry.py` (RecipeRegistry with Wood Floor
  and Bed recipes).
- Updated `src/screen/inventoryScreen.py` to add a Craft button and togglable
  craft panel showing available recipes; greyed-out recipes when materials are
  insufficient.
- Updated `src/inventory/inventoryJsonReaderWriter.py` to handle WoodFloor
  and Bed entities for save/load.
- Updated `src/world/roomJsonReaderWriter.py` to handle WoodFloor and Bed
  entities for room save/load.
- Created placeholder assets: `assets/images/woodFloor.png` and
  `assets/images/bed.png`.
- Added 6 unit tests in `tests/crafting/` covering recipe canCraft, craft,
  and registry validation.
- Added WoodFloor and Bed to `canBePickedUp` in `src/screen/worldScreen.py`
  so players can pick up placed floors and furniture.
- Created `src/entity/stoneFloor.py`, `src/entity/stoneBed.py`,
  `src/entity/fence.py`, `src/entity/campfire.py` (new craftable entities).
- Created placeholder assets: `assets/images/stoneFloor.png`,
  `assets/images/stoneBed.png`, `assets/images/fence.png`,
  `assets/images/campfire.png`.
- Added 4 new recipes to `src/crafting/recipeRegistry.py`: Stone Floor
  (4× Stone), Stone Bed (3× Stone + 2× Oak Wood), Fence (3× Jungle Wood),
  Campfire (2× Oak Wood + 1× Coal Ore).
- Updated `src/inventory/inventoryJsonReaderWriter.py` and
  `src/world/roomJsonReaderWriter.py` for new entity save/load.
- Added all new entities to `canBePickedUp` in `src/screen/worldScreen.py`.
- Added 4 tests for new recipes in `tests/crafting/test_recipeRegistry.py`.
- Added 1-second cooldown to the Craft button toggle in
  `src/screen/inventoryScreen.py` to prevent rapid toggling.

### 2026-04-14 — Hotbar Mouse Interaction
- Added direct hotbar mouse interaction to `src/screen/worldScreen.py`:
  - Left-click a hotbar slot to pick up / swap / merge items via a cursor slot.
  - Right-click a non-empty hotbar slot to move its contents to the first
    available non-hotbar inventory slot.
  - Right-click a hotbar slot while holding a cursor item to place it into
    that slot (with swap or merge support).
  - Clicking outside the hotbar while holding a cursor item returns it to
    the inventory.
  - Cursor items are returned to inventory when switching to the inventory
    screen or exiting the world screen.
- Added `cursorSlot` (InventorySlot) and `drawCursorSlot()` to WorldScreen
  for visual drag-and-drop feedback.
- Added `getHotbarSlotAtMousePosition()` to WorldScreen for hotbar hit
  detection.
- Added `returnCursorSlotToInventory()` helper to WorldScreen.
- Added `placeIntoFirstAvailableNonHotbarSlot(item)` to
  `src/inventory/inventory.py` for moving items out of the hotbar.
- Added 3 unit tests to `tests/inventory/test_inventory.py` covering the
  new `placeIntoFirstAvailableNonHotbarSlot` method.

### 2026-04-13 — Inventory Stack Merging
- Added `mergeIntoSlot(sourceSlot, destSlot)` method to `src/inventory/inventory.py`
  that transfers items from source to destination up to the max stack size of 20.
- Updated `swapCursorSlotWithInventorySlotByIndex` in `src/screen/inventoryScreen.py`
  to merge stacks when cursor and target slot hold the same item type.
- Updated `handleMouseClickEvent` in `src/screen/inventoryScreen.py` to merge
  stacks on mouse click when cursor and target slot hold the same item type.
- Existing swap behaviour preserved for empty or different-type slots.
- Added 4 unit tests to `tests/inventory/test_inventory.py` covering full merge,
  destination full, partial merge, and different-type no-merge scenarios.

### 2026-04-13 — Save Selection Screen
- Added `SAVE_SELECTION_SCREEN` to `ScreenType`.
- Created `src/screen/saveSelectionScreen.py` implementing a save selection UI:
  - Lists existing save directories with name and last-played date.
  - "New Game" button opens a naming dialog to type a custom save name.
  - Pressing Enter with an empty name auto-generates `save_1`, `save_2`, etc.
  - "Back" button returns to the main menu.
  - Displays a message when no save files exist.
  - Supports keyboard scrolling (Up/Down) and mouse wheel scrolling.
  - Escape to go back.
  - Matches visual style of other game screens.
- Modified `MainMenuScreen` to navigate to Save Selection Screen instead of
  directly to World Screen.
- Modified `Roam` to handle the new `SAVE_SELECTION_SCREEN` type and pass
  `initializeWorldScreen` to `SaveSelectionScreen`.
- Fixed click pass-through from main menu "Play" button to save list by
  waiting for mouse release at the start of `SaveSelectionScreen.run()`.
- Adjusted save list layout: smaller button height and bounded bottom
  limit to prevent overlap with the bottom action buttons.
- Added sort toggle button (date/name) to save selection screen.
- Added delete save functionality with confirmation dialog.
- Disabled underlying save/delete/bottom buttons when a dialog is active,
  preventing accidental save entry when clicking delete.
- Cached save directory scanning to avoid filesystem hits every frame.
- Clamped scroll offset to prevent scrolling past end of save list.
- Fixed busy-wait mouse release loop to handle QUIT events and use delay.
- Fixed `createNewGame` to use `os.path.exists` to avoid collisions with
  non-directory entries.
- Updated window caption when a save is selected.
- Updated test to use `tmp_path` instead of hard-coded `/tmp` path.
- Added 35 unit tests in `tests/screen/test_saveSelectionScreen.py`.
- Added path traversal validation in `createNewGameWithName` to reject
  names containing path separators, `..`, or absolute paths.
- Added safety check in `deleteSave` to verify the target path is within
  `savesBaseDirectory` before removal.
- Fixed `checkForLivingEntityDeaths` in `worldScreen.py` to handle
  missing entities in the removal loop using `removeLivingEntityById`.

### 2026-04-13 — Camera Mode: Follow Player
- Added `cameraFollowPlayer` config option (default: `True`) to `Config`.
- Added `drawWithOffset` method to `Room` for rendering at arbitrary screen
  positions.
- Added `drawFollowMode` method to `WorldScreen` that renders multiple rooms
  centered on the player, allowing cross-room visibility.
- Modified `WorldScreen.draw()` to branch between follow mode and the
  original room-at-a-time mode.
- Updated `getLocationAtMousePosition` to account for camera offset in
  follow mode.
- Added `getOrLoadRoom` helper in `WorldScreen` for retrieving or generating
  adjacent rooms.
- Added 'C' key toggle in `WorldScreen` for camera follow mode.
- Added "camera follow player" toggle button in `ConfigScreen`.
- Added unit tests for the new config option in `tests/config/test_config.py`.
- Optimized rendering performance: cached `pygame.image.load` results in
  `DrawableEntity`, cached `pygame.transform.scale` results in `Room`, and
  added screen-bounds clipping to `drawWithOffset`.
- Fixed `drawWithOffset` to guard `clipHeight` independently from `clipWidth`.
- Simplified `getOrLoadRoom` to delegate room loading to `Map.getRoom`,
  removing duplicate disk-loading logic.
- Removed `roomsExplored` stat inflation from auto-generated neighbor rooms
  in follow mode.
- Fixed mouse coordinate mapping in `getLocationAtMousePosition` to use
  floor division instead of `int()` truncation for correct negative-value
  handling.
- Moved `pygame.init()`/`pygame.quit()` into a pytest fixture in
  `test_config.py` to avoid leaking global state.
- Updated resize-related cache invalidation to clear `Room._scaledImageCache`
  when tile dimensions change, preventing stale scaled Surface reuse after
  display-size-driven tile resizing.
- Optimized `initializeLocationWidthAndHeight` to only clear the scaled image
  cache when tile dimensions actually change, preventing unnecessary cache
  invalidation on room transitions.
- Removed redundant `fill()` call from `drawFollowMode` since `draw()` already
  clears the screen.
- Added `getLocationAndRoomAtMousePosition` method to resolve mouse clicks to
  the correct neighboring room in follow mode, enabling cross-room interaction.
- Updated `executeGatherAction` and `executePlaceAction` to operate on the
  target room (not just `currentRoom`) so entities in visible neighboring rooms
  can be gathered from and placed into.
- Updated distance checks in gather/place actions to use world-grid coordinates
  for correct cross-room distance calculation.

### 2026-04-13 — Copilot instructions & learning log enhancements
- Added CI/CD section to `.github/copilot-instructions.md` documenting the
  `Tests` workflow, triggers, environment, and required checks.
- Expanded AI Agent Guidelines in `.github/copilot-instructions.md` with
  learning log maintenance instructions, integration status tracking, and
  feedback loop process.
- Added Learning Log section to `CHANGELOG.md` with initial entries.

### 2026-04-12 — Initial Copilot instructions created
- Created `.github/copilot-instructions.md` with project context gathered
  from repository inspection.
- Created `CHANGELOG.md` with commit history summary and initial AI agent
  session entry.

## Learning Log

Insights discovered by AI agents during their sessions. Future agents
should read this section before starting work — it captures context that
may not be obvious from the code alone. When you learn something new
about this repository, add it here so the next agent benefits.

- 2026-04-13: `[integrated]` The CI workflow sets
  `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` to run Pygame in
  headless mode. Tests that initialize Pygame must account for this
  (e.g., use a pytest fixture for `pygame.init()`/`pygame.quit()`).
- 2026-04-13: `[integrated]` `pytest.ini` adds `.`, `src`, and
  `src/entity` to `pythonpath` — imports in tests resolve against these
  roots.
- 2026-04-13: `[not yet integrated]` The `requirements.txt` includes
  Django and several unrelated packages that are not used by the game
  itself; they appear to be leftover from the original development
  environment. Agents should not assume every listed dependency is
  required at runtime.
- 2026-04-13: `[integrated]` Room save/load uses JSON files
  validated against schemas in `schemas/`. When adding new persistent
  data, a matching JSON schema should be created or updated.
- 2026-04-13: `[not yet integrated]` The `run.sh` script runs `git
  pull` before starting the game — it should not be used in CI or
  automated environments as it will attempt to fetch from the remote.
- 2026-04-16: `[not yet integrated]` When writing tests that use
  `isinstance` checks against classes also imported in source code
  (e.g., `worldScreen.py` imports `from entity.stone import Stone`),
  the test must import from the same module path (`from entity.stone
  import Stone`) rather than `from src.entity.stone import Stone`.
  Otherwise `isinstance` comparisons will fail because Python treats
  them as different classes.
- 2026-04-16: `[not yet integrated]` In this sandbox, installing the pinned
  `pygame==2.1.2` from `requirements.txt` failed on Python 3.12 due to source-build
  compatibility issues; local validation needed a compatible wheel (`pygame==2.5.2`)
  to run tests.
- 2026-04-17: `[not yet integrated]` When writing tests that use `pygame.display`
  with the dummy video driver, `pygame.display.set_mode()` may return a surface
  with `(0, 0)` size if pygame was previously quit and reinitialised. Use
  `unittest.mock.patch.object(pygame.display, "set_mode")` with `MagicMock`
  surfaces to avoid dependency on the dummy driver's display subsystem.
- 2026-04-18: `[not yet integrated]` The `saveCurrentRoomAsPNG` method
  draws the room at (0, 0) on the main display and captures it as a
  screenshot. When `set_clip()` is active (e.g., for game area
  clipping), the draw is clipped and the capture includes letterbox
  bars. The method must be called before any clip is set, and the
  capture size must match the actual room area (game area dimensions),
  not the full display size.
- 2026-04-18: `[not yet integrated]` The hotbar in `worldScreen.py`
  uses fixed pixel values for layout: item slots are 50×50px with 5px
  gaps, positioned at `y - 150` from the display bottom. The bar
  background extends from `y - 155` to `y - 95`. Any HUD element
  positioned near the bottom of the screen must account for this
  fixed region to avoid overlap.
- 2026-04-18: `[not yet integrated]` The `test_inventoryJsonReaderWriter.py`
  test file globally patches `config.pygame.display = MagicMock()` (line 6)
  which replaces `pygame.display` with a MagicMock for the entire test
  session. Any tests that run after this module and call
  `pygame.display.set_mode()` will receive a MagicMock instead of a real
  Surface. Screen tests should use `MagicMock` for `gameDisplay` directly
  (passing it to `Graphik(gameDisplay)` with explicit `get_width`/
  `get_height`/`get_size` return values) to avoid this pollution.
- 2026-04-18: `[not yet integrated]` All user-facing button labels use
  Title Case (e.g., "Play", "Back", "New Game", "Debug Mode"). Status
  messages use sentence case with the first word capitalized (e.g.,
  "Picked up Apple", "Inventory full"). Entity names in status messages
  are used verbatim from `getName()` without extra quotes. Future agents
  should follow this convention when adding new UI text.
- 2026-04-18: `[not yet integrated]` HUD element dragging uses
  middle-click (mouse button 2) to avoid conflicting with left-click
  (gather/hotbar pick-up) and right-click (place/hotbar management).
  The `HudDragManager` in `src/ui/hudDragManager.py` manages all
  drag state centrally. Each HUD element is registered with a callable
  that returns its default `pygame.Rect`. Offsets are stored per
  element and applied at draw time. Position clamping ensures at least
  20 % of an element remains visible on screen.
- 2026-04-18: `[integrated]` Many constructor parameters in the
  codebase lack type hints (e.g., `config` in `TickCounter`, `Stats`,
  `MapImageUpdater`, and `Map`). When adding DI or auto-wiring, type
  hints must be added to enable automatic resolution. Adding type hints
  is considered a wiring-only change, not a business-logic change.
- 2026-04-18: `[integrated]` Several classes require primitive
  values or runtime state in their constructors (e.g., `Player` needs
  `tickCounter.getTick()`, `Map`/`RoomFactory` need `config.gridSize`,
  `SaveSelectionScreen` needs a callback). These cannot be auto-wired
  and require factory functions or explicit instance registration.
- 2026-04-18: `[integrated]` The `test_worldScreen_pushStone.py`
  test creates `WorldScreen` using `__new__` (bypassing `__init__`) and
  manually sets attributes. This pattern means constructor changes to
  `WorldScreen` won't break those tests, but it also means those tests
  don't exercise the constructor or DI wiring.
- 2026-04-19: `[integrated]` The project uses a lightweight DI container
  (`src/di/`) for dependency management. New classes should use the
  `@component` decorator (from `src/appContainer.py`) instead of being
  manually constructed. Factory registrations for types needing primitives
  go in `src/bootstrap.py`. The container is a module-level singleton
  that persists across game restarts; `createContainer()` calls
  `resetSingletons()` to clear cached instances on each restart.
- 2026-04-19: `[not yet integrated]` The `Map` class uses a
  `threading.Lock` (`_lock`) to protect concurrent access to `rooms` and
  `_roomIndex`. Any code that reads or mutates these collections (including
  `getRoom`, `addRoom`, `generateNewRoom`, and `hasRoom`) acquires the lock.
  Background room pre-loading via `RoomPreloader` relies on this thread
  safety. Future modifications to `Map` that touch `_roomIndex` or `rooms`
  should also acquire `_lock`.
- 2026-04-19: `[not yet integrated]` The `MapImageUpdater` uses a
  background `ThreadPoolExecutor` (max 1 worker) to run Pillow-based map
  compositing off the main thread. A `_updateInProgress` flag prevents
  concurrent updates from piling up. The public `updateMapImage()` method
  is now non-blocking — it delegates to `updateMapImageAsync()`. The
  `saveCurrentRoomAsPNG()` method in `worldScreen.py` still runs on the
  main thread because it uses pygame rendering, which is not thread-safe.
- 2026-04-19: `[not yet integrated]` The `KeyBindings` instance is registered
  via `registerInstance()` in `roam.py` rather than using `@component`,
  because it needs to call `loadFromConfig()` with runtime config values
  before being injected. Classes that depend on `KeyBindings` (e.g.,
  `WorldScreen`, `ControlsScreen`) receive it via DI auto-wiring.
- 2026-04-19: `[not yet integrated]` When saving room state to JSON on a
  background thread, the JSON dict must be prepared on the main thread
  first (`generateJsonForRoom()`) to avoid `RuntimeError: dictionary
  changed size during iteration`. Only the file write should happen
  in the background.
- 2026-04-19: `[not yet integrated]` The `MapImageUpdater.roompngsLock`
  is shared between the map image updater (background compositing) and
  `WorldScreen._saveSurfaceToDisk()` (background PNG writes) to prevent
  `clearRoomImages()` from racing with concurrent PNG writes to the
  same directory.
- 2026-04-19: `[not yet integrated]` The `inventoryJsonReaderWriter.py`
  module uses entity registry dicts (`_SIMPLE_ENTITY_CONSTRUCTORS`,
  `_LIVING_ENTITY_CONSTRUCTORS`, `_FOOD_ENTITY_CLASSES`) at module level
  to map class name strings to constructors. When adding a new entity
  type, it must be added to the appropriate registry in both this file
  and `roomJsonReaderWriter.py` to support save/load.
- 2026-04-19: `[not yet integrated]` Screenshot functionality is
  centralized in `src/screen/screenshotHelper.py` with `takeScreenshot()`
  and `captureScreen()` functions. Screen classes should import from this
  module rather than implementing their own capture logic.
- 2026-04-19: `[not yet integrated]` `WorldScreen`, `RoomPreloader`, and
  `MapImageUpdater` are DI singletons whose `shutdown()` methods shut down
  their `ThreadPoolExecutor` instances. Because the same instances survive
  screen transitions (e.g., WorldScreen → InventoryScreen → WorldScreen),
  `shutdown()` must recreate the executor after draining it. Failing to do
  so causes `RuntimeError: cannot schedule new futures after shutdown` on
  the next `run()` call.
- 2026-04-19: `[not yet integrated]` The `src/logging/` package name
  conflicts with Python's standard library `logging` module when
  `src` is on `sys.path` (as configured in `pytest.ini`). The
  structured logging module was renamed to `src/gameLogging/` to avoid
  shadowing the stdlib. Future agents should avoid naming packages after
  standard library modules.
