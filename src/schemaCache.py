# @author Claude
# Loads and caches JSON validation schemas. Schema files are read-only at
# runtime, so each is parsed from disk only once and the cached dict is reused
# across every save() / load() instead of being re-opened and re-parsed.
import functools
import json


@functools.lru_cache(maxsize=None)
def loadSchema(filename):
    """Return the parsed JSON schema for ``filename`` (e.g. ``"stats.json"``)
    from the ``schemas/`` directory, reading and parsing it only once.

    The path is relative to the working directory established at startup by
    ``appPaths.prepareWorkingDirectory`` (the repo root, or the bundle dir when
    frozen), matching how every schema was loaded before this cache existed.
    """
    with open("schemas/" + filename) as f:
        return json.load(f)
