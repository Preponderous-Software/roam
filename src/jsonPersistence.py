# @author Claude
# Shared helpers for crash-tolerant JSON persistence. A single-player game's
# entire progress lives in its save files, so a truncated or corrupt file must
# degrade to "no save" rather than crashing the game on every launch, and a
# save interrupted mid-write must never destroy the previous good file.
import json
import os
import sys
import tempfile

from gameLogging.logger import getLogger

_logger = getLogger(__name__)


def _syncBrowserSavesIfAvailable():
    js = sys.modules.get("js")
    if js is None:
        return
    syncSaves = getattr(js, "syncSaves", None)
    if syncSaves is None:
        return
    try:
        syncSaves()
    except Exception as e:
        _logger.warning("could not sync browser saves", error=str(e))


def writeJsonAtomically(path, data, indent=4):
    """Serialize ``data`` to ``path`` atomically.

    Writes to a temporary file in the same directory, flushes and fsyncs it,
    then ``os.replace()``s it over the target — an atomic operation on a single
    filesystem. If the process is killed, the disk fills, or serialization
    raises mid-write, the previous good file is left intact and the temporary
    file is discarded, instead of the old behaviour of truncating the target
    with ``open(path, "w")`` before dumping into it.

    Falls back to a direct (non-atomic) write when the filesystem does not
    support ``os.replace()`` (e.g. Pyodide's Emscripten OPFS layer), so that
    saves still persist rather than failing silently.
    """
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    # Attempt atomic write via temp-file + rename.
    fd, tempPath = tempfile.mkstemp(dir=directory, suffix=".tmp")
    _renamed = False
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=indent)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass  # some FS backends (OPFS, network) don't support fsync
        try:
            os.replace(tempPath, path)
            _renamed = True
        except OSError:
            pass  # rename unsupported on this FS — fall through to direct write
    except BaseException:
        try:
            os.remove(tempPath)
        except OSError:
            pass
        raise

    if _renamed:
        _syncBrowserSavesIfAvailable()
        return

    # Rename failed (e.g. OPFS in Pyodide): clean up temp file, write directly.
    try:
        os.remove(tempPath)
    except OSError:
        pass
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
    _syncBrowserSavesIfAvailable()


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
