# Changelog

All notable changes to this repository are documented here.
Commits are grouped by date and summarized; AI-agent sessions are
logged in detail below.

## Commit History Summary

| Date | Commits | Summary |
|------|---------|---------|
| 2026-04-16 | 2 | feat: Add excrement spawning by living entities that decays into grass over time; test: Add unit tests for world package (RoomType, TickCounter, Room, RoomFactory, Map) |
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
- 2026-04-13: `[not yet integrated]` Room save/load uses JSON files
  validated against schemas in `schemas/`. When adding new persistent
  data, a matching JSON schema should be created or updated.
- 2026-04-13: `[not yet integrated]` The `run.sh` script runs `git
  pull` before starting the game — it should not be used in CI or
  automated environments as it will attempt to fetch from the remote.
