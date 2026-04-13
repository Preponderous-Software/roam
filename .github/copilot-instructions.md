## Project Overview

Roam is a single-player 2D survival game built with Python and Pygame. Players explore a procedurally-generated world, gather resources, manage an inventory, and interact with living entities (chickens, bears). There are no plans to add multiplayer.

## Technology Stack

- **Language:** Python
- **Game framework:** Pygame 2.1.2
- **Testing:** pytest 7.1.3, pytest-cov 4.0.0
- **Formatter:** Black (via `format.sh`), autoflake (unused import/variable removal)
- **Image processing:** Pillow 9.4.0
- **JSON schema validation:** jsonschema 4.17.3
- **Bundled libraries:** [graphik](https://github.com/Preponderous-Software/graphik) (vendored in `src/lib/graphik`), [py_env_lib](https://github.com/Preponderous-Software/py_env_lib) (vendored in `src/lib/pyenvlib`)
- **Version:** 0.8.0-SNAPSHOT (tracked in `version.txt`)

## Repository Layout

- **`src/`** — Main application source code.
  - `roam.py` — Entry point.
  - `config/` — Game configuration (`Config` class).
  - `entity/` — Game entities (resources like Apple, Stone, OakWood; living entities in `entity/living/`).
  - `inventory/` — Inventory system and JSON persistence.
  - `player/` — Player class.
  - `world/` — World map, rooms, room generation, tick counter.
  - `screen/` — Game screens (main menu, world, options, inventory, stats, config).
  - `ui/` — HUD elements (energy bar, status display).
  - `stats/` — Game statistics tracking.
  - `mapimage/` — Map image generation and updating.
  - `lib/` — Vendored third-party libraries (`graphik`, `pyenvlib`).
  - `media/` — Application icon.
- **`tests/`** — Unit tests mirroring `src/` structure (`entity/`, `inventory/`, `player/`, `stats/`).
- **`schemas/`** — JSON schemas for save-file validation (`inventory.json`, `room.json`, `playerAttributes.json`, etc.).
- **`assets/`** — Game asset images.
- **`pics/`** — Screenshot or promotional images.
- **`.vscode/`** — VS Code launch configuration.

## Coding Conventions

- **Naming:**
  - Classes use `PascalCase` (e.g., `DrawableEntity`, `RoomFactory`).
  - Methods and variables use `camelCase` (e.g., `getImagePath`, `livingEntities`).
  - Test functions use `snake_case` prefixed with `test_` (e.g., `test_initialization`).
  - Source files use lowercase for single-word modules (e.g., `apple.py`, `map.py`) and lowerCamelCase for multiword modules (e.g., `drawableEntity.py`, `roomFactory.py`).
  - Test files mirror the source module name with a `test_` prefix (e.g., `test_apple.py`, `test_drawableEntity.py`).
- **Indentation:** 4 spaces (Python standard).
- **Formatting:** Code is formatted with Black and cleaned with autoflake. Run `./format.sh` to format.
- **Docstrings/comments:** Author and date annotations appear as `# @author` / `# @since` comments above classes. Inline comments are used sparingly.
- **Patterns:**
  - Getter/setter methods (e.g., `getX()`, `setEnergy()`) rather than properties.
  - Inheritance from vendored library base classes (`Entity`, `Environment`).
  - Explicit `__init__` calls to parent classes (e.g., `Entity.__init__(self, name)`).
- **Anti-patterns to avoid:**
  - Do not introduce Python `@property` decorators — the codebase consistently uses explicit getters/setters.
  - Do not restructure the vendored `lib/` directory or update vendored libraries without explicit instruction.

## Testing

- **Framework:** pytest
- **Test location:** `tests/` directory, organized into subdirectories matching `src/` (e.g., `tests/entity/`, `tests/inventory/`).
- **Running tests:**
  - `python -m pytest` — run all tests.
  - `./test.sh` — run tests with verbose output and coverage report (generates `cov.xml`).
- **pytest configuration:** `pytest.ini` adds `.`, `src`, and `src/entity` to `pythonpath` — imports in tests resolve against these roots.
- **Coverage:** pytest-cov generates a terminal and XML coverage report via `test.sh`.
- **Headless Pygame:** CI sets `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy`. Tests that call `pygame.init()` should use a pytest fixture to ensure `pygame.quit()` is called after the test, avoiding leaked global state.

## CI/CD

- **Workflow:** `.github/workflows/tests.yml` runs the `Tests` workflow.
- **Triggers:** Push and pull request events targeting `main` or `master` branches.
- **Environment:** Ubuntu latest, Python 3.12, with `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` for headless Pygame.
- **Steps:** Installs dependencies (`pygame`, `pytest`, `pytest-cov`, `jsonschema`, `Pillow`), then runs `python -m pytest --verbose -vv --cov=src --cov-report=term-missing`.
- **Required checks:** The `test` job must pass before merging.

## AI Agent Guidelines

- Always read this file at the start of every session before making changes.
- Update `CHANGELOG.md` after every session in which files are modified, noting the date and a brief description of what was changed.
- Maintain the **Learning Log** section in `CHANGELOG.md`. Whenever you discover something about the repository that is not already documented — an undocumented convention, a non-obvious dependency, a gotcha, a useful pattern, or any context that would help a future AI agent work more effectively — append it to the learning log. This creates a feedback loop: insights gathered in one session inform every subsequent session.
- Each learning log entry must include an integration status — either `[not yet integrated]` or `[integrated]` — indicating whether the insight has been incorporated into this file (`.github/copilot-instructions.md`). If you notice that these instructions already contain a lesson from the learning log that is still marked `[not yet integrated]`, update its status to `[integrated]`.
- **Integrate learning log discoveries.** When writing or updating this file, review the Learning Log in `CHANGELOG.md` for entries marked `[not yet integrated]`. If an entry contains information that belongs here (e.g., an undocumented convention, a gotcha, or an implicit dependency), incorporate it into the appropriate section and update the entry's tag from `[not yet integrated]` to `[integrated]`.
- Do not rename or restructure files without a clear reason documented in the change log.
- Preserve existing conventions; do not introduce new patterns unless they are strictly necessary.
- When in doubt about intent, stop and ask rather than guessing.
- When writing Markdown files that contain triple-backtick code blocks (` ``` `), wrap the outer code fence with four or more backticks (`` ```` ``) so inner fences do not prematurely close the outer block.
