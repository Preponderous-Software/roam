# @author Claude
# Shared helpers for crash-tolerant JSON persistence. A single-player game's
# entire progress lives in its save files, so a truncated or corrupt file must
# degrade to "no save" rather than crashing the game on every launch, and a
# save interrupted mid-write must never destroy the previous good file.
import json
import os
import tempfile

from gameLogging.logger import getLogger

_logger = getLogger(__name__)


def writeJsonAtomically(path, data, indent=4):
    """Serialize ``data`` to ``path`` atomically.

    Writes to a temporary file in the same directory, flushes and fsyncs it,
    then ``os.replace()``s it over the target — an atomic operation on a single
    filesystem. If the process is killed, the disk fills, or serialization
    raises mid-write, the previous good file is left intact and the temporary
    file is discarded, instead of the old behaviour of truncating the target
    with ``open(path, "w")`` before dumping into it.
    """
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tempPath = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tempPath, path)
    except BaseException:
        # A failed save must not leave a stray temp file behind.
        try:
            os.remove(tempPath)
        except OSError:
            pass
        raise


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
