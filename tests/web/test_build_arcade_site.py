"""web/build_arcade_site.py: the static site arcade serves holds what the page loads."""

import os
import re

import pytest

import build_arcade_site

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _fake_repo(root):
    for src, _ in build_arcade_site.FILES:
        path = root / src
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(src)
    (root / "web" / "serve.py").write_text("server")
    (root / "web" / "pyodide_main.py").write_text("python")
    sprite = root / "assets" / "images" / "grass.png"
    sprite.parent.mkdir(parents=True)
    sprite.write_bytes(b"\x89PNG")
    (root / "assets" / "images" / "__pycache__").mkdir()
    (root / "assets" / "images" / "__pycache__" / "x.pyc").write_bytes(b"")
    return root


def _tree(out):
    return sorted(
        os.path.relpath(os.path.join(d, f), out).replace(os.sep, "/")
        for d, _, files in os.walk(out)
        for f in files
    )


def test_site_is_laid_out_as_serve_py_serves_the_repository(tmp_path):
    root = _fake_repo(tmp_path / "repo")
    out = tmp_path / "site"
    build_arcade_site.assemble(str(root), str(out))
    assert _tree(out) == [
        "assets/images/grass.png",
        "index.html",
        "web/game-worker.js",
        "web/game.zip",
        "web/game_version.txt",
        "web/saves.js",
    ]
    assert (out / "index.html").read_text() == "web/index.html"


def test_refuses_an_existing_output_directory(tmp_path):
    root = _fake_repo(tmp_path / "repo")
    out = tmp_path / "site"
    out.mkdir()
    with pytest.raises(SystemExit):
        build_arcade_site.assemble(str(root), str(out))


def test_refuses_when_the_zip_was_not_built(tmp_path):
    root = _fake_repo(tmp_path / "repo")
    (root / "web" / "game.zip").unlink()
    with pytest.raises(SystemExit):
        build_arcade_site.assemble(str(root), str(tmp_path / "site"))


@pytest.mark.parametrize("page", ["web/index.html", "web/game-worker.js"])
def test_every_web_url_the_page_loads_is_in_the_site(page):
    # The page and Worker fetch root-relative /web/... URLs; a new one that the
    # site does not carry would 404 on arcade while still working via serve.py.
    text = open(os.path.join(REPO, page)).read()
    shipped = {dst for _, dst in build_arcade_site.FILES}
    for url in re.findall(r"['\"]/(web/[A-Za-z0-9_.-]+)", text):
        assert url in shipped, url
