import os
import re

from appPaths import getBundleDirectory

# The static files the REST server hands out next to the API (RFC 0017 stage
# 1): the 3D spectator page and the game's own sprites, which the page loads at
# runtime. Same origin as /api/v1/snapshot, so no CORS header is needed.
#
# Only a fixed set of paths is served: the page itself and PNG files directly
# inside assets/images/ whose names are plain identifiers. Nothing else under
# the bundle directory (saves, config) is reachable, and no ".." can get past
# the name pattern.

_SPECTATOR_PAGE = ("spectator", "index.html")
_IMAGE_NAME = re.compile(r"^[A-Za-z0-9_]+\.png$")
_HTML = "text/html; charset=utf-8"
_PNG = "image/png"


def resolveStaticFile(parts):
    """Return (absolutePath, contentType) for a served static path, given the
    URL path's non-empty segments, or None when the path is not one."""
    root = getBundleDirectory()
    if parts in (["spectator"], ["spectator", "index.html"]):
        return os.path.join(root, *_SPECTATOR_PAGE), _HTML
    if (
        len(parts) == 3
        and parts[:2] == ["assets", "images"]
        and _IMAGE_NAME.match(parts[2])
    ):
        path = os.path.join(root, "assets", "images", parts[2])
        if os.path.isfile(path):
            return path, _PNG
    return None
