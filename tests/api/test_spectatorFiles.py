import os
import threading
import urllib.error
import urllib.request
from unittest.mock import MagicMock

import pytest

from api.restApiServer import RestApiServer
from api.spectatorFiles import resolveStaticFile
from appPaths import getBundleDirectory
from player.player import Player
from world.tickCounter import TickCounter


def test_spectator_page_resolves_with_and_without_index():
    for parts in (["spectator"], ["spectator", "index.html"]):
        path, contentType = resolveStaticFile(parts)

        assert path == os.path.join(getBundleDirectory(), "spectator", "index.html")
        assert contentType.startswith("text/html")
        assert os.path.isfile(path)


def test_sprite_resolves_from_the_game_assets():
    path, contentType = resolveStaticFile(["assets", "images", "grass.png"])

    assert path == os.path.join(getBundleDirectory(), "assets", "images", "grass.png")
    assert contentType == "image/png"


@pytest.mark.parametrize(
    "parts",
    [
        ["assets", "images", "missing.png"],
        ["assets", "images", "..", "config.yml"],
        ["assets", "images", "..png"],
        ["assets", "images", "grass.PNG.bak"],
        ["assets", "grass.png"],
        ["config.yml"],
        ["saves"],
        ["spectator", "other.html"],
        ["schemas", "room.json"],
    ],
)
def test_nothing_else_is_served(parts):
    assert resolveStaticFile(parts) is None


def test_spectator_page_is_read_only_and_same_origin():
    path, _ = resolveStaticFile(["spectator"])
    with open(path, encoding="utf-8") as page:
        html = page.read()

    # It reads the snapshot from its own origin and pins three.js exactly.
    assert '"/api/v1/snapshot"' in html
    assert "three@0.147.0/build/three.min.js" in html
    # Only GETs: no request body or non-GET method anywhere in the page.
    for verb in ("POST", "PUT", "DELETE", "PATCH"):
        assert verb not in html


def test_static_files_over_http(resolve, override_dependency, test_config):
    test_config.restEnabled = True
    test_config.restPort = 0
    override_dependency(Player, MagicMock())
    override_dependency(TickCounter, MagicMock())
    server = resolve(RestApiServer)
    fakeMap = MagicMock()
    fakeMap._lock = threading.Lock()
    server.setMap(fakeMap)
    server.start()
    try:
        base = "http://127.0.0.1:" + str(server._httpServer.server_address[1])
        with urllib.request.urlopen(base + "/spectator/") as response:
            pageType = response.headers["Content-Type"]
            page = response.read()
        with urllib.request.urlopen(base + "/assets/images/torch.png") as response:
            imageType = response.headers["Content-Type"]
            image = response.read()
        with pytest.raises(urllib.error.HTTPError) as missing:
            urllib.request.urlopen(base + "/assets/images/nope.png")
    finally:
        server.shutdown()

    assert pageType.startswith("text/html")
    assert b"Roam 3D" in page
    assert imageType == "image/png"
    assert image.startswith(b"\x89PNG")
    assert missing.value.code == 404
