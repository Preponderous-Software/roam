# Frontend Abstraction Plan — decoupling Roam from pygame

> 📊 **Visual companion:** [`renderer-architecture.html`](renderer-architecture.html)
> — an interactive diagram of the shipped seam (Renderer / InputSource / Clock)
> and how Pygame, Null, SDL, Web, and Text frontends each implement it. Open it
> in any browser (self-contained, no dependencies).


> Status: **proposal / not yet implemented.** No source has been changed. This
> document is the agreed target architecture and phased migration plan for
> letting Roam run behind multiple frontends (pygame today; text and web
> later) without rewriting game logic.

## 1. Goal

Today every screen talks to pygame directly — for drawing *and* for input.
The goal is a clean seam so the same screen/game logic can drive:

- the existing **pygame** desktop frontend,
- a **text/curses** frontend,
- a **web** frontend (e.g. a server pushing draw-ops to a canvas client),

by implementing two interfaces — one for output, one for input — plus a small
set of backend-neutral value types. Game logic should never import `pygame`.

This is a **refactor**, not a feature: the deliverable is the seam and the
pygame implementation behind it. Building an actual text or web frontend is
follow-on work that this plan unblocks.

## 2. Current state (measured, not estimated)

Baseline: `python3 -m pytest -q` → **621 passed** (pygame 2.1.2, SDL dummy
driver). This suite is the safety net for every phase below; the live game
cannot be launched in CI/sandbox, so headless tests + `roam.py --selftest`
are the verification anchors.

### Coupling inventory

`pygame` is imported in **20 source files**, not just the renderer:

| Layer | Files | Nature of coupling |
|---|---|---|
| Rendering facade | `lib/graphik/src/graphik.py` | wraps `pygame.draw` / font / mouse |
| Screens (10) | `src/screen/*.py` | event loops, keycodes, mouse, raw surface |
| HUD widgets | `ui/status.py`, `ui/energyBar.py`, `ui/hudDragManager.py` | `getGameDisplay().get_size()`, `pygame.Rect` |
| Entities | `entity/drawableEntity.py` | `pygame.image.load`, `pygame.Surface` |
| World | `world/room.py`, `world/dayNightCycle.py` | surface fills / color |
| Input model | `config/keyBindings.py` | **stores `pygame.K_*` ints as binding values** |
| Misc | `screen/screenshotHelper.py`, `mapimage/mapImageGenerator.py` | `pygame.image`, `pygame.transform`, `pygame.Surface` |
| Entry point | `roam.py` | `pygame.init`, display mode, `pygame.quit` |

Raw-surface operations reached through `getGameDisplay()` / `gameDisplay`:

```
 47  get_size        21  get_width      21  get_height
 12  blit            11  fill            2  set_clip
```

Direct `pygame.*` symbol usage outside `lib/` (top): `pygame.mouse` (23),
`pygame.display` (20), `pygame.event` (11), `pygame.QUIT` (11),
`pygame.KEYDOWN` (10), `pygame.K_*` keycodes (~30 sites, 7 distinct in
screens + the full default map in `keyBindings.py`), `pygame.transform` (9),
`pygame.image` (7), `pygame.Surface` (7), `pygame.Rect` (7),
`pygame.MOUSEWHEEL` (5), `pygame.SRCALPHA` (4), `pygame.time.Clock` (frame
pacing in `worldScreen`).

### The screen pattern today

Every screen owns its loop and pumps pygame directly:

```python
def run(self):
    while not self.changeScreen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: ...
            elif event.type == pygame.KEYDOWN: self.handleKeyDownEvent(event.key)
        self.graphik.getGameDisplay().fill((0, 0, 0))   # reaches past the facade
        self.drawStuff()                                 # via self.graphik.drawX
        pygame.display.update()                          # reaches past the facade
    return self.nextScreen
```

So there are **two** leaks to close, not one:
1. **Output** — screens bypass `Graphik` to touch the raw surface 104×.
2. **Input** — screens read `pygame.event` / `pygame.K_*` / `pygame.mouse`
   directly, and `KeyBindings` *stores pygame keycodes as its data model*.

### Known clean-code defects to fix along the way

- `graphik.py` defines **two `__init__` methods**; Python keeps only the
  second, so the first (with default 900×600 + color constants) is dead code.
- Color literals (`(0,0,0)`, `(255,255,255)`, `(255,0,255)`, …) are repeated
  across screens/widgets as raw tuples — candidates for a shared palette.

## 3. Target architecture

```
            ┌────────────────────────────────────────────┐
            │              Game / Screen logic            │
            │   (screens, HUD widgets, world, entities)   │
            │        depends ONLY on the interfaces        │
            └───────────────┬───────────────┬─────────────┘
                            │               │
                   Renderer │               │ InputSource
                  (output)  │               │ (input)
            ┌───────────────▼───┐   ┌────────▼────────────┐
            │  PygameRenderer   │   │  PygameInputSource  │   ← today
            │  TextRenderer     │   │  TextInputSource    │   ← later
            │  WebRenderer      │   │  WebInputSource     │   ← later
            └───────────────────┘   └─────────────────────┘
```

Supporting backend-neutral types (no pygame):
- `ui/geometry.py` → `Rect`, `Size`, `Point` (replace `pygame.Rect`).
- `ui/inputEvent.py` → `InputEvent` + `EventType` enum + `KeyCode` enum.
- `ui/palette.py` → named colors (kills scattered RGB tuples).
- `screen/Screen` (base class) → owns the run-loop skeleton so individual
  screens stop pumping pygame.

### 3a. `Renderer` interface (output)

Derived directly from operations screens actually use. New ABC at
`src/rendering/renderer.py`:

```python
class Renderer(ABC):
    # lifecycle / surface
    def getDisplaySize(self) -> Size: ...          # replaces getGameDisplay().get_size()
    def getGameAreaRect(self) -> Rect: ...         # already on Graphik
    def clearScreen(self, color) -> None: ...      # replaces gameDisplay.fill(color)
    def present(self) -> None: ...                 # replaces pygame.display.update()
    def setClipRegion(self, rect | None) -> None:  # replaces set_clip (2 sites)

    # primitives (already on Graphik — keep signatures)
    def drawRectangle(self, x, y, w, h, color): ...
    def drawText(self, text, x, y, size, color): ...
    def drawImage(self, image, x, y): ...          # replaces gameDisplay.blit (12 sites)

    # button: see §5.1 — split interaction out of rendering
    def drawButton(self, x, y, w, h, boxColor, textColor, textSize, text): ...
```

`Graphik` becomes `PygameRenderer` (or keeps the name and *implements*
`Renderer`). The dead `__init__` is deleted. `getGameDisplay()` is retained
**only** internally to the pygame impl; callers stop using it.

### 3b. `InputSource` interface (input)

New ABC at `src/rendering/inputSource.py`:

```python
class InputSource(ABC):
    def pollEvents(self) -> list[InputEvent]: ...   # replaces pygame.event.get()
    def isPressed(self, keyCode) -> bool: ...       # replaces pygame.key.get_pressed()
    def getMousePosition(self) -> Point: ...        # replaces pygame.mouse.get_pos()
    def getMouseButtons(self) -> MouseButtons: ...   # replaces pygame.mouse.get_pressed()
```

`InputEvent` is a small dataclass: `type: EventType` (`KEY_DOWN`, `KEY_UP`,
`MOUSE_DOWN`, `MOUSE_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `QUIT`, `RESIZE`,
`TEXT_INPUT`, `FOCUS_LOST`/`FOCUS_GAINED`), plus optional `key`, `pos`,
`button`, `text`, `size` fields. `KeyCode` is a backend-neutral enum; the
pygame input source maps `pygame.K_*` ↔ `KeyCode` at the boundary.

### 3c. `KeyBindings` data-model change (the subtle one)

`KeyBindings.DEFAULT_BINDINGS` currently stores raw `pygame.K_*` ints as
*values*. To decouple, bindings must store `KeyCode` enum members instead, and
the pygame frontend maps incoming pygame keys → `KeyCode` before lookup.
- `getKeyName()` (uses `pygame.key.name`) moves behind the frontend or a
  `KeyCode.displayName` table.
- Config persistence (`key_*` ints in `config.yml`) needs a stable int value
  per `KeyCode` so existing saved keybindings keep working — **back-compat
  requirement**, covered by tests in Phase 4.

### 3d. `Screen` base class

Collapse the duplicated `while not self.changeScreen: for event in
pygame.event.get(): …` skeleton into a base class that takes a `Renderer` +
`InputSource`, runs the loop, and calls overridable
`handleEvent(event)` / `draw()` hooks. Removes ~10 copies of the loop and is
where `present()` / `clearScreen()` get called once.

## 4. The hard parts (and how each is handled)

| Problem | Plan |
|---|---|
| **Immediate-mode `drawButton`** polls the mouse *inside* the renderer and fires a callback on click. That fuses input+output and won't port to text/web. | Split: renderer only *draws* the button; hit-testing + click dispatch moves to a `Button`/widget helper driven by `InputSource`. See §5.1. Behavior-preserving. |
| **`pygame.Rect`** used as a geometry value type in HUD layout + drag manager. | Introduce `ui/geometry.py::Rect` (plain dataclass with `collidepoint`, `move`, etc.). Mechanical replace; pygame impl can convert to `pygame.Rect` only where it draws. |
| **Offscreen surfaces / `transform` / `image.load`** (minimap, map image gen, entity images, fallback magenta square). | Define an opaque `Image` handle in the Renderer API (`loadImage(path) -> Image`, `scaleImage`, `createSurface`, `blitToImage`). pygame impl wraps `pygame.Surface`. Minimap compositing becomes renderer calls. |
| **Frame pacing** (`pygame.time.Clock().tick(tps)` in worldScreen). | Add `clock`/`tick(fps)` to the frontend (InputSource or a small `Clock` from the frontend factory). Text/web supply their own pacing. |
| **Display init / fullscreen / resize / icon** in `roam.py`. | Move into a `Frontend` factory (`createFrontend(config) -> (Renderer, InputSource)`) that owns `pygame.init`, mode set, icon, and `quit`. `roam.py` depends on the factory, not pygame. |
| **Screenshot** (`screenshotHelper` saves the surface). | `Renderer.captureScreenshot(path)`; pygame impl keeps current behavior, others no-op or HTML2canvas-style. |
| **DI wiring** (`@component`, `createContainer`). | Register `Renderer` + `InputSource` interfaces in `bootstrap.py`; screens type-hint the interfaces so auto-wiring is unchanged. `roam.py` registers the pygame instances like it does `Graphik` today. |

### 5.1 drawButton split (illustrative)

```python
# before: renderer draws AND polls mouse AND calls function on click
graphik.drawButton(x, y, w, h, box, text, size, label, onClick)

# after: draw is pure; interaction handled by the loop via InputSource
renderer.drawButton(x, y, w, h, box, textColor, size, label)
if button_rect.collidepoint(input.getMousePosition()) and clicked_this_frame:
    onClick()
```

A `Button` widget can encapsulate both halves so call sites stay terse.

## 5. Phased rollout (each phase ends test-green)

Ordered so the **safe, fully-verifiable output seam lands first** and the
riskier input work is isolated and incremental.

- **Phase 0 — Hygiene (tiny, zero behavior change).**
  Delete the dead `__init__` in `graphik.py`; add `ui/palette.py` and replace
  the most-repeated color literals. Confirms tooling/test loop. *Verify:*
  pytest 621 green + `black`/`autoflake`.

- **Phase 1 — Renderer output seam.**
  Add `Renderer` ABC; make `Graphik` implement it; add `getDisplaySize`,
  `clearScreen`, `present`, `setClipRegion`, `drawImage`. Replace all 104
  `getGameDisplay()` reach-throughs + 12 `pygame.display.update()` with
  facade calls. Update `conftest.py` `test_graphik` fixture to spec the new
  methods (e.g. `getDisplaySize.return_value = Size(1280, 720)`).
  *Verify:* pytest green; no `getGameDisplay()` outside the pygame impl
  (`grep`), no `pygame.display` outside frontend.

- **Phase 2 — Geometry + Image value types.**
  Introduce `ui/geometry.py`; replace `pygame.Rect` in widgets/HUD/drag.
  Introduce `Image` handle; route entity/minimap/mapimage surfaces through
  the Renderer. *Verify:* pytest green (HUD/status/energyBar/drag tests exist).

- **Phase 3 — Frontend factory + Screen base class.**
  `createFrontend(config)`; move `pygame.init`/mode/icon/quit/clock out of
  `roam.py` and screens. Extract the run-loop skeleton into a `Screen` base.
  *Verify:* pytest green; `roam.py --selftest` passes; manual smoke of pygame
  build by the maintainer (cannot be automated here — **flagged**).

- **Phase 4 — Input seam.**
  Add `InputSource` + `InputEvent` + `KeyCode`; convert `KeyBindings` to store
  `KeyCode` with int-stable config back-compat; convert each screen's event
  handling to consume `InputEvent`s. Do screens **one per commit** (10
  commits) — smallest first (`mainMenuScreen`, `statsScreen`) → largest
  (`worldScreen`). Split `drawButton` interaction out (§5.1).
  *Verify per screen:* pytest green; the existing hotbar/key tests in
  `tests/screen/` exercise dispatch and must pass unmodified in intent.

- **Phase 5 — Prove the seam.**
  Add a minimal `NullRenderer`/`NullInputSource` (or a tiny text renderer) used
  only in a new test asserting a screen renders one frame without importing
  pygame. This is the executable proof the abstraction holds. No real text/web
  frontend is built here — that's separate feature work.

## 6. Test & verification strategy

- **Anchor:** `python3 -m pytest -q` must stay at ≥621 passing every phase.
  (`python` is 2.7 on this box — always invoke `python3`; SDL dummy driver is
  set in `conftest.py` and screen tests.)
- **Fixture impact:** `conftest.py::test_graphik` is `MagicMock(spec=Graphik)`
  with `getGameDisplay().get_size() → (1280,720)`. Any method screens newly
  call on the renderer must be added to the spec'd mock or layout math breaks.
  This is the main test-maintenance cost of Phase 1.
- **Formatter:** run `./format.sh` (black + autoflake) before each commit; the
  repo expects black-clean (`#428` proposes a `black --check` CI gate).
- **Grep gates** (cheap regression guards per phase):
  - Phase 1 done ⇒ `grep -rn getGameDisplay src --include='*.py'` only matches
    the pygame renderer impl.
  - Phase 4 done ⇒ `grep -rn 'pygame' src --include='*.py'` only matches files
    under `rendering/` (the frontend impls) + the frontend factory.
- **Unverifiable-by-agent (flag honestly):** the live pygame window (actual
  drawing, fullscreen, resize, mouse-drag HUD, minimap) cannot be exercised
  headless here. Each phase that changes runtime visuals needs a maintainer
  smoke-run; the plan keeps those changes in Phases 3–4 so reviewers know
  where to look.

## 7. Constraints honored

- **No new third-party dependencies** — only stdlib (`abc`, `enum`,
  `dataclasses`) and the existing pygame.
- **No public-contract changes** — `ScreenType` values, save format, config
  keys, and CLI (`--selftest`) are preserved; the `key_*` config back-compat
  is an explicit Phase 4 test.
- **Tests preserved** — signatures updated only where a refactor forces it
  (e.g. the `test_graphik` fixture); no test deleted.
- **Incremental** — every phase compiles and is test-green on its own, so the
  work can land as a series of reviewable PRs rather than one big-bang change.

## 8. Rough size

~20 source files touched. Phases 0–2 are mechanical and low-risk
(~the bulk of the 104+ call-site edits, all test-covered). Phases 3–4 carry
the real design risk (input model + run-loop ownership + keybinding data
model) and the only changes needing a live smoke test. Suggest landing 0–2 as
one PR, then 3, then 4 as one-screen-per-commit.

## 9. What a future frontend implements

To add a text or web frontend, implement two classes and one factory branch —
**no game-logic changes**:
- `XRenderer(Renderer)` — the ~10 draw/lifecycle methods.
- `XInputSource(InputSource)` — events + key/mouse state, mapping native input
  to `KeyCode`/`InputEvent`.
- a `createFrontend(config)` branch selecting the backend (e.g. via
  `config.frontend` or a CLI flag).
