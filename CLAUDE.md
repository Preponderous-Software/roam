# Roam — Claude Code guidelines

## Frontend abstraction

Roam has two rendering frontends behind the same `Renderer` / `InputSource` / `Clock` interfaces:

- **pygame** (`PygameRenderer`, `PygameInputSource`) — the default desktop frontend
- **text / TUI** (`TextRenderer`, `TextInputSource`, `TextClock`) — launched with `--text`; runs in any terminal with no display server

**When adding any drawing, input, or HUD feature, you must handle both frontends.** The common pattern is:

```python
isTextMode = not self.renderer.supportsImageLoading()
if isTextMode:
    # character-grid rendering path
else:
    # pygame / image-based path
```

Key contracts:
- `supportsImageLoading()` returns `False` in text mode, `True` in pygame.
- `loadImage(path)` returns a one-character glyph string in text mode; a pygame Surface in pygame mode. Pass the return value straight to `drawImage` — never inspect its type.
- `getGameAreaRect()` always returns a `geometry.Rect` (has `.x`, `.y`, `.width`, `.height`, `.right`, `.bottom`). Never assume it returns a tuple.
- All key checks use `KeyCode` enum values — never compare against raw integers.

## World view seam (3D, RFC 0017)

Next to the pixel-shaped `Renderer`, game logic can publish a world-shaped, read-only `WorldView` for 3D frontends and the spectator:

- `src/rendering/worldView.py`: immutable `WorldView` / `RoomView` / `ActorView` / `LightView` / `CameraHint`. They hold primitives and tuples only, never live `Entity`/`Room` objects, and reassignment raises. Read them through getters (no `@property`).
- `src/rendering/worldViewSink.py`: `WorldViewSink` (`wantsWorldView()` defaults to `False`, plus `getWantedRadiusRooms()` and `publish(view)`) and `NullWorldViewSink`, the default registered in `bootstrap.py`. A frontend that draws from views registers its own sink.
- `src/world/worldViewBuilder.py`: builds a view from **already-loaded rooms only**. It must never call `Map.getRoom` (that loads from disk), `Map.generateNewRoom`, `RoomFactory`, `WorldScreen.getOrLoadRoom` or any `*JsonReaderWriter`, because viewing must not change saves (`tests/api/test_snapshotSaveSafety.py`). It caches each room by `Room.getRevision()`, which `world/trackedLocation.TrackedLocation` bumps on every entity add/remove/`setEntities`. Any new way of changing a location's entities must go through those `Location` methods, or 3D views go stale. The revision is in memory only and must never be saved (`tests/world/test_roomJsonReaderWriterFieldPin.py`).
- `WorldScreen._publishWorldView()` runs once per tick, after game logic and before `draw()`, and builds only when some sink wants a view. **2D frontends never ask, so they must stay at zero cost.** Do not add work outside that `wantsWorldView()` check.
- `Renderer.drawsWorldFromView()` defaults to `False` (every 2D backend). When a frontend returns `True` (only the opt-in web 3D view, `/play?view=3d`), `WorldScreen.draw()` skips the world tiles and day/night overlay, still loads the same rooms through `getOrLoadRoom`, calls `Renderer.clearRegion(gameArea)`, and draws the HUD as usual. That frontend registers `rendering/web3dWorldViewSink.Web3DWorldViewSink` through `getWorldViewSink()` (`roam.registerFrontendWorldViewSink`).
- Light sources: use `world/lightSources.py` (`isLightSource`, `collectLightSources`). It is shared by the 2D day/night overlay and the builder.

**REST snapshot and spectator.** With `restEnabled: true`, `GET /api/v1/snapshot?radius=R` (0–3) serves the latest published view as JSON, and `/spectator/` serves the three.js page (`spectator/index.html`, which loads sprites from `/assets/images/`). The REST server's sink builds **on demand**: only while the snapshot was polled in the last 5 s, at most every 0.25 s, at the radius asked for. So the first poll can return 503 ("no world view published yet"). Everything stays GET-only and bound to `127.0.0.1`. Browser check: `tests/integration/test_spectator_smoke.js` (CI job "3D spectator").

## Keybindings

- Primary bindings use F-keys or mouse where appropriate for desktop (e.g. F1 for help, F3 for debug).
- Every action that a terminal user needs must have an alt binding using an ASCII key. Add it to `DEFAULT_BINDINGS` and `ACTION_LABELS` in `src/config/keyBindings.py`, then check for it alongside the primary in `_handleUtilityKey` (or the relevant screen handler) with `or key == kb.getKey("alt_<action>")`.
- Alt bindings in the Controls screen render indented in `palette.MEDIUM_GRAY` (detected by `action.startswith("alt_")`).

## Tests

Run the full suite with:
```
python3 -m pytest tests/
```

For straight-line functionality verification against the text/TUI frontend
(boot to a screen, send keys, expect text), prefer adding a `.roamscript`
file under `tests/integration/scripts/` over a hand-written
`TextPlaythrough` test — see `docs/roamscript.md`. `test_roam_scripts.py`
discovers and runs every script automatically; no wiring needed.

Formatting is enforced by **black** (`python3 -m black src tests`). CI runs black in check mode — always format before pushing.

After any text-interface change, verify:
1. `python3 -m pytest tests/rendering/ tests/config/ -q` — all text-interface unit tests pass
2. `python3 -m pytest tests/screen/ tests/ui/ -q` — pygame-facing screen tests pass
3. `python3 -m black --check src tests` — no formatting violations
