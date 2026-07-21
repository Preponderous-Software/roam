# RoamScript

RoamScript is a small line-oriented DSL for writing functionality-verification
scripts against the text/TUI frontend, without hand-writing a
`TextPlaythrough` driver per scenario. A script is a plain-text
`.roamscript` file: one command per line, run top to bottom against a fresh
game process.

- Interpreter: `tests/integration/roamScript.py`
- Example scripts: `tests/integration/scripts/*.roamscript`
- Pytest wrapper that runs every script in CI: `tests/integration/test_roam_scripts.py`

It's built on the existing `tests/integration/textPlaythrough.py` harness
(launches `roam.py --text` under a pseudo-terminal, matches on rendered
screen text), so it inherits the same constraint: **POSIX only** (needs a
pty) — it skips on Windows dev machines and runs on the ubuntu CI job.

## Running a script

As part of the suite:
```
python3 -m pytest tests/integration/test_roam_scripts.py -q
```

Standalone, for a quick manual verification pass (prints a step trace and
PASS/FAIL, exit code 0/1):
```
python3 tests/integration/roamScript.py tests/integration/scripts/create_save_and_enter_world.roamscript
```

## Grammar

Blank lines and lines starting with `#` are ignored. Every other line is
`COMMAND ARGS...`. Unquoted words are joined with a single space; quote an
argument (`"like this"`) to keep embedded spaces or to include text that
would otherwise look like a `timeout=` token.

| Command | Effect |
| --- | --- |
| `expect TEXT [timeout=N]` | Wait (up to `timeout` seconds, default the harness's boot timeout) for `TEXT` to appear in the rendered output. Fails the script if it never appears. |
| `send KEYS...` | Type keys. Each token is either a named key or sent as literal characters (see table below). |
| `assertContains TEXT [timeout=N]` | Like `expect`, but framed as an assertion with a short default timeout (`1.0`s) — use when `TEXT` should already be on screen. |
| `assertNotContains TEXT [timeout=N]` | Fails if `TEXT` appears within `timeout` seconds (default `0.5`). |
| `assertPathExists PATH` | Fails unless `PATH` (repo-relative) exists on disk. |
| `assertPathNotExists PATH` | Fails if `PATH` (repo-relative) exists on disk. |
| `resetBuffer` | Discard captured output so far. See "Re-visiting a screen" below — required before `expect`/`assertContains`/`assertNotContains` can prove anything about a screen you've already been on. |
| `wait SECONDS` | Pace the script without asserting anything. Prefer `expect`/`assertContains` — they fail fast and name what they were waiting for; reach for `wait` only when there's genuinely nothing to match on. |

Named `send` tokens:

| Token | Sends |
| --- | --- |
| `enter`, `return` | `\r` |
| `esc`, `escape` | Escape |
| `tab` | Tab |
| `backspace` | Backspace |
| `space` | Space |
| `up`, `down`, `left`, `right` | Arrow-key escape sequences |
| `ctrl+c` | `\x03` |
| anything else | sent as its literal characters |

`{saveName}` in any argument is replaced with the run's generated save name
(unique per run, auto-cleaned up afterward) — use it instead of hardcoding a
save name so scripts can run concurrently and don't leave state behind.

A script never needs to assert a clean exit itself: `runScript()` always
checks, after the last line, that the child process exited without dumping a
traceback — mirroring the `assert game.cleanExit()` convention in
`test_text_playthrough.py`.

## Re-visiting a screen

The captured output is a running transcript of everything the game has ever
printed, not a live snapshot of the current screen — it only ever grows.
That has two consequences:

- `expect`/`assertContains` for text a screen already showed once will match
  instantly from history the *next* time you visit that screen too, even if
  the real render is broken or slow — a false-pass risk, not real evidence.
- `assertNotContains` can only prove text *never appeared at all* in the
  whole run. It can't prove a "was on screen, now isn't" transition, because
  the earlier occurrence is still sitting in the transcript.

Call `resetBuffer` right before the transition you actually want evidence
for, so the following `expect`/`assertContains`/`assertNotContains` can only
match genuinely new output:

```
send esc
resetBuffer
expect Tick timeout=10
```

## Example

```
# Creating a save reaches the world and the HUD starts ticking.
expect Roam
send enter
expect Select Save
send c
expect Enter save name
send {saveName} enter
expect Tick timeout=15
assertContains TPS
```

## Adding a new script

Drop a `.roamscript` file in `tests/integration/scripts/` — `test_roam_scripts.py`
discovers and runs every file in that directory automatically, no wiring
needed. Prefer this DSL for straight-line "reach this screen / this text
shows up" verification; reach for a hand-written `TextPlaythrough`-based test
instead when a scenario needs real Python (loops, computed assertions,
inspecting files beyond existence).
