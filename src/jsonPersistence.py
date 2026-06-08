# @author Claude
# Shared helpers for crash-tolerant JSON persistence. A single-player game's
# entire progress lives in its save files, so a truncated or corrupt file must
# degrade to "no save" rather than crashing the game on every launch.
import json

from gameLogging.logger import getLogger

_logger = getLogger(__name__)


def readJsonFile(path, default=None):
    """Read and parse JSON from ``path``.

    Returns the parsed object on success. On a missing file, or a corrupt /
    truncated file that cannot be parsed, logs the path and returns ``default``
    instead of raising — so a damaged save is treated as absent and the caller
    can fall back to its defaults rather than propagating the error to startup.
    """
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        _logger.error(
            "could not read save file; treating it as absent",
            path=path,
            error=str(e),
        )
        return default
