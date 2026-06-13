# Changelog

All notable changes to this repository are documented here.
Commits are grouped by date and summarized; AI-agent sessions are
logged in detail below.

## Commit History Summary

| Date | Commits | Summary |
|------|---------|---------|
| 2026-06-13 | 1+ | refactor: Renderer image loading/scaling, Phase 2b-1 (frontend-abstraction epic #433) — add `Renderer.loadImage` (cached by path, with a visible magenta placeholder on load failure) and `Renderer.scaleImage`; migrate the inventory/chest/world hotbar+cursor item icons (and the minimap scale) from `pygame.transform.scale`/`item.getImage()` to `renderer.loadImage(item.getImagePath())` + `renderer.scaleImage`. No `pygame.transform` left in those screens (codex + the dynamic minimap *load* intentionally retained). +3 smoke tests; 642 passing (part of #436 — entity/Room image ownership follows in 2b-2) |
| 2026-06-13 | 1+ | refactor: Backend-neutral geometry type, Phase 2a (frontend-abstraction epic #433) — add `ui/geometry.Rect` (mutable x/y/width/height + `collidepoint`/`move`/`copy`) and replace the 5 `pygame.Rect` construction sites in `ui/status`, `ui/energyBar`, `worldScreen` HUD layout; `HudDragManager` was already backend-neutral. `ui/status` and `ui/energyBar` no longer import pygame at all. +7 tests incl. a `HudDragManager`×`Rect` integration test (part of #436 — image abstraction follows in 2b) |
| 2026-06-13 | 1+ | refactor: Renderer output seam, part 1b — `worldScreen` + `EnergyBar` (closes #435, frontend-abstraction epic #433) — migrate the last and largest rendering consumer off the raw pygame surface; the two `display = getGameDisplay()` overlay locals and the minimap/hotbar/day-night blits now go through `Renderer`; add `getRenderTarget`/`setRenderTarget` to the interface for the off-screen room-PNG render (replacing a direct `graphik.gameDisplay` swap). With this, no `src/screen/` or `src/ui/` file calls `getGameDisplay()`/`pygame.display` directly. +1 smoke test (render-target redirect); 633 passing |
| 2026-06-13 | 1+ | refactor: Renderer output seam, part 1a (frontend-abstraction epic #433) — add `rendering/Renderer` (backend-neutral drawing interface) + `PygameRenderer` that *composes* the vendored `Graphik` (never modifies it); migrate the 9 non-world screens + `ui/status` off the raw pygame surface onto `getDisplaySize`/`getDisplayWidth`/`getDisplayHeight`/`clearScreen`/`present`/`drawImage`/`setClipRegion`/`setCaption`/`captureScreenshot`, so those files no longer call `getGameDisplay()`/`pygame.display`; +9 tests incl. a headless draw-path smoke and an interface-contract test (part of #435 — `worldScreen` follows in 1b) |
| 2026-06-13 | 1+ | refactor: Introduce a shared UI color palette (`src/ui/palette.py`) — named `(R, G, B)` constants (a 10-step grayscale ramp + primary accents + `DEBUG_MAGENTA`) replacing 152 inline RGB literals across the 11 screens, `ui/status` + `ui/energyBar`, and the `DrawableEntity` missing-asset fallback; backend-neutral so a future text/web renderer can reinterpret colors in one place; +4 tests (closes #434 — Phase 0 of the frontend-abstraction epic #433) |
| 2026-06-12 | 1+ | feat: Add craftable storage containers (`Chest`) — new `Chest` entity (solid, `StorableInventory`-backed, placeholder `chest.png`), a `6× OakWood` recipe, a right-click `ChestScreen` that moves items between the player and the chest via a cursor slot, room-JSON save/load of chest contents (the gravestone `storedInventory` path generalized to any `StorableInventory`), and an empty-only `canBePickedUp` guard so a non-empty chest can't be picked up; +27 tests (closes #346) |
| 2026-06-07 | 1+ | test: Add unit coverage for `WorldScreenPersistence` (previously untested) — player-attributes round-trip + missing/corrupt-file no-op, player-location save JSON shape + missing/room-not-found/happy-path load, inventory save/load delegation, and room-save path; +11 tests (closes #364) |
| 2026-06-07 | 1+ | fix: Make all save writes atomic (write-atomicity half of #370, closes it) — add `writeJsonAtomically(path, data)` to `src/jsonPersistence.py` (write to a temp file in the same dir, flush+fsync, `os.replace` over the target; temp cleaned up and error re-raised on failure) and route every JSON writer through it (`stats`, `tickCounter`, `codex`, `goals`, `inventory`, `roomJsonReaderWriter`, `worldScreenPersistence` ×3, and `WorldScreen._writeJsonToFile`/`_doSave`) so a save interrupted mid-write can no longer truncate the previous good file; +4 tests (closes #370) |
| 2026-06-07 | 1+ | fix: Tolerate corrupt/truncated save files on load (load-resilience half of #370) — add `src/jsonPersistence.py` (`readJsonFile(path, default)`, which catches `JSONDecodeError`/`OSError`/`UnicodeDecodeError`, logs the path, and returns the default) and route the previously-unguarded startup loaders through it (`stats.load`, `tickCounter.load`, `worldScreenPersistence` player location/attributes, `roomJsonReaderWriter.loadRoom`, `inventoryJsonReaderWriter.loadInventory`); `map.getRoom` now treats an unreadable room file as absent so a fresh room is generated instead of crashing every launch; +7 tests (addresses #370; atomic-write half to follow) |
| 2026-06-07 | 1+ | refactor: Cache JSON validation schemas instead of re-reading them on every save/load — add `src/schemaCache.py` (`loadSchema(filename)`, `lru_cache`d) and route the four classes that re-opened+re-parsed their schema in both `save()` and `load()` (`stats.py`, `tickCounter.py`, `goalsJsonReaderWriter.py`, `codexJsonReaderWriter.py`) through it, removing the per-operation disk read and the duplicated load-schema boilerplate; +3 tests (closes #411) |
| 2026-06-07 | 1+ | robustness: Log once when the minimap image fails to load — the `except (FileNotFoundError, pygame.error)` in `WorldScreen.drawMiniMap` previously swallowed the failure silently; it now warns via the structured logger on the good->failed transition (throttled by a `_miniMapLoadFailed` flag, reset on a successful load), keeping the existing fallback-to-cached-or-return behavior; +3 tests (closes #412) |
| 2026-06-07 | 1+ | docs: Sync the config/docs sources of truth — drop the dead `black`/`white` keys from `config.yml` and add the missing `cropGrowthTicks` (static) and `pushableStone` (dynamic toggle) keys the code already reads; correct `copilot-instructions.md` (add the `crafting/`, `codex/`, `gameLogging/` packages to the repository layout, fix the Pillow version to `>=10.0.0`, refresh the stale `0.8.0-SNAPSHOT` version marker to `0.11.0-SNAPSHOT`) (closes #362, #365) |
| 2026-06-07 | 1+ | refactor: Add `Config.getRoomsDirectory()` as the single source of truth for the `<saveDir>/rooms` path — `getRoomFilePath` and both makedirs sites (`roomJsonReaderWriter`, `worldScreenPersistence`) now go through it instead of hand-concatenating `"/rooms"` (closes #409) |
| 2026-06-07 | 1+ | refactor: Replace the 10 near-identical hotbar `elif` branches in `InventoryScreen.handleKeyDownEvent` with a data-driven `_handleHotbarKey` loop (preserving the `hotbar_0 → slot 9` wrap); +3 tests (closes #410) |
| 2026-06-07 | 1+ | fix: Correct release versioning — `version.txt` had been stale at `0.8.0-SNAPSHOT` while `0.9.0`/`0.10.0` were already released, leading to an erroneous `v0.9.0` tag/release (now deleted); set `version.txt` to `0.11.0-SNAPSHOT`, switch the release workflow to the repo's bare-number tag convention (`0.11.0`, not `v0.11.0`), and fix `UpdateChecker` to read the `/releases` list (every Roam release is a GitHub pre-release, so `/releases/latest` 404s) |
| 2026-06-07 | 1+ | feat: In-game update notifier + version plumbing — bundle `version.txt` in `roam.spec` and stamp the release tag into it (so packaged builds know their version, previously blank), add `Config.getVersion()`, and add an `UpdateChecker` that checks GitHub Releases on a daemon thread (fail-silent, `checkForUpdates` config toggle) and shows a "press U to download" banner on the main menu (closes #413, #414) |
| 2026-06-07 | 1+ | fix: Prevent stacking floor tiles — `executePlaceAction` now blocks placing a `WoodFloor`/`StoneFloor` where a floor already exists (via a new `locationContainsFloor` helper), setting "A floor is already here" and consuming no item; +2 tests (closes #345) |
| 2026-06-07 | 1+ | ux: install.ps1 — drop `--quiet` so dependency-install progress is visible (no more "frozen" hang) and pip's real error shows on failure; the completion message now warns that shortcuts are anchored to the folder and prints where saves/settings/screenshots live (`%APPDATA%\Roam`) (closes #400, #401) |
| 2026-06-07 | 1+ | docs: Lead the README with the recommended prebuilt download (no Python), reframe the clone steps as "Run from Source (for developers)", and rename the `install.ps1` section to a "setup script" distinct from the `RoamSetup.exe` installer — fixes the information scent and the two-things-both-called-"wizard" naming collision (closes #404) |
| 2026-06-07 | 1+ | test: Add unit-test coverage for `Room.tickExcrement` (spawn/decay/grass-blocking branches), `Inventory.hasAvailableSlotFor` (empty/matching-stack/full), and `MapImageGenerator` coordinate + bounds math; align `test_room.py` entity imports to the production `entity.*` root so `isinstance` checks match room-created entities; +18 tests (issues #372, #367) |
| 2026-06-07 | 1+ | chore: Bump GitHub Actions to their Node 24 majors across all workflows — `actions/checkout` v4→v6, `actions/setup-python` v5→v6, `actions/upload-artifact` v4→v7 — clearing the Node.js 20 deprecation warnings |
| 2026-06-07 | 1+ | feat: Add a release workflow — on a `v*` tag push, build and attach `Roam-<version>-Setup.exe`, a portable Windows zip, and `Roam-<version>.dmg` to an auto-generated GitHub Release (so distributables persist beyond the ~90-day CI-artifact retention) |
| 2026-06-07 | 1+ | feat: Package Roam for macOS (#394) — add a macOS-only PyInstaller `BUNDLE` step to `roam.spec` (`dist/Roam.app`), route user data to `~/Library/Application Support/Roam` on macOS (`Config.getUserDataDirectory`/`getSavesBaseDirectory`), and add a `macos-latest` CI job that builds the `.app`, runs `--selftest`, builds a `.dmg`, and uploads both |
| 2026-06-07 | 1+ | feat: Add a Windows setup wizard installer (#385, phase 2) — `roam.iss` Inno Setup script wrapping the PyInstaller build into `RoamSetup.exe` (installs to Program Files, Start Menu + optional Desktop shortcuts, uninstaller/Add-Remove Programs); CI builds the installer and runs a silent install → frozen `--selftest` → uninstall round-trip and uploads `RoamSetup.exe`. Completes #385 |
| 2026-06-07 | 1+ | feat: Store all writable user data under %APPDATA% on Windows — add `Config.getUserDataDirectory()` and route config + screenshots through it (joining saves, which already used %APPDATA%), seed the writable `config.yml` from the bundled defaults on first run, and relocate screenshots; lets config/keybinding writes and screenshots work when installed to a read-only location like Program Files |
| 2026-06-07 | 1+ | feat: Package Roam as a standalone Windows executable (#385, phase 1) — add a PyInstaller `roam.spec` bundling the game + `assets`/`schemas`/`config.yml`, a `src/appPaths.py` helper that chdir's into the bundle when frozen so relative asset/schema paths resolve, a `--selftest` flag, and a CI `package` job that builds `dist/Roam/Roam.exe` on Windows and smoke-tests the frozen bundle; route `Config.getConfigFilePath()` through the bundle dir |
| 2026-06-07 | 1+ | fix: Make Roam installable on modern Python — replace the stale `pip freeze` in `requirements.txt` (which pinned `pygame==2.1.2`, with no wheels for Python 3.11+, plus exact transitive pins) with the four direct runtime deps + two test deps using lower bounds; raise the `windows-installer` CI job from Python 3.10 back to 3.12 to prove the install works on a current interpreter |
| 2026-06-07 | 1+ | feat: Store saves under %APPDATA% on Windows — add `Config.getSavesBaseDirectory()`/`getDefaultSaveDirectory()` as the single source of truth for the save root (`%APPDATA%\Roam\saves` on Windows, repo-relative `saves/` elsewhere), wire both `Config.pathToSaveDirectory` and `SaveSelectionScreen.savesBaseDirectory` to it, unpin `pathToSaveDirectory` in `config.yml` so the platform default applies, and document the location in the README |
| 2026-06-07 | 1+ | ci: Smoke-test the Windows installer on CI — add `-NonInteractive`/`-NoLaunch` switches to `install.ps1` (suppress prompts and skip launch for automation) and a `windows-latest` GitHub Actions job that runs the wizard non-interactively, asserts it generated `icon.ico` plus Desktop/Start Menu shortcuts, and runs the test suite on Windows; fix: guard `TickCounter` against a `ZeroDivisionError` on Windows' coarse clock (the bug the new job caught on its first run) |
| 2026-06-07 | 1+ | feat: Add Windows installation wizard — `install.ps1` PowerShell wizard (checks Python/pip, installs pygame + requirements.txt, converts the bundled PNG icon to `.ico` via Pillow, and creates Desktop/Start Menu shortcuts) plus a double-clickable `run.bat` launcher; README documents the wizard; the Windows analogue of `run.sh` (closes #383) |
| 2026-04-20 | 7+ | refactor: Comprehensive Clean Code refactoring — DRY entity hierarchy (move `isSolid`/`solid` to `DrawableEntity` base, remove duplication from 20+ subclasses); DRY `ConfigScreen` (replace 9 toggle methods with data-driven `_toggleConfigAttribute`); DRY `OptionsScreen` (add `_switchToScreen` helper, data-driven menu buttons); extract `WorldScreenPersistence` and `pickupableEntities` modules; decompose 14 long methods into focused helpers; consolidate 3 cooldown methods; extract `_tryHarvestCrop` from gather action; DRY hotbar selection indicator; remove ~40 redundant comments; add logging to silent `except` blocks; rename cryptic `highestmtps` variable; DI audit — register `WorldScreenPersistence` with `@component`, inject `RoomFactory` and `RoomJsonReaderWriter` factory into `Map` via DI instead of manual instantiation; run Black/autoflake; all 409 tests pass |
| 2026-04-20 | 4+ | refactor: Clean Code refactoring of worldScreen.py — Extract helper classes (`WorldScreenPersistence`, `pickupableEntities`) and decompose long methods (`draw`, `run`, `changeRooms`, `executePlaceAction`, `handleKeyDownEvent`, `handleMouseDownEvent`); consolidate cooldown methods; simplify mouse wheel with modulo; remove 14 unused entity imports and `jsonschema` import |
| 2026-04-20 | 3+ | feat: Add day/night cycle with craftable light sources — `DayNightCycle` class with sine-curve overlay opacity, phase detection, and radial light mask caching; `Torch` entity (craftable from OakWood + CoalOre, yields 2) with `lightRadius=6`; `Campfire` updated with `lightRadius=8`; per-pixel alpha overlay with opacity-scaled `BLEND_RGBA_MIN` light halos in `WorldScreen.draw()` for smooth dusk/dawn lighting; light source collection iterates all entities per location; configurable `dayNightCycleEnabled` and `dayNightCycleLengthTicks` (default 54000 = 30 min at 30 tps); toggle in `ConfigScreen`; debug info; Torch registered in entity registries; 23 new unit tests |
| 2026-04-20 | 2+ | feat: Add Codex screen — records living entities the player has encountered; `Codex` class with discover/hasDiscovered/getDiscoveredEntities registered as `@component`; `CodexJsonReaderWriter` for JSON persistence with `schemas/codex.json` schema; discovery triggered on room transitions and initialization; status message on first discovery; `CodexScreen` with scrollable list showing discovered entities with textures and `???` for undiscovered; configurable `L` keybinding via `KeyBindings`; `CODEX_SCREEN` added to `ScreenType`; integrated in `Roam.run()` and `WorldScreen`; codex saved/loaded alongside stats and tick count; README updated with `L` keybinding; 18 new unit tests |
| 2026-04-20 | 1+ | feat: Add farming system — WheatSeed, YoungCrop, MatureCrop, Wheat entities; crop growth via tickCrops; planting seeds on grass via right-click; harvesting mature crops via left-click; crafting recipe (Grass → WheatSeed ×3); persistence for crop tickPlanted; all entity types registered in room and inventory JSON reader/writers; cropGrowthTicks config option; unit tests for entities, growth, crafting, and serialization |
| 2026-04-19 | 12+ | feat: Add structured logging with structlog — create `src/gameLogging/logger.py` with `getLogger()` and `redact()` helpers, register `LoggerFactory` singleton in DI container, add `LOG_LEVEL`/`LOG_FORMAT` config support, replace all `print()` calls in source files with structured logger calls, expand instrumentation to config.py (startup config values at DEBUG), roam.py (screen transitions, shutdown at INFO), worldScreen.py (room transitions, initialization at INFO), map.py (room loading/generation at INFO), roomFactory.py (room creation, entity spawning at DEBUG), roomPreloader.py (background preloading at DEBUG, failures at ERROR), stats.py (save/load at INFO), saveSelectionScreen.py (save selection/creation/deletion at INFO), inventory.py (item operations at DEBUG); fix incorrect log levels in worldScreen.py (entity edge cases from ERROR to DEBUG); docs: Create `LOGGING.md` documenting log levels, env vars, field conventions, and redaction policy |
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

### 2026-06-13 — Renderer image loading/scaling, Phase 2b-1 (issue #436, epic #433)
- **Context:** Phase 2b moves image handling off direct pygame so a non-pygame frontend can supply its own. Investigation showed the genuinely backend-neutral operations are image *loading by path* and *scaling* (entity/item icons); per-pixel light-mask/overlay compositing (`dayNightCycle`, the world overlays with `BLEND_RGBA_*`) is inherently raster-specific and stays pygame, and `mapImageGenerator` is PIL-based (out of scope). 2b is split: **2b-1** (this PR) adds the renderer image API and migrates the screen-layer icons; **2b-2** migrates `Room` + removes `DrawableEntity.getImage()`.
- **`Renderer`/`PygameRenderer`:** add `loadImage(path)` — caches by path (game assets are static) and, on a failed load, logs once and returns a 32×32 `DEBUG_MAGENTA` placeholder (the same fallback `DrawableEntity` used) so a missing asset is visible rather than fatal — and `scaleImage(image, size)`.
- **Migration:** `inventoryScreen` (panel + cursor), `chestScreen` (panel + cursor), and `worldScreen` (hotbar + cursor) now build item icons via `renderer.loadImage(item.getImagePath())` + `renderer.scaleImage(...)` instead of `item.getImage()` + `pygame.transform.scale`. The minimap's *scale* also moved to `scaleImage`; its bespoke periodic-reload *load* stays pygame (it re-reads a regenerated PNG, so the path-keyed cache must not apply). `codexScreen` keeps its own image handling — it returns `None` for an undiscovered entity (shows `???`), which is different from the magenta-placeholder semantics, so migrating it would change behavior.
- **Tests (+3):** smoke tests for `loadImage` (loads a real asset, caches by path), the missing-asset magenta placeholder, and `scaleImage` resizing.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 642 passed (was 639; +3). Headless smoke exercises the new methods; **live item/icon rendering is for the maintainer smoke-run** (user is smoke-testing each 2b step).
- **Learning Log:** `[integrated]` — recognized that not every pygame call is equally abstractable: image load/scale are backend-neutral and worth an interface method, but per-pixel alpha-blend compositing and a PIL-based map generator are not, and forcing them behind the Renderer would be over-abstraction. Also: a path-keyed asset cache is correct for static assets but wrong for a periodically-regenerated file (the minimap), so that load was deliberately left uncached.

### 2026-06-13 — Backend-neutral geometry type, Phase 2a (issue #436, epic #433)
- **Context:** Phase 2 removes the remaining pygame value types from backend-agnostic code. Part 2a covers geometry; the image/surface abstraction is 2b. HUD layout and hit-testing used `pygame.Rect`, which forced pygame into otherwise frontend-neutral layout code.
- **`src/ui/geometry.py` (new):** `Rect` — mutable `x`/`y`/`width`/`height` plus `collidepoint`/`move`/`copy`/`__eq__`. Mirrors only the slice of the `pygame.Rect` API the codebase actually uses on these rects (surveyed: 5 construction sites; `collidepoint`, `x/y/width/height`). Edge/center accessors were intentionally omitted (no consumer needs them, and the codebase avoids property decorators).
- **Adoption:** replaced the 5 `pygame.Rect(...)` constructions in `ui/status.getDefaultRect`, `ui/energyBar.getDefaultRect`, and `worldScreen._getHotbarDefaultRect`/`_getMinimapDefaultRect`. The constructed rects flow only into `HudDragManager` (already duck-typed/backend-neutral) and layout math — never into a pygame API — so no boundary conversion is needed (`worldScreen.setClipRegion` uses `getGameAreaRect`, the vendored `Graphik`'s own `pygame.Rect`, which is unchanged). As a result `ui/status` and `ui/energyBar` no longer import pygame at all.
- **Tests (+7):** `tests/ui/test_geometry.py` covers construction, inclusive-tl/exclusive-br `collidepoint`, non-mutating `move`, `x/y` mutability, equality/copy, and a `HudDragManager`×`Rect` integration test proving the drag manager works against the new type.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 640 passed (was 633; +7). `Rect` is pure data, so behavior is fully unit-covered; no live-window dependency this phase.
- **Learning Log:** `[integrated]` — no new convention; surveyed the real `pygame.Rect` API surface before sizing the replacement (avoided reimplementing the whole class) and confirmed via grep that constructed rects never cross a pygame boundary, so the swap needed no conversion shims.

### 2026-06-13 — Renderer output seam, part 1b — worldScreen + EnergyBar (closes #435, Phase 1 of epic #433)
- **Context:** Completes Phase 1 by migrating the last rendering consumers — the 2120-line `worldScreen` and the `EnergyBar` HUD widget — onto the `Renderer` interface introduced in 1a. After this, no file under `src/screen/` or `src/ui/` reaches the raw pygame display surface.
- **`src/screen/worldScreen.py`:** all `getGameDisplay()`/`gameDisplay`/`pygame.display.update`/`takeScreenshot` reach-throughs now go through `self.renderer`. The two overlay helpers (`_drawPauseOverlay`, `_drawDeathOverlay`) that did `display = getGameDisplay(); display.blit(dim, ...)` now use `getDisplaySize()` + `drawImage()`. The day/night light overlay (`self._dayNightOverlay`, an off-screen surface the screen owns) is intentionally left as direct pygame — it is composited onto, not the display, and belongs to the Phase 2 Image abstraction.
- **Off-screen room PNG:** `saveCurrentRoomAsPNG` previously swapped `self.graphik.gameDisplay` to an off-screen surface so `Room.draw` (which renders through the shared `Graphik`) would target it. Added `getRenderTarget()`/`setRenderTarget(target)` to `Renderer`/`PygameRenderer` to express this save/redirect/restore cleanly through the interface instead of mutating a renderer attribute.
- **`src/ui/energyBar.py`:** migrated to `Renderer` (`getDisplaySize`); `pygame.Rect` construction stays (geometry is Phase 2).
- **Tests:** `tests/screen/test_worldScreen_minimap.py` repointed (`ws.renderer`); added a render-target smoke test asserting `setRenderTarget` redirects drawing to an off-screen surface (and leaves the window untouched) and `getRenderTarget` round-trips. The interface-contract test from 1a now also covers `worldScreen`'s renderer calls.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 633 passed. `grep -rn 'getGameDisplay\|pygame.display' src/screen src/ui` → no matches outside the renderer. As with 1a, the headless smoke exercises draw paths but the live window is not runnable here — **visual correctness of `worldScreen` is unverified** and flagged for a maintainer smoke-run.
- **Learning Log:** `[integrated]` — reused the 1a dummy-driver-smoke + static-contract approach. The one genuinely non-mechanical site (the `gameDisplay` attribute swap for off-screen rendering) was promoted to an explicit interface method pair rather than leaking the surface attribute through the renderer; worth noting that "render to an off-screen target" is a recurring need a Renderer interface should own.

### 2026-06-13 — Renderer output seam, part 1a (issue #435, Phase 1 of frontend-abstraction epic #433)
- **Context:** Phase 1 of epic #433 closes the largest pygame leak: screens reach past the `Graphik` facade to the raw pygame display surface (`getGameDisplay().fill/blit/set_clip/get_size`, `pygame.display.update`). This introduces a backend-neutral `Renderer` interface and migrates screens onto it. Per the agreed plan, Phase 1 is split into **1a** (this PR — the `rendering/` module + the 9 non-world screens + `ui/status`) and **1b** (`worldScreen` + `EnergyBar`), to stay reviewable.
- **`src/rendering/renderer.py` (new):** `Renderer(ABC)` — the drawing contract: `getDisplaySize`/`getDisplayWidth`/`getDisplayHeight`, `clearScreen`, `present`, `setCaption`, `drawRectangle`/`drawText`/`drawButton`/`drawImage`, `getGameAreaRect`, `setClipRegion`, `captureScreenshot`. Colors are the `ui/palette` tuples.
- **`src/rendering/pygameRenderer.py` (new):** `PygameRenderer(Renderer)` **composes** the vendored `Graphik` (drawing primitives delegate to it) and owns the surface lifecycle (clear/present/clip/blit/screenshot/caption). The vendored `src/lib/graphik/` is left untouched — the composition approach replaces the plan's original "make Graphik implement Renderer".
- **Migration (10 files):** the 9 screens that are not `worldScreen` (`mainMenu`, `saveSelection`, `options`, `config`, `controls`, `codex`, `stats`, `inventory`, `chest`) and `ui/status` now depend on `Renderer` (constructor param + `self.renderer`) instead of `Graphik`; all `getGameDisplay()`/`gameDisplay`/`pygame.display`/`takeScreenshot` reach-throughs in those files were rewritten to interface calls. `Status` is `@component` and DI-resolved independently, so it migrates safely while `worldScreen` still injects `Graphik` (both wrap the same surface).
- **`src/roam.py`:** registers `PygameRenderer(graphik)` under the `Renderer` type so `@component` screens auto-wire it; the `SaveSelectionScreen` factory now resolves `Renderer`.
- **Tests (+9):** `tests/conftest.py` gains a `test_renderer` fixture (PygameRenderer-spec mock) registered alongside `test_graphik`; the five screen/status tests that built a mock `Graphik` were repointed at the renderer (real `Graphik` wrapped in `PygameRenderer`, or a renderer mock). New `tests/rendering/`: a **contract** test (statically asserts every `self.renderer.X(` call across `screen/` + `ui/` resolves to a `Renderer` method, and that `PygameRenderer` is concrete) and a **headless smoke** test that drives every renderer method and the `MainMenuScreen` draw path against a real offscreen SDL-dummy surface.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 632 passed (was 625; +7 net after repointing 5 existing tests). The headless smoke exercises the migrated draw paths (which the logic-only screen tests never invoked), but the live pygame window is not runnable here, so **visual correctness is unverified** — surfaced for a maintainer smoke-run.
- **Learning Log:** `[integrated]` — the screen *draw* paths had no test coverage (existing screen tests assert logic via mocked Graphik and never call `draw()`/`run()`); a headless SDL-dummy smoke plus a static interface-contract test close most of that gap without a live window. Candidate `create-dev-loop.md` rule: when a refactor changes uncovered draw/render code, add a dummy-driver smoke that actually executes it rather than relying on the mock-based logic tests.

### 2026-06-13 — Shared UI color palette (issue #434, Phase 0 of frontend-abstraction epic #433)
- **Context:** First phase of the frontend-abstraction effort (epic #433, plan in `docs/rendering-abstraction-plan.md`), whose goal is to let Roam run behind multiple frontends (pygame today; text/web later). Inline `(R, G, B)` literals scattered across the rendering consumers are a blocker: a non-pygame renderer needs a single place to reinterpret colors. This phase extracts a shared palette; the `Renderer`/`InputSource` interfaces follow in later phases.
- **Architecture note:** the epic's plan originally said "make `Graphik` implement `Renderer`" and "delete its dead duplicate `__init__`", but `src/lib/graphik/` is a vendored library (do-not-modify without explicit instruction; on the do-not-auto-merge list). The approach was changed to **composition** — later phases will add a `PygameRenderer(Renderer)` adapter that wraps an untouched `Graphik` — so no vendored code is modified and phase PRs stay auto-mergeable. The dead-`__init__` cleanup was therefore dropped from this phase's scope (it lives in vendored code); the duplicate is harmless (Python keeps the second definition).
- **`src/ui/palette.py` (new):** named `(R, G, B)` constants — a 10-step grayscale ramp (`WHITE`…`BLACK`), primary accents (`RED`/`GREEN`/`BLUE`), and `DEBUG_MAGENTA` for the missing-asset placeholder. Kept as plain tuples so they stay backend-neutral. Mirrors the existing constants-module style of `ui/hotbarLayout.py` (`# @author`/`# @since` header).
- **Adoption (13 files, 152 literals):** exact 3-tuple RGB literals matching a palette entry were replaced with the named constant across all 11 screens, `ui/status`, `ui/energyBar`, and `entity/drawableEntity` (the magenta fallback). Each swap is provably behavior-preserving (literal → constant of the identical value). Context-specific one-offs not in the palette (e.g. `(255, 220, 120)`, `(255, 215, 73)`) were intentionally left inline. The 4-tuple `pygame.Rect(0, 0, 0, 0)` was correctly not matched.
- **Tests (+4):** `tests/ui/test_palette.py` — every public constant is a valid 3-channel `(0–255)` RGB tuple, the grayscale ramp is ordered light→dark, and `WHITE`/`BLACK` are the extremes.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 625 passed (was 621; +4). Note: colors are not exercised by the suite, but each replacement is value-identical, so correctness rests on equality rather than test coverage. Cannot run the live pygame window in this environment — visual rendering is unverified (mechanically risk-free here given value-identical swaps).
- **Learning Log:** `[integrated]` — applied the standing scoped-formatting rule (roam-dev-loop#3): `./format.sh` reformatted pre-existing Black/autoflake drift in five unrelated files (`gravestone.py`, `goals.py`, and three test files — the recurring drift that improvement #428 proposes to gate in CI); those were reverted so the diff carries only the palette change. No new convention; the composition-over-vendored-modification decision above is recorded in the epic plan rather than as a repo rule.

### 2026-06-12 — Add craftable storage containers (issue #346)
- **Context:** The only way to store items outside the player's inventory was to drop them in the world, which is lossy. #346 asked for a craftable, placeable `Chest` that opens on right-click, persists its contents across save/load, and cannot be picked up while non-empty. The codebase already had a `Gravestone` using the `StorableInventory` mixin and a full room-JSON `storedInventory` serialization path, so the persistence side was modeled directly on it.
- **`src/entity/chest.py` (new):** `Chest(DrawableEntity, StorableInventory)` — solid, `assets/images/chest.png` placeholder asset (a generated 32×32 RGBA chest icon). Mirrors `gravestone.py`.
- **Crafting:** added a `Chest` recipe (`6× OakWood`) to `RecipeRegistry`.
- **`src/screen/chestScreen.py` (new):** a `@component` screen (new `ScreenType.CHEST_SCREEN`) that draws the chest's stored inventory (top panel) and the player's inventory (bottom panel) and moves items between them through a cursor slot — left-click swaps/merges, click-outside drops (whole stack on left, one on middle), Esc / inventory-key closes. On close it returns held cursor items to the player and fires an on-close callback so the chest's room is saved. Wired in `roam.py` (resolve + dispatch branch passing the active chest, player inventory, and `WorldScreen.saveActiveChestRoom`).
- **`src/screen/worldScreen.py`:** right-clicking a placed `Chest` now opens it (`_openChest` — returns the cursor slot to inventory, records the active chest + its room, requests `CHEST_SCREEN`); the chest check sits alongside the existing gravestone interaction in `executePlaceAction`. Added `getActiveChest` / `saveActiveChestRoom`.
- **`src/world/roomJsonReaderWriter.py`:** `Chest` added to `entityConstructors`; the two gravestone-specific `storedInventory` branches (serialize + restore) were generalized to `isinstance(..., StorableInventory)` so both `Gravestone` and `Chest` round-trip through the same code. No `schemas/room.json` change — `storedInventory` is not enumerated there (the schema is permissive, consistent with the existing gravestone precedent).
- **`src/screen/pickupableEntities.py`:** `Chest` added to `PICKUPABLE_TYPES`, with a guard in `canBePickedUp` that returns `True` for a chest only when its stored inventory is empty, preventing item loss.
- **Tests (+27):** `test_chest.py` (entity + stored-inventory independence), a `Chest` recipe assertion, `Chest` added to the room-JSON parametrized round-trip plus two chest-specific serialize/round-trip tests, `test_pickupableEntities.py` (empty vs non-empty chest guard, and re-pickupable once emptied), `test_chestScreen.py` (cursor swap/merge/exchange, click-to-move geometry, drop-outside, and close-returns-cursor-and-calls-onClose), and `test_worldScreen_chest.py` (open sets active chest + requests `CHEST_SCREEN`, returns cursor items first, and the save-active-room callback).
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 591 passed (was 564; +27). Black-clean on all touched files (file-scoped; `worldScreen.py`'s pre-existing unrelated Black drift was left untouched per the standing scoped-formatting rule).
- **Learning Log:** `[not yet integrated]` — a workspace lesson worth a `create-dev-loop.md` rule: this machine had **two** clones of the repo (`/root/roam` and `/root/preponderous/roam`) at **different** commits. The branch was correctly created from updated `main` in one clone while edits were made (via absolute paths) in the other, which sat on a stale `main`. The fix was to generate a `git diff --binary` of the work and `git apply --3way` it onto the correctly-based branch. Candidate rule: confirm the working clone with `git rev-parse --show-toplevel` before editing, and verify the edited files' clone is the one holding the intended branch + base.

### 2026-06-07 — Add unit coverage for WorldScreenPersistence (issue #364)
- **Context:** `src/screen/worldScreenPersistence.py` handles core game-state persistence (player location / attributes / inventory, room save) but had zero test coverage. The issue's suggested `buildRoomPath` target was removed as dead code in #380 (noted in the issue comment), so the tests target the methods that actually exist.
- **`tests/screen/test_worldScreenPersistence.py` (new):** 11 tests resolving `WorldScreenPersistence` from the shared test DI container — player-attributes round-trip (energy preserved), and missing-file / corrupt-file loads that no-op (the latter a regression tie-in with the #370 load hardening); player-location save writes the expected `{roomX, roomY, locationId}` JSON, and load covers missing-file → `None`, room-not-found (`getRoom` → -1) → `None`, and the happy path (returns the room and calls `addEntityToLocation`); inventory save/load delegation to the injected `InventoryJsonReaderWriter` (sets inventory when present, keeps existing when `None`); and `saveRoomToFile` writes to `Config.getRoomFilePath`. Rooms/maps are `MagicMock`s; no real saves are touched (`tmp_path`).
- **Validation:** `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 564 passed (was 553; +11). Test-only change; no `src/` modified. Black-clean.
- **Learning Log:** `[integrated]` — no new convention; resolved via the DI container per the repo testing notes, and verified the issue's named surface (`buildRoomPath`) against source before writing (it was gone), targeting the real methods instead.

### 2026-06-07 — Make all save writes atomic (issue #370, write half — closes it)
- **Context:** The write half of #370. Every JSON writer opened the existing good file with `open(path, "w")` — which truncates immediately — and then `json.dump`ed into that handle. A process kill, full disk, or `json.dump` error mid-write left the good file already truncated and a partial result on disk. Combined with the load half (previous session), this is the full #370 fix: writes can no longer corrupt a save, and any pre-existing corruption is now tolerated on load.
- **`src/jsonPersistence.py`:** Added `writeJsonAtomically(path, data, indent=4)` — `os.makedirs` the parent dir, write to a `tempfile.mkstemp` temp file in the **same directory**, `flush()` + `os.fsync()`, then `os.replace()` over the target (atomic on a single filesystem). On any exception the temp file is removed and the error re-raised, so a failed save leaves the previous file intact and no stray temp behind.
- **Writers routed through it:** `stats.save`, `tickCounter.save`, `codexJsonReaderWriter.save`, `goalsJsonReaderWriter.save`, `inventoryJsonReaderWriter.saveInventory`, `roomJsonReaderWriter.saveRoom`, `worldScreenPersistence` (player location / attributes / room), and `WorldScreen._writeJsonToFile` / `_doSave` (the in-game background room-save path). The last two were not in the issue's enumerated list but are the hot save path and have the same truncate-then-dump bug, so they were included to actually close #370. Serialized output is byte-identical (same `json.dump(..., indent=4)`).
- **`tests/test_jsonPersistence.py`:** +4 tests — round-trip, missing-directory creation, no temp file left on success, and the core guarantee that a serialization failure (a non-JSON-serializable `set`) preserves the previous good file and leaves no temp file.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 553 passed (was 549; +4). Black/autoflake scoped to the ten changed files; `import json` became unused in `stats.py`, `tickCounter.py`, and `worldScreen.py` (autoflake removed it). File-scoped Black again reformatted pre-existing-drift blocks in `worldScreen.py` (the `status.set` / `_loadOrGenerateRoom` lines, same as cycle #424); those were reverted so the diff carries only the atomic-write change (roam-dev-loop#3).
- **Learning Log:** `[integrated]` — the `worldScreen.py` pre-existing Black drift re-surfaced for the third time this run (cycles #424, #426-area, now). It is reverted each time but keeps recurring because CI does not enforce formatting; a one-time formatting sweep or a CI `black --check` gate would end the recurring friction — worth filing as a Roam improvement during a future triage.

### 2026-06-07 — Tolerate corrupt/truncated save files on load (issue #370, load half)
- **Context:** #370 has two compounding weaknesses — non-atomic writes (a killed save truncates the good file) and unguarded loads (a truncated/corrupt file raises `json.JSONDecodeError` straight out of `WorldScreen.initialize`, so the game crashes on **every** launch until the user manually deletes the file). The full fix would touch >10 files (atomic writes across 8 writers + tolerant loads across ~6 loaders), exceeding the dev-loop scope ceiling, so it was split. This session does the **load-resilience** half — the part that fixes the user-visible crash-on-load symptom; the **atomic-write** half (corruption prevention) is a tracked follow-up.
- **`src/jsonPersistence.py` (new):** `readJsonFile(path, default=None)` — opens and `json.load`s the file, returning `default` on a missing file and logging + returning `default` on `(json.JSONDecodeError, OSError, UnicodeDecodeError)`. Module-level helper (mirrors `gameLogging.getLogger` / `schemaCache.loadSchema`).
- **Loaders routed through it:** `stats.load`, `tickCounter.load`, `worldScreenPersistence.loadPlayerLocationFromFile` / `loadPlayerAttributesFromFile`, `roomJsonReaderWriter.loadRoom` (now returns `None` on unreadable), `inventoryJsonReaderWriter.loadInventory`. Each treats an unreadable file as "no save" and falls back to its existing default. Schema *validation* (a separate concern, #363) and the serialized format are unchanged; the existing per-class save/load round-trip tests stay green.
- **`src/world/map.py`:** `getRoom` now checks `loadRoom(...) is None` and returns `-1` (treat the room as absent), so `WorldScreen.initialize` generates a fresh room (0,0) instead of crashing when that room file is corrupt.
- **`tests/test_jsonPersistence.py` (new):** 7 tests — `readJsonFile` happy/missing/corrupt/truncated, `Stats.load` and `TickCounter.load` no longer raise on a corrupt file (would crash before the fix), and a valid-file round-trip still loads (happy path preserved).
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 549 passed (was 542; +7). Black/autoflake scoped to the eight changed files left them unchanged (autoflake removed the now-unused `import os` in `stats.py`).
- **Learning Log:** `[integrated]` — applied the scope-ceiling split rule (RESEARCH.md §2): a single issue spanning >10 files was split into a load-half (this PR, fixes the crash symptom) and an atomic-write follow-up, rather than one oversized data-critical PR. Reused the module-level-helper pattern and `#370` keeps open until the write half lands.

### 2026-06-07 — Cache JSON validation schemas across save/load (issue #411)
- **Context:** Four persistence classes opened and `json.load`-ed their validation schema from disk in **both** `save()` and `load()`, even though schema files never change at runtime — repeated, avoidable disk I/O + parsing on the frequently-hit save path, plus four copies of the same load-schema boilerplate.
- **`src/schemaCache.py` (new):** A module-level `loadSchema(filename)` helper, `functools.lru_cache`d, that reads `schemas/<filename>` once and returns the cached parsed dict. It uses the same working-directory-relative path the call sites already used (established at startup by `appPaths.prepareWorkingDirectory`), so behaviour is unchanged when frozen. Module-level cached helper (mirrors the `gameLogging.getLogger` pattern) rather than a DI component, since it has no injectable dependencies and is pure read-only.
- **Call sites routed through it:** `src/stats/stats.py`, `src/world/tickCounter.py`, `src/goals/goalsJsonReaderWriter.py`, `src/codex/codexJsonReaderWriter.py` — each `with open("schemas/X.json") as f: schema = json.load(f); jsonschema.validate(...)` pair collapsed to `jsonschema.validate(data, loadSchema("X.json"))` in both methods. No serialized format changed; validation semantics are identical (same schema object).
- **`tests/test_schemaCache.py` (new):** 3 tests — returns the parsed schema dict; returns the same cached object on repeat; reads each file from disk only once (patched `builtins.open` call-count, `cache_clear()` for isolation).
- **Scope note:** The same re-read pattern also exists in `worldScreenPersistence.py`, `roam.py`, `inventoryJsonReaderWriter.py`, and `roomJsonReaderWriter.py`. #411 scopes to the four classes above, so those four were left for a follow-up to keep the diff matched to the issue (the latter two are also on the do-not-auto-merge persistence list).
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 542 passed (was 539; +3). Black/autoflake scoped to the six changed files left them unchanged (no drift to revert this time).
- **Learning Log:** `[integrated]` — no new convention; followed the module-level-cached-helper pattern (`getLogger`), structured logging, and issue-scoped editing (deferred the out-of-scope sites explicitly rather than silently expanding).

### 2026-06-07 — Log minimap image-load failures instead of swallowing them (issue #412)
- **Context:** In `WorldScreen.drawMiniMap`, the reload path caught `(FileNotFoundError, pygame.error)` and silently fell back to the cached frame (or returned). The fallback is correct — it must not crash the render loop — but it logged nothing, so a persistently missing/corrupt `mapImage.png` made the minimap silently never appear with zero diagnostic. Same class of silent-render-failure that #368 fixed for `DrawableEntity.getImage`.
- **`src/screen/worldScreen.py`:** Added a `_miniMapLoadFailed` flag (initialized in `__init__`). The `except` now logs `_logger.warning("could not load minimap image; keeping last good frame if available", path=..., error=...)` only on the good->failed transition (guarded by the flag), and a successful load resets the flag. This avoids per-reload log spam (the path runs every ~60 ticks) while making the failure diagnosable, and re-arms the warning if the minimap recovers and later breaks again. Existing fallback-to-cached-or-return behavior is unchanged.
- **`tests/screen/test_worldScreen_minimap.py` (new):** 3 tests — a corrupt `mapImage.png` is logged once and `drawMiniMap` returns cleanly (would fail before the fix, which logged nothing); repeated failures log only once (throttle); a successful load resets the failure flag (recovery). Built via `WorldScreen.__new__` with minimal attributes, mirroring `test_worldScreen_saveSurfacing.py`.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 539 passed (was 536; +3). Black/autoflake scoped to the two changed files; pre-existing Black drift the file-scoped format pulled in (unrelated `status.set`/`_loadOrGenerateRoom` lines) was reverted so the diff carries only the change.
- **Learning Log:** `[integrated]` — reused the #368 silent-render-failure precedent (structured `getLogger`, log-once degradation) and the cycle-2/4 hunk-scoping rule (roam-dev-loop#3): file-scoped `black` reformatted pre-existing-drift blocks in `worldScreen.py`; those were reverted and only the intended hunks kept.

### 2026-06-07 — Sync the config and copilot-instructions sources of truth (issues #362, #365)
- **Context:** A triage pass found drift between three sources of truth and the code: `config.yml`, `.github/copilot-instructions.md`, and `version.txt`. Each claim was re-verified against source before editing (line numbers in the issues were stale but the underlying mismatches held).
- **`config.yml` (#365):** Removed the `black`/`white` keys — they parse into `Config.black`/`Config.white` but a grep across `src/` (excluding `src/lib/`) finds zero consumers, so they were dead and misleading. Added the two keys the code reads but the file omitted: `cropGrowthTicks: 1800` (read at `config.py`, consumed at `world/room.py` for crop maturity) under the static section, and `pushableStone: true` (read at `config.py`, consumed at `worldScreen.py`, and already an in-game toggle in `configScreen.py`) under the dynamic section. The `getColorValue` helper and `Config.black`/`Config.white` reads were left in place — they default harmlessly and are covered by `tests/config/test_config.py`; removing them would delete tested code, which the issue marks as optional and is out of scope for a config-sync change.
- **`.github/copilot-instructions.md` (#362):** Added the `crafting/`, `codex/`, and `gameLogging/` packages (all present under `src/`) to the Repository Layout; corrected the Pillow version from the stale `9.4.0` to `>=10.0.0` to match `requirements.txt` (the issue said `==12.2.0`, but the actual pin is `>=10.0.0`); refreshed the stale `0.8.0-SNAPSHOT` version marker in the Technology Stack section to `0.11.0-SNAPSHOT` to match `version.txt`.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` green (config/docs-only change; no behavioral code touched).
- **Merge note:** `config.yml` is on the do-not-auto-merge list, so this PR is left for manual review rather than auto-merged.
- **Learning Log:** `[integrated]` — no new convention; reinforces the existing doc-drift / config-sync triage rules already in `copilot-instructions.md`. Confirmed the standing lesson that issue-reported specifics (line numbers, the `==12.2.0` Pillow pin) must be re-verified against source — Phase-3 localization caught the wrong version string before it shipped.

### 2026-06-07 — Correct release versioning and the update-check endpoint
- **Context:** `version.txt` had drifted to `0.8.0-SNAPSHOT` while the repo had in fact already published `0.9.0` and `0.10.0` (all releases are GitHub pre-releases, bare-number tags). Trusting the stale file, an erroneous `v0.9.0` tag + release was cut today (a duplicate version, `v`-prefixed against the bare-number convention, and briefly flagged "latest"). It was deleted (the real `0.9.0`/`0.10.0` are separate tags and untouched).
- **`version.txt`:** Set to `0.11.0-SNAPSHOT` (the correct in-development version after the real latest, `0.10.0`).
- **`.github/workflows/release.yml`:** Changed the trigger from `v*` to the bare-number pattern `[0-9]+.[0-9]+.[0-9]+`, matching all 11 prior releases. The existing `TrimStart("v")` / `${GITHUB_REF_NAME#v}` version extraction is a harmless no-op for bare tags. The next release is cut with `git tag 0.11.0 && git push origin 0.11.0`.
- **`src/update/updateChecker.py`:** Switched from `/releases/latest` to the `/releases` list. Every Roam release is published as a GitHub *pre-release*, and `/releases/latest` excludes pre-releases (returns 404), so the notifier built in #414 would never have found an update for this repo. It now reads the newest non-draft tag from the list. Updated tests accordingly (parse newest from list, skip drafts, empty-list → None).
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest tests/update` → 17 passed.
- **Learning Log:** `[not yet integrated]` — a release-process lesson worth a `create-dev-loop.md` rule: before cutting a release, verify the actual published releases/tags (`gh release list`, `git ls-remote --tags`) rather than trusting `version.txt`; and confirm the repo's tag convention (prefix, prerelease flag) so the new tag/release is consistent. A stale version marker had silently diverged from the real release history.

### 2026-06-07 — In-game update notifier and version plumbing (issues #413, #414)
- **Version prerequisite (#413):** Packaged builds previously had no `version.txt` (it wasn't in `roam.spec`'s `datas`), so `MainMenuScreen.drawVersion` found no file and showed nothing; `version.txt` was also a static `0.8.0-SNAPSHOT` never stamped per release. Fixed by bundling `("version.txt", ".")` in `roam.spec`, having the release workflow write the tag into `version.txt` before building (the `windows` job via `Set-Content`, the `macos` job via `printf`), and adding `Config.getVersion()` (reads the bundled `version.txt` via `getBundleDirectory()`, returns `"unknown"` if absent). `drawVersion` now sources the version through `Config.getVersion()`.
- **Update notifier (#414):** New `src/update/updateChecker.py` — a DI `@component` (`UpdateChecker(config)`). `checkForUpdatesAsync()` runs a one-shot daemon-thread check (no-op when the new `checkForUpdates` config toggle is off, or already started) that fetches the latest tag from the GitHub Releases API (stdlib `urllib`, 5s timeout, **never raises** — fails silently offline / when no releases exist), and `isNewerVersion` compares numeric dotted parts (a clean release outranks a same-numbered `-SNAPSHOT`; unparseable tags never show a spurious update). `MainMenuScreen` injects it, kicks the check off in `run()`, draws an "Update available: vX — press U to download" banner, and opens the Releases page in the browser on `U`. Added `checkForUpdates: true` to `config.yml` (the only network request Roam makes; documented as disable-able).
- **`tests/update/test_updateChecker.py` (new):** 16 tests — `isNewerVersion` across higher/lower/equal/`v`-prefix/snapshot-vs-release/short-version/unparseable cases; `_fetchLatestVersion` with `urllib`/`json.load` mocked (parse tag, return None on network error, None when tag missing); and `_checkForUpdates` orchestration (sets/doesn't set update-available; no-op when disabled). No real network is touched.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 529 passed (was 513; +16). DI resolution of `UpdateChecker` (and its `Config` wiring) confirmed via `container.resolve`. Black-clean (scoped to changed files).
- **Scope/merge note:** This PR touches `.github/workflows/release.yml`, `config.yml`, and `roam.spec` — `release.yml` and `config.yml` are on the do-not-auto-merge list, so the PR is for manual review. Tiers 2–3 (in-game download/apply, silent auto-update) are out of scope and tracked in #415/#416, gated on code-signing (#393/#396).
- **Learning Log:** `[integrated]` — no new convention; followed DI `@component` wiring, structured logging, stdlib-only networking on a daemon thread (fail-silent to preserve the game's offline-first behavior), and scoped formatting.

### 2026-06-07 — Prevent floors from being placed on floors (issue #345)
- **`src/screen/worldScreen.py`:** Floor tiles (`WoodFloor`, `StoneFloor`) are non-solid, so the existing `locationContainsSolidEntity` guard didn't stop them — players could stack multiple floors on one location, wasting items. Added a `locationContainsFloor(location)` helper (mirroring `locationContainsSolidEntity`) and a guard in `executePlaceAction`: when the selected item is a floor and the target already contains a floor, it sets the status `"A floor is already here"` and returns **before** energy or the item is consumed. Imported `WoodFloor`/`StoneFloor`.
- **`tests/screen/test_worldScreen_placeFloor.py` (new):** Two tests driving `executePlaceAction` via the `WorldScreen.__new__` + mocked-deps harness used by the other worldScreen tests — placing a `StoneFloor` on a location that already has a `WoodFloor` is blocked (no `StoneFloor` added, item not consumed, status set), and placing a floor on an empty location still succeeds (placed + item consumed). The blocked test was confirmed to fail without the guard.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → 513 passed (was 511; +2). The new lines are Black-clean (`black --diff` flags only pre-existing drift elsewhere in `worldScreen.py`, which was intentionally left untouched to keep this PR scoped, per the format-scope lesson).
- **Learning Log:** `[integrated]` — no new convention; reused the existing scoped-formatting rule (don't run Black tree-wide on a file with pre-existing drift) and the worldScreen test harness pattern.

### 2026-06-07 — Add unit-test coverage for excrement decay, inventory slotting, and minimap geometry (issues #372, #367)
- **`tests/world/test_room.py`:** Added eight tests for `Room.tickExcrement`, previously uncovered. Using the room's real 3×3 grid and a `SimpleNamespace(excrementDecayTicks=…)` config stub, they drive each branch: a living entity spawns excrement when `random.randrange` is monkeypatched to hit the 0.1% chance (and does **not** when it misses); an entity at location `-1` is skipped; a bogus location id exercises the `KeyError` guard without crashing; excrement below the decay threshold is left in place; expired excrement on an empty location decays into grass; and grass placement is correctly blocked by an existing `Grass` and by a solid `Stone`.
- **`tests/inventory/test_inventory.py`:** Added three tests for `Inventory.hasAvailableSlotFor` — an empty inventory (empty-slot branch), an inventory with no empty slot but a matching `Grass` stack with room (matching-stack branch, isolated by filling all other slots with `Stone`), and a full inventory of non-matching `Stone` (returns `False`).
- **`tests/mapimage/test_mapImageGenerator.py` (new):** Seven tests for `MapImageGenerator.pasteRoomImagesAtCorrectCoordinates`, mocking `Image.open`/the canvas so no real room PNGs are needed. They assert coordinate parsing and `picX`/`picY` math for the origin, an offset room, and negative coordinates; that a room at the high boundary (`picX == 1000 < 1100`) is pasted; and that rooms past the high (`picX == 1100`) and low (`picX == -100`) boundaries are skipped (`paste` not called).
- **Import-identity note:** `room.py` constructs entities via the `entity.*` import root (since `src` is on `pytest.ini`'s pythonpath), while the existing `test_room.py` imported `Grass`/`Stone` via `src.entity.*`. Under the multi-root pythonpath these are **distinct class objects**, so `isinstance(roomCreatedGrass, src.entity.grass.Grass)` is `False`. The grass/stone imports were switched to the `entity.*` root so the new `isinstance`-based assertions match production-created entities; the pre-existing `Grass`/`Stone` usages remain correct (they are self-consistent). Without this, the "blocked by existing grass" test passed for the wrong reason (a second, differently-typed grass was created and silently not counted).
- **Validation:** `python3 -m compileall src -q` clean; full suite `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` → **489 passed** (was 471; +18 new tests). `black`/`autoflake` were run scoped to the three changed test files (not tree-wide) per the cycle-2/4 lesson; both left them unchanged.
- **Scope note:** This PR contains only the three test files (plus this changelog). The branch was rebased onto `main` so it carries a single commit; an earlier accidental base on the unmerged `ci/windows-installer-smoke-test` branch was dropped. Unrelated working-tree edits seen during the session (an uncommitted `tickCounter.py` `ZeroDivisionError` guard, not present in any commit) were excluded.
- **Deferred this cycle (skip reasons):** #364 (WorldScreenPersistence tests) — heavier persistence round-trip with the DI container + `tmp_path` + schema validation; deserves its own cycle. #385 (PyInstaller/Inno Setup installer) — large and Windows-only, not verifiable in the Linux sandbox. #362, #365, #370 — each touches a do-not-auto-merge path (`copilot-instructions.md`, `config.yml`, save-persistence) and is better landed as its own reviewed PR. All are pure test additions here to keep the PR auto-mergeable.
- **Learning Log:** `[not yet integrated]` — two friction points worth a `create-dev-loop.md` rule. (1) The generated skill's verification commands use bare `python`, but this environment's `python` is **Python 2** (`compileall`/pytest fail on type-hint syntax and `mock`); the repo requires `python3` (as PR #383/#384 used). Candidate rule: for Python repos, probe `python3` first and pin it in the skill's commands. (2) Repos with a multi-root pythonpath (`pytest.ini` adding `.` and `src`) create a dual-import hazard where `entity.x` and `src.entity.x` are different classes; tests doing `isinstance` checks against production-created objects must import via the same root the source uses.
### 2026-06-07 — Bump GitHub Actions to Node 24 majors
- **`.github/workflows/{tests,windows-installer,macos-package,release}.yml`:** Bumped `actions/checkout@v4 → @v6`, `actions/setup-python@v5 → @v6`, and `actions/upload-artifact@v4 → @v7` (the current latest majors, all on Node 24), clearing the Node.js 20 deprecation warnings GitHub emitted on every run (Node 20 is force-removed from runners on 2026-09-16). Versions were confirmed against `repos/actions/<name>/releases/latest`.
- **Validation:** Pure CI-config change; no source touched. The `checkout`/`setup-python`/`upload-artifact` bumps are exercised directly by this PR's `test`, `windows-installer`, `package`, and `package-macos` jobs; `release.yml` (tag-only) uses the same `checkout`/`setup-python` versions proven by those jobs. `.github/workflows/` is on the do-not-auto-merge list → manual review.

### 2026-06-07 — Add a tag-triggered release workflow
- **`.github/workflows/release.yml` (new):** Triggers on `v*` tag pushes (`permissions: contents: write`). A `create-release` job creates the GitHub Release for the tag (idempotent — skipped if it already exists) with `gh release create --generate-notes`. A `windows` job (windows-latest) builds the PyInstaller exe, compiles the Inno Setup installer with the tag's version (`ISCC /DMyAppVersion=<tag without leading v>`), produces `Roam-<version>-Setup.exe` and a `Roam-<version>-windows-portable.zip`, and attaches them via `gh release upload --clobber`. A `macos` job (macos-latest) builds the `.app`, packages `Roam-<version>.dmg`, and attaches it. All uploads use the built-in `GITHUB_TOKEN`; no third-party actions.
- **Rationale:** CI build artifacts expire (~90 days), so the only durable place for end-user downloads is a Release. The build steps mirror the already-green `package` / `package-macos` jobs; the new pieces are tag→version extraction and the `gh release` create/upload calls.
- **`README.md`:** Added a Downloads section pointing to the Releases page and noting the artifacts are unsigned (SmartScreen/Gatekeeper — #393/#396).
- **Validation:** YAML validated locally (`yaml.safe_load`); the workflow only runs on tag pushes, so it is not exercised by PR CI. The per-OS build steps are identical to the existing, passing package jobs. A real end-to-end check requires pushing a version tag (a maintainer action that publishes a public Release), so it is intentionally left for the user rather than triggered here. `.github/workflows/` is on the do-not-auto-merge list → manual review.

### 2026-06-07 — Package Roam for macOS (.app + .dmg) (#394)
- **`src/config/config.py`:** Added a macOS branch (`sys.platform == "darwin"`) to `getUserDataDirectory()` → `~/Library/Application Support/Roam`, and to `getSavesBaseDirectory()` → that dir's `saves`. Mirrors the Windows `%APPDATA%` handling so a `.app` in a read-only `/Applications` can still persist config, saves, and screenshots. The existing Windows and from-source branches are untouched (the Windows no-APPDATA fallback still returns `"saves"`/the bundle dir). Added `import sys`.
- **`roam.spec`:** Platform icon selection (`.icns` on macOS, `.ico` elsewhere) and a macOS-only `BUNDLE(coll, name="Roam.app", bundle_identifier="com.preponderous.roam", ...)` step, so the same spec yields `dist/Roam.app` on macOS in addition to the one-folder output. The frozen-path shim (`appPaths.prepareWorkingDirectory`) and `--selftest` already work cross-platform.
- **`.github/workflows/macos-package.yml` (new):** A `macos-latest` job that generates `icon.icns` from `src/media/icon.PNG` via `sips`+`iconutil`, builds `dist/Roam.app` with PyInstaller, runs `Roam.app/Contents/MacOS/Roam --selftest` (verifies the bundled app locates its data and writes to `~/Library/Application Support`), builds `dist/Roam.dmg` with `hdiutil`, and uploads both the `.app` and `.dmg` as artifacts.
- **`tests/config/test_config.py`, `tests/screen/test_screenshotHelper.py`:** Added macOS cases (`sys.platform="darwin"`) for the user-data dir, saves base, and screenshots folder; pinned the existing POSIX cases to `sys.platform="linux"` so they stay correct regardless of host. `.gitignore` ignores the generated `src/media/icon.icns`.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 493 passed (was 490; +3). The `.app`/`.dmg` build and the frozen `--selftest` run only on `macos-latest` (no macOS/PyInstaller-darwin in the Linux sandbox) — the `package-macos` CI job is the verification anchor.
- **Scope:** Delivers #394 (build + .dmg + macOS user-data location). `.github/workflows/` is on the do-not-auto-merge list, so this PR is for manual review. macOS notarization / Gatekeeper signing is a further follow-up (analogous to the Windows code-signing issue #393).

### 2026-06-07 — Add a Windows setup wizard installer (#385, phase 2)
- **`roam.iss` (new):** Inno Setup 6 script that packages the PyInstaller one-folder build (`dist\Roam\`) into `installer-output\RoamSetup.exe`. Installs into `{autopf}\Roam` (Program Files, 64-bit), creates a Start Menu entry and an uninstaller shortcut, offers an optional Desktop shortcut (`[Tasks] desktopicon`), registers an Add/Remove Programs uninstaller, and offers to launch on finish. A stable `AppId` GUID supports clean upgrades/uninstalls; `MyAppVersion` defaults to `0.8.0` and can be overridden via `ISCC /DMyAppVersion=...`. The setup icon is included only when `src\media\icon.ico` exists (it is generated at build time and gitignored). Installing to a read-only Program Files is safe because user data lives under `%APPDATA%\Roam` (#388, #391).
- **`.github/workflows/windows-installer.yml`:** Extended the `package` job to compile the installer with `ISCC.exe`, assert `RoamSetup.exe`, then run a full end-to-end round-trip on the runner — silent install (`/VERYSILENT`) into Program Files, run the **installed** `Roam.exe --selftest` (verifies the packaged app finds its bundled data and writes to `%APPDATA%` from a read-only install dir), then silent uninstall — and upload `RoamSetup.exe` as the `roam-setup` artifact.
- **`README.md` / `.gitignore`:** Documented building `RoamSetup.exe` with Inno Setup and the silent-install option; ignore `installer-output/`.
- **Validation:** Pure packaging/CI work — no Python source changed, so the test suites are unaffected (the Linux `test` and the existing Windows pytest run stay green). The installer build and the install→selftest→uninstall round-trip are verified by the `package` job on `windows-latest` (no Inno Setup/Windows in the Linux sandbox). `.github/workflows/` is on the do-not-auto-merge list, so this PR is for manual review.
- **Scope:** Completes #385 (standalone executable + setup wizard). Phase 1 (#390) produced the frozen exe; the writable-user-data work (#388, #391) made a read-only Program Files install viable; this adds the user-facing installer. Code signing (to avoid SmartScreen warnings) and a macOS `.app`/`.dmg` remain possible future follow-ups, as noted in #385/#385's macOS note.

### 2026-06-07 — Store writable user data under %APPDATA% on Windows
- **Motivation:** Phase 1 of #385 (PR #390) noted that a packaged install into a read-only location (e.g. Program Files) would break config/keybinding writes (`Config.saveWindowSize`, `KeyBindings.saveToConfigFile` → `_writeKeyValues`) and screenshot saves, which were still install-relative. Saves were already relocated to `%APPDATA%` (#388); this does the same for the remaining writable data.
- **`src/config/config.py`:** Added `getUserDataDirectory()` — `%APPDATA%\Roam` on Windows (with an `APPDATA`-missing fallback to the bundle dir), the bundle/repo root elsewhere (preserving from-source behavior). `getConfigFilePath()` now resolves under it (writable), with a new `getBundledConfigFilePath()` for the shipped defaults and `ensureUserConfigExists()` (called at the start of `__init__`) that copies the bundled `config.yml` into the user-data dir on first run so shipped settings are preserved and the file is writable. No-op from source (user and bundled paths are the same file).
- **`src/screen/screenshotHelper.py`:** Replaced the relative `SCREENSHOTS_FOLDER = "screenshots"` constant with `getScreenshotsFolder()` → `<userDataDir>/screenshots`, and switched path building to `os.path.join`.
- **`src/appPaths.py`:** Reimplemented `getBundleDirectory()` with `os.path` instead of `pathlib` — `pathlib.Path` keys off `os.name` and raises `NotImplementedError` instantiating a `WindowsPath` on a POSIX host, which broke cross-platform tests that monkeypatch `os.name="nt"`.
- **Tests:** `tests/config/test_config.py` — `getUserDataDirectory` from source / on Windows / `APPDATA`-missing fallback, and `ensureUserConfigExists` seeds-when-missing / no-op-when-same-file / no-op-when-user-exists. `tests/screen/test_screenshotHelper.py` (new) — screenshots folder resolves under the user-data dir on POSIX and Windows.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 490 passed (was 482; +8). From source the config/screenshot locations are unchanged (repo root); the Windows `%APPDATA%` branch is exercised via monkeypatched `os.name`/`APPDATA` on the Linux runner and natively by the `windows-installer` job.
- **Scope:** `getSavesBaseDirectory()` was intentionally left as-is (it already returns `%APPDATA%\Roam\saves` on Windows and its tests pin the relative `"saves"` string on other platforms). With this, #385's remaining follow-up is just phase 2 — the Inno Setup/NSIS setup wizard.

### 2026-06-07 — Package Roam as a standalone Windows executable (#385, phase 1)
- **`src/appPaths.py` (new):** `isFrozen()`, `getBundleDirectory()`, and `prepareWorkingDirectory()`. A frozen PyInstaller build starts with an arbitrary working directory, but the game loads assets/schemas via repo-root-relative paths (`"assets/images/stone.png"`, `open("schemas/tick.json")`). `prepareWorkingDirectory()` chdir's into the bundle (`sys._MEIPASS`) when frozen so those ~20 entity image paths and ~6 schema-load sites resolve unchanged — avoiding an invasive per-file rewrite. No-op when run from source.
- **`src/roam.py`:** Calls `prepareWorkingDirectory()` before constructing the game, and adds a `--selftest` flag that initializes pygame headlessly, loads a bundled image + schema, and reads `config.yml`, exiting 0/1. CI runs the packaged exe with `--selftest` to confirm the bundle is complete without launching the interactive loop.
- **`src/config/config.py`:** `getConfigFilePath()` now resolves `config.yml` via `getBundleDirectory()` instead of a `__file__`-relative path, which is unreliable when frozen. From source this still resolves to the repository root.
- **`roam.spec` (new):** One-folder PyInstaller build (`dist/Roam/Roam.exe`) bundling `assets`, `schemas`, `config.yml`, and `src/media` at their existing relative paths; sets the icon only if `src/media/icon.ico` exists (it is generated by `install.ps1` and gitignored).
- **`.github/workflows/windows-installer.yml`:** Added a `package` job that installs PyInstaller, generates the icon, builds the spec, asserts `dist/Roam/Roam.exe` exists, runs `Roam.exe --selftest` (the frozen-bundle verification anchor), and uploads the build as an artifact.
- **`tests/test_appPaths.py` (new):** 5 tests covering not-frozen vs. frozen (`sys.frozen`/`sys._MEIPASS` monkeypatched) for `isFrozen`/`getBundleDirectory` and that `prepareWorkingDirectory` only chdir's when frozen.
- **`README.md` / `.gitignore`:** Documented the `pyinstaller roam.spec` build and `--selftest`; ignore `build/` and `dist/`.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 482 passed (was 477; +5); `python3 src/roam.py --selftest` exits 0 from source. The actual PyInstaller build and frozen selftest run only on `windows-latest` (no PyInstaller/Windows in the Linux sandbox) — the `package` CI job is the verification anchor.
- **Scope (phase 1 of #385):** Establishes a verifiable frozen build. Deferred to follow-ups: wrapping the build in an Inno Setup/NSIS setup wizard with shortcuts + uninstaller (phase 2); and relocating writable config/keybindings persistence and screenshots out of a potentially read-only install directory (config.yml/keybinding writes and `screenshots/` are still install-relative). `.github/workflows/` is on the do-not-auto-merge list, so this PR is for manual review.

### 2026-06-07 — Make Roam installable on modern Python (unpin requirements.txt)
- **`requirements.txt`:** Was a frozen `pip freeze` pinning exact versions, including `pygame==2.1.2` (no wheels for Python 3.11+, so `install.ps1` / `run.sh` failed to install on a modern default Python) and exact transitive pins like `pyrsistent==0.19.3`, `attrs==22.1.0`, and the unused `image==1.5.33`. Replaced with the actual direct dependencies, verified against the source's third-party imports (`pygame`, `PIL`/Pillow, `jsonschema`, `structlog` at runtime; `pytest`, `pytest-cov` for tests), using lower bounds (`pygame>=2.6.1`, etc.) so pip resolves modern wheels for whatever Python is in use. Transitive deps are now resolved automatically. This mirrors the dependency set the Linux Tests job already installs and passes with on Python 3.12.
- **`.github/workflows/windows-installer.yml`:** Raised the job's Python from **3.10 back to 3.12** (the 3.10 pin existed only because of the old `pygame==2.1.2` wheel gap). Because the wizard runs `pip install -r requirements.txt`, the job now actually verifies the installer works end-to-end on a current Python.
- **Validation:** No source/test code changed, so the local suite is unaffected (it runs against the already-installed pygame). The fix is verified by the `windows-installer` job installing `requirements.txt` on Python 3.12 and the suite passing there. No PyPI access in the sandbox to install the new floors locally; CI is the anchor (the Linux Tests job already proves these deps work unpinned on 3.12).
- **Scope note:** Broader than just the pygame line because fixing pygame alone would still leave the install broken on 3.11+ at the next stale transitive pin (e.g. `pyrsistent==0.19.3`). `requirements.txt` and `.github/workflows/` are both on the dev-loop's do-not-auto-merge list, so this PR is for manual review.

### 2026-06-07 — Store saves under %APPDATA% on Windows
- **`src/config/config.py`:** Added two static methods as the single source of truth for the save root. `getSavesBaseDirectory()` returns `%APPDATA%\Roam\saves` on Windows (`os.name == "nt"` and `APPDATA` set) and the repo-relative `"saves"` everywhere else (and as a fallback when `APPDATA` is missing). `getDefaultSaveDirectory()` returns `<base>/defaultsavefile`. `Config.__init__` now uses `getDefaultSaveDirectory()` as the default for `pathToSaveDirectory` instead of the hard-coded `"saves/defaultsavefile"`. Added `import os`.
- **`src/screen/saveSelectionScreen.py`:** `savesBaseDirectory` now comes from `Config.getSavesBaseDirectory()` instead of the hard-coded `"saves"`, so the in-game save-selection UI lists/creates slots in the same per-user location. (Save writers already use `os.makedirs`, which creates the full `%APPDATA%\Roam\saves\...` chain on first save.)
- **`config.yml`:** Removed the explicit `pathToSaveDirectory: saves/defaultsavefile` (replaced with an explanatory comment) so the platform-aware default takes effect; an explicit value still overrides it.
- **`README.md`:** Documented the Windows save location (`%APPDATA%\Roam\saves`) under the Windows Installation Wizard section, noting Linux/macOS are unchanged and the `config.yml` override.
- **`tests/config/test_config.py`:** Added 5 tests — POSIX base is `"saves"`, Windows base uses `APPDATA`, Windows falls back to `"saves"` when `APPDATA` is unset, the default save dir is `<base>/defaultsavefile`, and `Config()` adopts the platform default when `config.yml` does not pin it (`os.name` and `APPDATA` are monkeypatched, so the Windows branch is exercised on the Linux runner too).
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 476 passed (was 471; +5). Linux/macOS behavior is unchanged (default stays `saves/defaultsavefile`).
- **Scope/verification notes:** Branched off `main`, which does not yet carry `windows-installer.yml` (it is in the still-open #386), so this PR initially gets only the Linux `test` check; once #386 merges, the `windows-latest` job will exercise the real `%APPDATA%` resolution here. `config.yml` is on the dev-loop's do-not-auto-merge list, so this PR is for manual review. Existing-save migration (moving an old `<install>\saves` to `%APPDATA%`) is intentionally out of scope — fresh installs have nothing to migrate; a one-time migration could follow if wanted.

### 2026-06-07 — Smoke-test the Windows installer on CI (follow-up to #383)
- **`install.ps1`:** Added a `param([switch]$NonInteractive, [switch]$NoLaunch)` block (the first executable statement, after the comment-based help). A new `Pause-IfInteractive` helper replaces the three bare `Read-Host "Press Enter to exit"` calls so they no-op under `-NonInteractive`; the final "play now?" prompt is now gated behind `if ($NonInteractive -or $NoLaunch) { ...skip... } else { ...prompt/launch... }`. `-NonInteractive` is for automation/CI (no prompts, no launch); `-NoLaunch` lets an interactive user finish the install without launching.
- **`.github/workflows/windows-installer.yml` (new):** A `windows-latest` job that checks out, sets up Python **3.10** (the newest interpreter with prebuilt `pygame==2.1.2` wheels — the version pinned in `requirements.txt` that the wizard installs; newer interpreters would build pygame from source and fail), runs `install.ps1 -NonInteractive`, asserts the wizard generated `src/media/icon.ico` and both the Desktop and Start Menu `Roam.lnk` shortcuts, then runs `python -m pytest` on Windows (deps already installed by the wizard, so this also exercises the wizard's dependency install and gives Roam a Windows-native test run).
- **`src/world/tickCounter.py` (Windows-only crash the new job caught on its first run):** `updateMeasuredTicksPerSecond` computed `self.measuredTicksPerSecond = 1 / timeElapsed`. On Windows, `time.time()` has ~15ms resolution, so two ticks in quick succession can read the same timestamp, making `timeElapsed` zero → `ZeroDivisionError` (3 tests crashed on `windows-latest`; the finer Linux clock hid it). The division (and the highest-TPS update) is now guarded by `if timeElapsed > 0`, preserving the last measured rate when the clock did not advance. **`tests/world/test_tickCounter.py`:** added `test_increment_tick_with_zero_time_elapsed`, which mocks `time.time` to return a repeated timestamp and asserts no exception plus a preserved rate — confirmed to fail (ZeroDivisionError) without the guard.
- **Validation:** Linux suite unaffected — `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` still 471 passed. The new Windows job and the PowerShell switch changes execute only on `windows-latest`; the first real verification is the PR's `Windows Installer` check itself (the Linux sandbox still cannot run PowerShell). This directly addresses the coverage gap filed as roam-dev-loop#6 — the deliverable now has a Windows CI anchor rather than relying on hand-review alone.
- **Merge note:** This PR adds a file under `.github/workflows/` — on the dev-loop's do-not-auto-merge list — so it is left open for manual review rather than auto-merged.
- **Learning Log:** `[not yet integrated]` — surfaced a pre-existing latent issue while designing the job: `requirements.txt` pins `pygame==2.1.2`, which has no wheels for Python 3.11+, so `install.ps1`/`run.sh` would fail to install on a modern default interpreter. The Windows job pins 3.10 to stay green; the underlying stale pin is left as a separate concern (not in scope here, and `requirements.txt` is itself on the do-not-auto-merge list).

### 2026-06-07 — Add Windows installation wizard (issue #383)
- **`install.ps1` (new):** PowerShell installation wizard, the Windows analogue of `run.sh`. Resolves a Python interpreter (`python`, falling back to the `py` launcher); if none is found it opens the python.org download page and exits with PATH guidance. Bootstraps pip via `ensurepip` when absent, installs `pygame --pre` and `requirements.txt`, converts `src/media/icon.PNG` to `src/media/icon.ico` with Pillow (an existing dependency) for use as the shortcut icon (graceful fallback to the launcher's default icon on failure), and creates **Desktop** and **Start Menu** shortcuts to the launcher via the `WScript.Shell` COM object. Finishes by offering to launch the game.
- **`run.bat` (new):** Double-clickable launcher (and the shortcut target). `cd /d "%~dp0"` so relative paths resolve regardless of where it is invoked, checks for Python on PATH with a friendly message, runs `python src\roam.py`, and pauses on error so the window does not vanish before the user can read it.
- **`README.md`:** Added a "Windows Installation Wizard" section next to the existing "Run Script (Linux Only)" section, covering the run-with-PowerShell flow, the `-ExecutionPolicy Bypass` fallback for blocked scripts, and the missing-Python path.
- **`.gitignore`:** Ignore the wizard-generated `src/media/icon.ico` so it is not accidentally committed by users who run the wizard.
- **Validation:** No Python source changed, so the pytest suite and JSON schemas are unaffected; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` was run as a regression check (no new tests — the deliverable is Windows shell tooling, not Python code). The PowerShell wizard and the `.bat` launcher are Windows-only and **could not be executed in this Linux sandbox** (no `pwsh`/`cmd.exe`); they were authored against PowerShell/batch conventions and reviewed by hand but are flagged unverified-on-Windows.
- **Scope note:** Implemented the lightweight script route from #383 (no separate Python bundling). A fully packaged PyInstaller + Inno Setup/NSIS installer remains a possible follow-up; the script-based wizard already satisfies the acceptance criteria (no manual pip/python, dependencies installed, a shortcut is created, documented in the README).
- **Learning Log:** `[not yet integrated]` — this cycle's deliverable was non-Python platform tooling (PowerShell/batch) that the Linux CI and sandbox cannot execute or lint; the only available anchor was the unaffected pytest suite plus manual review. Candidate rule for `create-dev-loop.md`: when a PR ships platform-specific shell/installer scripts outside the test harness's reach, state the no-automated-coverage gap explicitly in the PR body and CHANGELOG rather than implying the green CI run covered it.

### 2026-06-06 — Abort save on schema-validation failure instead of writing invalid data (issue #363)
- **`src/inventory/inventoryJsonReaderWriter.py` (`saveInventory`), `src/codex/codexJsonReaderWriter.py` (`save`):** Both writers validated the serialized data against their JSON schema, caught the `ValidationError`, **logged it, and then wrote the invalid data anyway** — so validation offered no protection. Both now abort (return `False`) on a validation failure (after an explanatory log), leaving the existing good file untouched, and return `True` on a successful write. Because validation runs before the `open(path, "w")` truncation, aborting preserves the prior save byte-for-byte.
- **Player-facing surfacing (`src/screen/worldScreen.py`, `src/screen/worldScreenPersistence.py`):** `savePlayerInventoryToFile` and `saveCodexToFile` now check the writer's return value and set a status message (`"Could not save inventory (invalid data)"` / `"Could not save codex (invalid data)"`) when a save is skipped, so a failed save is no longer silent to the player (addressing the "log *and surface it*" part of #363).
- **Tests (`tests/inventory/test_inventoryJsonReaderWriter.py`, `tests/codex/test_codexJsonReaderWriter.py`, `tests/screen/test_worldScreen_saveSurfacing.py` — new):** Force a `ValidationError` (monkeypatching `jsonschema.validate`) and assert the existing file is not clobbered, no new file is created, and the writer returns `False`; success returns `True`. A codex save/load round-trip test and two `saveCodexToFile` surfacing tests (status set on failure, not set on success) were added. The abort tests were confirmed to **fail without the fix** (the old code logged the error and then re-wrote the file).
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 471 passed (was 464; +7 new).
- **Scope note:** Deliberately limited to the two writers #363 names plus their save-orchestration call sites. The broader atomic-write + guarded-load rework (#370) — temp-file + `os.replace`, resilient `json.load`, and the cross-file save-transaction needed to avoid stale/desynced save sets — is left as its own follow-up.
- **Design tradeoff:** Aborting on validation failure converts a best-effort save into strict-or-nothing. If a schema were ever too strict, a legitimate save would now be skipped (the player is told via the status message) rather than written. This is the behavior #363 requests; the prior behavior was strictly worse for inventory, whose unguarded loader could crash or total-loss on the invalid data it used to write.
- **Learning Log:** `[integrated]` — applied cycle-4 hunk-scoping: file-scoped Black again reformatted pre-existing-drift blocks in `worldScreen.py` and the existing `test_saveInventory`; both were reverted and the intended edits re-applied so the diff carries only the change (per roam-dev-loop#3).

### 2026-06-06 — Harden render loop against missing/unreadable assets (issue #368)
- **`src/entity/drawableEntity.py`:** `getImage` previously called `pygame.image.load` with no error handling; a missing, renamed, or corrupt sprite raised `pygame.error` / `FileNotFoundError` straight out of the hot render path (`room.py`, `worldScreen.py`, `inventoryScreen.py`), hard-crashing an in-progress, auto-saving session. The load is now wrapped in `try`/`except (pygame.error, FileNotFoundError)`: on failure it logs the offending `imagePath` once (structured `getLogger` warning) and caches a magenta placeholder surface from the new `_createFallbackSurface()` helper, so the game degrades gracefully and the missing asset is visible rather than fatal. The fallback is cached per path, so the failing load is not retried every frame and the warning is logged only once.
- **`tests/entity/test_drawableEntity.py`:** Added a headless-pygame fixture plus two tests: a missing asset returns a `pygame.Surface` of the fallback size (would raise under the old unguarded load), and the fallback is cached (the second `getImage` returns the same surface, confirming no per-frame retry). Both pop their cache keys to keep the class-level `_imageCache` clean.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 464 passed (was 462; +2 new).
- **Learning Log:** `[integrated]` — applied the cycle-4 refinements: formatting was scoped to the two changed files and the diff verified at the hunk level (no pre-existing drift in this file to leak); no `print()`, structured `getLogger` used per logging conventions.

### 2026-06-06 — Consolidate room save-file path into a single source of truth (issue #373)
- **`src/config/config.py`:** Added `Config.getRoomFilePath(self, x, y)` — the single canonical builder for the `<saveDir>/rooms/room_<x>_<y>.json` layout.
- **`src/world/map.py`, `src/world/roomPreloader.py`:** Replaced inline hand-concatenated path builds in `getRoom` / the preloader with `self.config.getRoomFilePath(x, y)`.
- **`src/screen/worldScreenPersistence.py`:** `saveRoomToFile` now calls `getRoomFilePath`; removed the dead `buildRoomPath` method (it had zero callers).
- **`src/screen/worldScreen.py`:** Removed the `_buildRoomFilePath` helper and routed its two call sites (`saveRoomToFileAsync`, entity-move save) through `config.getRoomFilePath`.
- **`tests/conftest.py`:** The shared `test_config` mock (`MagicMock(spec=Config)`) now delegates `getRoomFilePath` to the real `Config.getRoomFilePath` so path construction reflects each test's `pathToSaveDirectory` — required because the logic moved behind a Config method the mock would otherwise stub out.
- **`tests/config/test_config.py`:** Added `test_get_room_file_path_format` pinning the exact on-disk path string (including negative coordinates) that all save/load call sites depend on.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 462 passed (was 461; +1 new). The format string `"/rooms/room_"` now appears in exactly one place. Net −22 LOC.
- **Learning Log:** `[not yet integrated]` — refines the cycle-2 lesson (roam-dev-loop#3): scoping formatters to *changed files* is still insufficient when a touched file carries pre-existing Black drift (`worldScreen.py` here), because `black <file>` reformats the whole file. The fix is to scope to changed *hunks* — after formatting, diff the touched file and revert any reformat that isn't part of the change (here, `worldScreen.py` was reverted and the two intended edits re-applied by hand).

### 2026-06-06 — Deduplicate the config-file rewrite loop (issue #366)
- **`src/config/config.py`:** Extracted the read → update-matching-keys → append-new-keys → write-back loop into a new `Config._writeKeyValues(self, savedValues, errorMessage)` helper. `saveWindowSize` now just builds its `savedValues` dict and delegates; the differing log message is passed through `errorMessage` so existing log behavior is preserved.
- **`src/config/keyBindings.py`:** `KeyBindings.saveToConfigFile` now builds its prefixed `savedValues` dict and delegates to `config._writeKeyValues(...)`, dropping the verbatim-duplicated loop (~37 lines). Removed the now-unused `getLogger` import and module-level `_logger` (the only use was the warning that moved into `Config`).
- **`tests/config/test_config.py`:** Added `test_write_key_values_updates_appends_and_preserves`, a direct test of the helper covering in-place key update (no duplicate), new-key append, and comment/blank-line preservation in a single call. The existing `saveWindowSize`/`saveToConfigFile` suites already exercise the helper through both public callers, providing regression coverage for the extraction.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 461 passed (was 460; +1 new). Net −13 LOC across 3 files.
- **Learning Log:** `[integrated]` — applied the cycle-2 lesson (roam-dev-loop#3): formatting was run scoped to the 3 changed files (`black`/`autoflake` on explicit paths) rather than tree-wide `./format.sh`, so no unrelated drift entered the diff.

### 2026-06-06 — Fix death-penalty rounding and un-skip silently-dead tests (issues #369, #371)
- **`src/screen/worldScreen.py`:** Changed the on-death score penalty from `math.ceil(score * 0.9)` to `math.floor(score * 0.9)`. With `ceil`, the intended 10% penalty was a no-op for every score 1–9 (`ceil(0.9)` = 1, `ceil(8.1)` = 9) and only began reducing the score at 10 — exactly the early game where new players die most. `floor` makes the penalty always apply.
- **`tests/screen/test_worldScreen_deathPenalty.py`** (new): Parametrized regression test pinning `removeEnergyAndCheckForPlayerDeath` at boundary scores (1→0, 9→8, 10→9, 25→22, 100→90); each case would fail under the old `ceil` logic. Also asserts the death counter increments.
- **`tests/inventory/test_inventory.py`:** Renamed `removeSelectedItem` → `test_removeSelectedItem` so pytest actually collects it — the only test for `Inventory.removeSelectedItem` had been silently skipped (missing `test_` prefix).
- **`tests/crafting/test_recipe.py`:** Added two multi-ingredient `Recipe.craft` tests (Bed = OakWood×3 + Stone×2) using the previously-unused `createInventoryWithOakWoodAndStone` helper — covering the multi-type/multi-slot ingredient-deduction path that single-ingredient tests never exercised.
- **Validation:** `python3 -m compileall src -q` clean; `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -m pytest` — 460 passed (was 451; +9 effective new cases).
- **Learning Log:** `[not yet integrated]` — observed that `./format.sh` (Black + autoflake) reformats ~8 files unrelated to the change because CI does not enforce formatting, so drift accumulates on `main`; running it tree-wide pollutes a focused PR. For this session only the four in-scope files were kept and unrelated reformats reverted. Candidate rule for `copilot-instructions.md`: run formatters scoped to changed files, or land a separate formatting-only sweep.

### 2026-06-06 — Documentation sync: README clone URL and PLANNING.md drift (issues #374, #361)
- **`README.md`:** Corrected the "Clone and Run" git URL from `https://github.com/Stephenson-Software/Roam.git` to the canonical `https://github.com/Preponderous-Software/roam.git` (matching the configured `origin` remote and the org used elsewhere in the README for the `graphik` / `py_env_lib` libraries).
- **`PLANNING.md`:**
  - Removed the stale "(unimplemented)" marker from the Crafting heading and documented the shipped recipe system (`Recipe` / `RecipeRegistry` in `src/crafting/`, listing all 8 recipes: Wood Floor, Bed, Stone Floor, Stone Bed, Fence, Campfire, Wheat Seed, Torch).
  - Reconciled the Room Types list with `RoomType` in `src/world/roomType.py` — added the missing `Empty` type and corrected `Grass` → `Grassland`.
- **Validation:** Documentation-only change; no `src/` or `tests/` files modified. `python -m compileall src -q` clean; full test suite re-run as a regression check (PASS).
- **Learning Log:** `[integrated]` — no new convention; reinforces the existing doc-drift triage rule already in `copilot-instructions.md`.

### 2026-04-23 — Clean Code refactoring (names, DRY, dead code)
- **`src/screen/worldScreen.py`:**
  - Removed duplicate `from math import ceil` import (already imported via `import math`); replaced the one `ceil()` call with `math.ceil()`.
  - Renamed `ifCorner` → `isCorner` (predicate methods should start with `is`, not `if`); updated all 4 call sites.
  - Extracted `_buildRoomFilePath(room)` helper — eliminates two identical string-concatenation blocks that constructed the room JSON file path in `saveRoomToFileAsync()` and `save()`.
- **`src/inventory/inventory.py`:**
  - Renamed `type` parameter → `itemType` in `getNumItemsByType()` to stop shadowing the Python built-in `type`.
  - Replaced `for i in range(self.size):` with `for _ in range(self.size):` since the loop variable was unused.
- **`src/world/roomFactory.py`:**
  - Replaced four `for i in range(...)` loops where `i` was never used with `for _ in range(...)`. Simplified `range(0, n)` to `range(n)` for all four.
  - Consolidated the repeated `self.lastRoomTypeCreated = roomType` assignments that appeared in every branch of `createRoom()` into a single `if room is not None: self.lastRoomTypeCreated = roomType` after the if/elif block, preserving the semantics that unknown room types do not update the field.
  - Removed `# spawn methods` section comment (added no information beyond the method names themselves).
- **`src/world/room.py`:**
  - Removed `elif isinstance(entity, MatureCrop): pass  # MatureCrop waits for player harvest` dead code block in `tickCrops()`.
- **`src/world/roomJsonReaderWriter.py`:**
  - Removed `# validate json with schema` and `# add living entities` comments that merely restated what the immediately following line of code already expressed.
- **Validation:** All 436 tests pass.

### 2026-04-23 — Fix minimap not showing consistently on new maps
- **Root cause:** `MapImageGenerator.getRoomImages()` and `clearRoomImages()` both call `os.listdir()` on the `roompngs` directory without checking if it exists. There is a race between the `_doSave()` background thread (which triggers `updateMapImage()` after each room-change save) and the main thread's `draw()` call (which creates the `roompngs` directory lazily via `saveCurrentRoomAsPNG()`). When `_doSave()` finishes before `draw()` has created the directory, `os.listdir()` raises `FileNotFoundError`, the exception is caught silently by `_doUpdateMapImage()`'s try/except, and `mapImage.png` is never written — leaving the minimap invisible until the next update cycle succeeds.
- **Fix — `src/mapimage/mapImageGenerator.py`:**
  - `getRoomImages()`: returns `[]` immediately if `roompngs` directory does not exist.
  - `clearRoomImages()`: returns immediately (no-op) if `roompngs` directory does not exist.
  These guards ensure `generate()` never throws on a fresh game, and `mapImage.png` is written (initially blank white) as soon as the first map update runs, so the minimap widget appears immediately and fills in as rooms are visited.
- **Validation:** All 436 tests pass.

### 2026-04-23 — Fix 'rooms explored' statistic not updating correctly
- **Root cause:** `RoomPreloader` generates rooms in background threads. When the player later enters a pre-loaded room, `_loadOrGenerateRoom` found the room already cached (`hasRoom` true) and skipped the `generateNewRoom` branch — so `incrementRoomsExplored()` was never called. The result: rooms explored stayed in single digits no matter how far the player explored.
- **Fix — `src/world/map.py`:**
  - Added `_freshlyGeneratedRooms: set` to `Map.__init__` (protected by the existing `_lock` for thread safety).
  - `generateNewRoom()` now adds `(x, y)` to `_freshlyGeneratedRooms` when a room is actually created (inside the lock, after the double-checked skip).
  - New public method `consumeIsNewRoom(x, y) -> bool`: atomically checks whether the room was freshly generated and removes it from the set in a single lock acquisition. Returns `True` only once per newly generated room.
- **Fix — `src/screen/worldScreen.py`:**
  - `_loadOrGenerateRoom(x, y, updateStats=True)`: replaced the old unconditional `incrementRoomsExplored` on the generate branch with a `consumeIsNewRoom` call that works for both the direct-generate path **and** the pre-loaded path (where the room is already in memory). This is the single authoritative place stats are updated for player room transitions.
  - `initialize()`: replaced the unconditional `stats.incrementRoomsExplored()` with `if self.map.consumeIsNewRoom(0, 0):` so that the starting room only counts if it was freshly generated, and the flag is consumed to prevent double-counting when the player later returns to room (0, 0).
  - Entity room transition at line 1851: passes `updateStats=False` so living-entity cross-room moves do not consume the new-room flag or increment statistics.
- **New tests:**
  - `tests/world/test_map.py`: 4 new tests for `consumeIsNewRoom` (true on generate, false after consume, false for disk-loaded rooms, false on duplicate generate).
  - `tests/world/test_roomsExplored.py`: 6 new tests covering entering a new room increments by 1, re-entry does not re-increment, pre-loaded rooms still increment when entered, pre-loaded rooms that are never entered do not increment, multiple new rooms each count once, and loading a room from disk does not increment.
- **Validation:** All 436 tests pass (426 existing + 10 new).

### 2026-04-23 — Fix toggle buttons covering Back button in settings screen (issue)
- **Modified `src/screen/configScreen.py`:**
  - Added `self.scrollOffset = 0` to `__init__` to track scroll state.
  - Refactored `drawMenuButtons()` to use the scrollable row pattern from `ControlsScreen.drawBindings()`: calculates `visibleRows` from available vertical space, clamps `scrollOffset`, renders only visible toggles, and shows a scroll indicator (`"1-N of 9"`) when content overflows.
  - Replaced `drawBackButton()` with `drawBottomButtons()` that always draws the **Back** button at a fixed position at the bottom of the screen (`y - 45`), matching `ControlsScreen.drawBottomButtons()`.
  - Added `handleScrollEvent(event)` method matching `ControlsScreen.handleScrollEvent()`.
  - Updated `run()` to: reset `scrollOffset` on entry; handle `pygame.MOUSEWHEEL` events via `handleScrollEvent()`; call `drawBottomButtons()` as a separate step after `drawMenuButtons()`.
  - Row height (35), button height (28), and bottom margin values match `ControlsScreen` for visual consistency.
- **Validation:** All 426 tests pass.

### 2026-04-21 — Add gravestone feature (issue #337)
- **New file:** `src/entity/storableInventory.py` — `StorableInventory` mixin class that holds an `Inventory` instance and exposes `getStoredInventory()`. Designed for reuse by the future `Chest` entity.
- **New file:** `src/entity/gravestone.py` — `Gravestone` entity extending `DrawableEntity` (solid=True) and `StorableInventory`. Not pickupable, not craftable.
- **New asset:** `assets/images/gravestone.png` — 32×32 RGBA placeholder sprite.
- **Modified `src/screen/worldScreen.py`**:
  - Added import for `Gravestone`.
  - `respawnPlayer()` now creates a `Gravestone`, transfers all player inventory items into its stored inventory, and places it at the player's last location instead of scattering individual items. No gravestone is spawned if the player's inventory was empty.
  - `executePlaceAction()` now checks for a `Gravestone` at the target location before other solid-entity guards. If found, it delegates to `_interactWithGravestone()`.
  - New `_interactWithGravestone(gravestone, targetRoom, targetLocation)`: transfers all stored items into the player's inventory; if any item doesn't fit, sets status "Inventory full" and leaves the gravestone in place; on full retrieval, removes the gravestone and sets status "Retrieved items from Gravestone".
- **Modified `src/world/roomJsonReaderWriter.py`**:
  - Added `Gravestone` import.
  - `generateJsonForEntity()` serializes `Gravestone` with a `storedInventory` field.
  - `generateEntityFromJson()` restores the stored inventory after deserialization.
  - `_createEntity()` handles `entityClass == "Gravestone"`.
  - New helpers: `_generateJsonForStoredInventory()`, `_restoreStoredInventory()`, `_createStoredItem()`.
- **New tests:** `tests/entity/test_gravestone.py` (6 tests); `tests/screen/test_worldScreen_gravestone.py` (5 tests); `tests/world/test_roomJsonReaderWriter.py` extended with 4 new gravestone tests.
- **Validation:** All 426 tests pass (411 existing + 15 new).

### 2026-04-20 — Resolve PR review threads for test-DI refactor
- Added thread-safe public registration snapshot/restore APIs to the DI container:
  `Container.getRegistration(...)` and `Container.restoreRegistration(...)`.
- Updated `tests/conftest.py` override fixture to use those APIs instead of direct
  mutation of `container._registrations`.
- Normalized `tests/ui/test_status.py` imports to consistently use `ui.*`
  module paths (`ui.hotbarLayout`).
- Added unit tests for the new container APIs in `tests/di/test_container.py`.
- Validation: full suite passed (`411 passed`).

### 2026-04-20 — Clean Code refactoring of worldScreen.py
- **Refactored:** `src/screen/worldScreen.py` (2122 → 1963 lines, -159 lines)
- **Persistence delegation:** Replaced inline save/load methods
  (`savePlayerLocationToFile`, `loadPlayerLocationFromFile`,
  `savePlayerAttributesToFile`, `loadPlayerAttributesFromFile`,
  `savePlayerInventoryToFile`, `loadPlayerInventoryFromFile`, `saveRoomToFile`)
  with thin wrappers delegating to `WorldScreenPersistence` (`self.persistence`).
- **pickupableEntities delegation:** Replaced 30-line `canBePickedUp` method with
  call to imported `canBePickedUp()` function from `pickupableEntities.py`.
- **Method extractions from `draw()`:** `_drawDayNightOverlay(gameArea)`,
  `_drawHotbar()`, `_drawDebugInfo()`.
- **Method extractions from `run()`:** `_processEvents()`,
  `_updateLivingEntities()`, `_updateGameState()`.
- **Method extractions from `changeRooms()`:** `_loadOrGenerateRoom(x, y)`,
  `_calculateTargetLocationForRoomTransition(playerLocation)`.
  `_loadOrGenerateRoom` is also reused by `_updateLivingEntities()`, eliminating
  duplicated room-loading logic that was previously inlined in `run()`.
- **Method extraction from `executePlaceAction()`:**
  `_plantWheatSeed(targetLocation, targetRoom)`.
- **Method extractions from `handleKeyDownEvent()`:**
  `_handleMovementKey(direction)`, `_handleHotbarKey(key)`.
- **Method extractions from `handleMouseDownEvent()`:**
  `_handleHotbarClick(hotbarIndex)`, `_handleWorldClick()`.
- **Cooldown consolidation:** Three near-identical cooldown checkers consolidated
  into `_checkCooldown(tickToCheck, speed)` with thin wrappers preserved.
- **Mouse wheel simplification:** Replaced two 7-line branches with modulo
  arithmetic: `(current + delta) % 10`.
- **Import cleanup:** Removed `jsonschema` and 14 entity imports that were only
  used in the old `canBePickedUp` method (Apple, Banana, Bed, Campfire, CoalOre,
  Fence, IronOre, JungleWood, Leaves, OakWood, StoneBed, StoneFloor, Torch,
  WoodFloor).
- **All 409 existing tests pass.**

### 2026-04-20 — Add day/night cycle
- **New file:** `src/world/dayNightCycle.py` — `DayNightCycle` class registered as
  `@component`; exposes `getOverlayOpacity(tick)` (sine-curve mapping 0–200),
  `getPhase(tick)` returning `day`/`dusk`/`night`/`dawn`, and `getLightMask(radiusPx)`
  for cached radial light masks.
- **Config:** Added `dayNightCycleEnabled` (default `true`) and
  `dayNightCycleLengthTicks` (default `54000` — 30 min at 30 tps) to `config.yml`
  and `Config` class. Default derived from `ticksPerSecond * 30 * 60`.
- **Rendering (`src/screen/worldScreen.py`):** After rooms are drawn and before
  the clip is removed, a per-pixel alpha overlay (`pygame.SRCALPHA`) is filled at
  the computed opacity and blitted onto the game area rect. Light-emitting entities
  (Torch, Campfire) punch radial gradient holes in the overlay via
  `BLEND_RGBA_MIN`. Overlay surface is only reallocated when the game area size
  changes.
- **Light sources:** New `Torch` entity (`src/entity/torch.py`) with `lightRadius=6`,
  craftable from 1× OakWood + 1× CoalOre (yields 2). Campfire (`src/entity/campfire.py`)
  updated with `lightRadius=8`. Both entities reduce day/night darkness in a
  circular area when placed.
- **Bug fix:** Fixed `_collectLightSourcesFromRoom` crash — `grid.getLocations()`
  returns a dict; iteration must use `for locationId in grid.getLocations()`
  followed by `grid.getLocation(locationId)` (matching existing codebase pattern).
- **Debug info:** When `config.debug` is `True` and the cycle is enabled, the
  current phase and overlay opacity are shown in the top-right debug text area.
- **Settings (`src/screen/configScreen.py`):** Added "Day/Night Cycle" toggle
  button consistent with existing toggles.
- **Entity registries:** Torch registered in `roomJsonReaderWriter.py`,
  `inventoryJsonReaderWriter.py`, `canBePickedUp()`, and `recipeRegistry.py`.
- **Tests:** Added unit tests in `tests/world/test_dayNightCycle.py`, plus
  `tests/entity/test_torch.py`, `tests/entity/test_campfire_light.py`,
  `tests/crafting/test_torchRecipe.py`. Updated config defaults test.
- **Bug fix:** Fixed inverted light mask — `getLightMask()` was creating alpha=0
  background with filled circles, causing square bright areas when blitted via
  `BLEND_RGBA_MIN`. Rewrote to use per-pixel distance field: background alpha=255,
  centre alpha=0, smooth radial gradient to edge.
- **Implementation detail:** `_collectLightSourcesFromRoom` iterates all entities
  at each location when collecting active light sources.
- **Performance:** Optimized light source rendering to reduce per-frame TPS drop:
  merged light source collection into the existing room drawing pass (eliminates
  duplicate room iteration), cached scaled light masks across frames keyed by
  opacity (only regenerated when opacity changes), used `getNumEntities()` for fast
  empty-location skipping, and replaced `math.hypot()` with squared-distance
  comparison plus pre-computed `invRadius` multiplier in mask generation.
- **Test improvement:** Added alpha profile assertions to light mask tests: center
  transparency, corner opacity, and edge opacity checks.
- **Bug fix:** Fixed minimap rendering black rectangles and discontinuous map
  content — `saveCurrentRoomAsPNG()` was drawing the room onto the main display
  (which still held the previous frame's day/night overlay) then capturing from a
  misaligned offset. Rewrote to render onto a clean off-screen surface with the
  room's background color, producing overlay-free minimap tiles.
- **Robustness:** Wrapped display swap and player removal/re-add in
  `saveCurrentRoomAsPNG()` with `try/finally` to guarantee state restoration if
  `Room.draw()` throws.
- **Defensive guard:** `getLightMask()` now clamps `radiusPx <= 0` to 1,
  preventing `ZeroDivisionError` and invalid surface sizes.
- **Test cleanup:** Replaced repeated `pygame.init()`/`pygame.quit()` calls in
  light mask tests with a shared `pygame_init` pytest fixture. Added edge-case
  tests for zero and negative radius inputs with alpha profile assertions.

### 2026-04-20 — Add farming system (planting, growing, harvesting)
- **New entity files:**
  - `src/entity/wheatSeed.py` — `WheatSeed` (DrawableEntity, solid=False)
  - `src/entity/youngCrop.py` — `YoungCrop` (DrawableEntity, solid=False, stores `tickPlanted`)
  - `src/entity/matureCrop.py` — `MatureCrop` (DrawableEntity, solid=False, stores `tickPlanted`)
  - `src/entity/wheat.py` — `Wheat` (Food, solid=False, energy 10–20)
- **New placeholder assets:** `assets/images/wheatSeed.png`, `youngCrop.png`, `matureCrop.png`, `wheat.png` (32×32 RGBA)
- **Config:** Added `cropGrowthTicks` (default 1800) to `src/config/config.py`
- **Growth logic:** Added `tickCrops(tick, config)` to `src/world/room.py` — YoungCrop → MatureCrop after `cropGrowthTicks` ticks
- **World screen (`src/screen/worldScreen.py`):**
  - Called `tickCrops` from the tick loop alongside `tickExcrement`
  - Added planting logic to `executePlaceAction()` — WheatSeed on Grass → YoungCrop
  - Added harvesting logic to `executeGatherAction()` — MatureCrop → Wheat in inventory
  - Added all four new entities to `canBePickedUp()`
- **Crafting:** Added Wheat Seed recipe (1× Grass → 3× WheatSeed) to `recipeRegistry.py`;
  extended `Recipe` class with `resultCount` parameter and updated `craft()` to return a list
- **Persistence:**
  - Added WheatSeed, Wheat, YoungCrop, MatureCrop to `roomJsonReaderWriter.py` and `inventoryJsonReaderWriter.py`
  - YoungCrop/MatureCrop serialize/deserialize `tickPlanted`
- **README:** Updated Controls table with farming actions
- **Tests:** Added 21 new tests across 6 test files:
  - `tests/entity/test_wheatSeed.py`, `test_youngCrop.py`, `test_matureCrop.py`, `test_wheat.py`
  - `tests/crafting/test_wheatSeedRecipe.py`
  - `tests/world/test_cropGrowth.py`
  - Updated `tests/world/test_roomJsonReaderWriter.py` with crop entity serialization tests
  - Updated `tests/crafting/test_recipe.py` for list return from `craft()`

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

### 2026-04-20 — Test DI container for pytest suite
- Added shared test DI setup in `tests/conftest.py`:
  - autouse container initialization per test via `bootstrap.createContainer()`
  - standardized headless SDL env defaults for tests
  - common fixtures: `test_config`, `test_graphik`, `di_container`, `resolve`,
    `override_dependency`
  - test-only transient registrations for `InventoryJsonReaderWriter` and
    `CodexJsonReaderWriter`
  - override restoration logic to prevent dependency registration leakage
    across tests.
- Refactored tests to resolve DI-managed classes through the container instead
  of manual construction in:
  - `tests/inventory/test_inventoryJsonReaderWriter.py`
  - `tests/stats/test_stats.py`
  - `tests/mapimage/test_mapImageUpdater.py`
  - `tests/player/test_player.py`
  - `tests/world/test_map.py`
  - `tests/world/test_roomFactory.py`
  - `tests/world/test_roomJsonReaderWriter.py`
  - `tests/world/test_roomPreloader.py`
  - `tests/world/test_tickCounter.py`
  - `tests/world/test_dayNightCycle.py`
  - `tests/codex/test_codex.py`
  - `tests/codex/test_codexScreen.py`
  - `tests/ui/test_status.py`
  - `tests/ui/test_hudDragManager.py`
- Validation: full suite still passes (`409 passed`).

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
- 2026-04-20: `[not yet integrated]` The `Recipe.craft()` method now
  returns a list of result entities (to support multi-item output like
  1× Grass → 3× WheatSeed). Callers (e.g., `inventoryScreen.craftRecipe`)
  must iterate the list and add each item individually.
- 2026-04-20: `[not yet integrated]` Entities with tick-based state
  (like `tickPlanted` on `YoungCrop`/`MatureCrop` or `tickCreated` on
  `Excrement`) must be handled specially in both JSON reader/writers:
  they need custom constructor calls in `_createEntity`, serialization
  in `generateJsonForEntity`, and a separate registry in the inventory
  reader/writer.
- 2026-04-20: `[not yet integrated]` When adding a new screen type, the
  following files must be updated: `src/screen/screenType.py` (new constant),
  `src/roam.py` (import, resolve in `_initializeDependencies`, handle in
  `run()`), and the originating screen's `handleKeyDownEvent()`. New screens
  should follow the `ControlsScreen` pattern: `@component` class with
  `graphik`, `config` constructor params, a `run()` loop, and
  `changeScreen`/`nextScreen` flow control.
- 2026-04-20: `[integrated]` The `WorldScreen.draw()` method uses
  `set_clip(gameArea)` / `set_clip(None)` to restrict rendering to the game
  area square. Overlays that should only affect the game area (like the
  day/night cycle) must be blitted while the clip is still active. HUD
  elements drawn after `set_clip(None)` are unaffected by the clip and
  render over the full display including letterbox bars.
- 2026-04-20: `[not yet integrated]` `grid.getLocations()` (from
  `src/lib/pyenvlib/grid.py`) returns a **dict** keyed by UUID, not a
  list of Location objects. The codebase convention is
  `for locationId in grid.getLocations():` followed by
  `location = grid.getLocation(locationId)`. Iterating with
  `for location in grid.getLocations()` yields UUID keys, not Locations,
  and will crash when calling Location methods.
- 2026-04-20: `[not yet integrated]` `worldScreen.py` now delegates
  save/load operations to `WorldScreenPersistence` (in
  `src/screen/worldScreenPersistence.py`) and entity pickup checks to
  `canBePickedUp()` (in `src/screen/pickupableEntities.py`). When adding
  new pickupable entity types, add them to `PICKUPABLE_TYPES` in
  `pickupableEntities.py` instead of modifying worldScreen.py. When
  modifying save/load logic, edit `worldScreenPersistence.py`.
- 2026-04-20: `[not yet integrated]` The `DrawableEntity` base class now accepts
  an optional `solid` parameter (default `False`) and provides `isSolid()`. Entity
  subclasses no longer need to define `self.solid` or `isSolid()` unless they need
  non-default solid behavior. Solid entities should pass `True` as the third argument
  to `DrawableEntity.__init__()`. Non-solid entities can omit it entirely since the
  default is `False`.
- 2026-04-20: `[not yet integrated]` The `ConfigScreen` uses a data-driven approach
  for toggle buttons: a list of `(label, configAttribute)` tuples drives both rendering
  and toggling via `_toggleConfigAttribute(attributeName)`. When adding new toggleable
  config options, add a tuple to the `toggleButtons` list in `drawMenuButtons()` rather
  than creating a new method.
- 2026-04-20: `[integrated]` The `Map` class accepts optional `roomFactory` and
  `roomJsonReaderWriterFactory` constructor parameters (both default to `None`). When
  provided via DI (see `bootstrap.py`), these prevent manual instantiation of
  `RoomFactory` and `RoomJsonReaderWriter` inside `Map`. Without these parameters
  (e.g., in tests), `Map` falls back to manual construction for backward compatibility.
  New code that needs a `RoomJsonReaderWriter` inside a DI-wired class should follow
  this factory-callback pattern rather than importing and instantiating the class directly.
- 2026-04-20: `[integrated]` The test suite now has a shared DI container
  bootstrap in `tests/conftest.py` with an autouse fixture. Prefer `resolve(...)`
  in tests for DI-managed classes and use `override_dependency(...)` for test-specific
  mocks; the fixture restores overridden registrations after each test to avoid state
  leakage between tests.
- 2026-04-21: `[not yet integrated]` When writing tests that use `isinstance` with
  classes that are also imported by source modules without the `src.` prefix, the test
  must use the same import path as the source. For example, if `worldScreen.py` imports
  `from entity.gravestone import Gravestone`, and a test imports
  `from src.entity.gravestone import Gravestone`, the `isinstance` check will fail
  because Python treats them as distinct classes. Tests in `tests/entity/` and
  `tests/world/` should consistently use bare imports (e.g., `from entity.gravestone
  import Gravestone`) to match source imports.
- 2026-04-21: `[not yet integrated]` A freshly constructed `DrawableEntity` (or
  subclass) has default IDs of `-1` (from the `Entity` base class in `pyenvlib`).
  Calling `str(entity.getEnvironmentID())` returns `"-1"`, which is not a valid UUID
  string. Round-trip tests that serialize then deserialize an entity using
  `roomJsonReaderWriter` must set proper UUID values with `entity.setEnvironmentID(uuid4())`,
  `entity.setGridID(uuid4())`, and `entity.setLocationID(str(uuid4()))` before generating
  JSON.
- 2026-04-23: `[not yet integrated]` `MapImageGenerator.getRoomImages()` and `clearRoomImages()` both call `os.listdir(roompngs)` and will raise `FileNotFoundError` if the directory does not yet exist. The `roompngs` directory is created lazily by `saveCurrentRoomAsPNG()` (called from `draw()` on the main thread), but `updateMapImage()` can be triggered earlier by `_doSave()` on the `_saveExecutor` background thread. Guard both methods with `os.path.isdir` to return early / return `[]` when the directory is missing.
- 2026-04-23: `[not yet integrated]` `Map` now tracks freshly generated rooms in
  `_freshlyGeneratedRooms` (a `set` protected by `_lock`). A room is flagged when
  `generateNewRoom()` creates it for the first time; loading a room via `addRoom()` or
  `getRoom()` (from disk) does NOT set the flag. `consumeIsNewRoom(x, y)` atomically
  checks and clears the flag — returns `True` exactly once per newly generated room.
  `WorldScreen._loadOrGenerateRoom()` now calls `consumeIsNewRoom` to decide whether to
  increment `rooms explored`; this handles both the pre-loaded (RoomPreloader background
  thread) and direct-generate path uniformly. Pass `updateStats=False` when calling
  `_loadOrGenerateRoom` for non-player transitions (e.g., living-entity cross-room moves)
  so the flag is not consumed and stats are not affected. This remains not yet integrated
  because it is a localized implementation detail for `Map`/`WorldScreen` room-generation
  and stats behavior, not a repository-wide contributor convention for
  `.github/copilot-instructions.md`.
- 2026-04-23: `[not yet integrated]` When searching for Clean Code naming issues, Python's built-in `type` is a common shadowing victim — any method parameter named `type` (as in `getNumItemsByType(self, type)`) silently hides the built-in. Rename to a descriptive name like `itemType`. Similarly, predicate methods that return bool should be named with `is`/`has` prefixes, not `if` (e.g., `ifCorner` → `isCorner`). When the same string-building expression appears in multiple methods, extract it into a single private helper rather than duplicating it.

