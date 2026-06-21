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

## Keybindings

- Primary bindings use F-keys or mouse where appropriate for desktop (e.g. F1 for help, F3 for debug).
- Every action that a terminal user needs must have an alt binding using an ASCII key. Add it to `DEFAULT_BINDINGS` and `ACTION_LABELS` in `src/config/keyBindings.py`, then check for it alongside the primary in `_handleUtilityKey` (or the relevant screen handler) with `or key == kb.getKey("alt_<action>")`.
- Alt bindings in the Controls screen render indented in `palette.MEDIUM_GRAY` (detected by `action.startswith("alt_")`).

## Tests

Run the full suite with:
```
python3 -m pytest tests/
```

Formatting is enforced by **black** (`python3 -m black src tests`). CI runs black in check mode — always format before pushing.

After any text-interface change, verify:
1. `python3 -m pytest tests/rendering/ tests/config/ -q` — all text-interface unit tests pass
2. `python3 -m pytest tests/screen/ tests/ui/ -q` — pygame-facing screen tests pass
3. `python3 -m black --check src tests` — no formatting violations
