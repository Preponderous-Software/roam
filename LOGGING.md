# Logging

Roam uses [structlog](https://www.structlog.org/) for structured logging
across the codebase.

## Configuration

Logging behaviour is controlled by two environment variables:

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Minimum log level to emit |
| `LOG_FORMAT` | `pretty` | Output format (`pretty` or `json`) |

### Accepted log levels

| Level | Numeric | Use |
|---|---|---|
| `DEBUG` | 10 | Room generation decisions, movement/collision, inventory ops, AI behaviour |
| `INFO` | 20 | Game start/stop, room transitions, save/load, major state changes |
| `WARN` | 30 | Slow ticks, missing assets with fallback, recoverable save issues |
| `ERROR` | 40 | File I/O failures, deserialization errors, background thread exceptions |
| `CRITICAL` | 50 | Missing asset dirs, pygame init failure, unrecoverable corruption |

## Usage

```python
from gameLogging.logger import getLogger

logger = getLogger(__name__)

# Structured keyword arguments (preferred)
logger.info("player moved", roomX=x, roomY=y, direction=direction)

# Avoid f-string messages
# logger.info(f"player moved to {x},{y}")  # ❌
```

## Field naming conventions

All structured log fields use **camelCase** matching the existing codebase
conventions:

- `roomX`, `roomY` — room coordinates
- `entityId` — entity UUID
- `tickCount` — current tick number
- `durationMs` — elapsed time in milliseconds
- `path` — file path for save/load operations

## Redaction

The `redact()` helper replaces sensitive tokens, passwords, API keys, and
private keys with `[REDACTED]`:

```python
from gameLogging.logger import redact

logger.info("config loaded", filePath=redact(somePath))
```

Use `redact()` before logging any user-identifiable data or credentials.

## DI integration

The `LoggerFactory` singleton is registered in the DI container via
`bootstrap.py`. Classes that need a logger can resolve it through the
container, or simply import `getLogger` directly:

```python
from gameLogging.logger import getLogger
```
