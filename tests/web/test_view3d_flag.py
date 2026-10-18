"""The browser build's 3D view (RFC 0017 stage 3) is opt-in: without
?view=3d the page must not load three.js or web/roam3d.js, the Worker must be
started exactly as before, and the Pyodide entry must stay 2D. These static
checks back the browser test in tests/integration/test_view3d_flag.js."""

import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as source:
        return source.read()


def _setupView3dBody(page):
    start = page.index("async function setupView3d()")
    end = page.index("function onWorldView(")
    return page[start:end]


def test_no_static_script_tag_loads_3d_code():
    page = _read("web/index.html")
    for src in re.findall(r"<script[^>]*src=\"([^\"]+)\"", page):
        assert "three" not in src and "roam3d" not in src, src


def test_3d_code_is_loaded_only_inside_the_opt_in_setup():
    page = _read("web/index.html")
    setup = _setupView3dBody(page)
    outside = page.replace(setup, "")
    assert "three@0.147.0/build/three.min.js" in setup
    assert "/web/roam3d.js" in setup
    assert "three.min.js" not in outside
    assert "/web/roam3d.js" not in outside


def test_the_flag_is_the_view_3d_url_parameter_and_gates_the_setup():
    page = _read("web/index.html")
    assert 'new URLSearchParams(location.search).get("view") === "3d"' in page
    assert (
        "if (_view3d.requested) setupView3d().then(startWorker);\n  else startWorker();"
        in page
    )
    # The Worker hears about 3D only when the setup succeeded.
    assert "if (_view3d.enabled) init.view3d = true;" in page


def test_worker_and_pyodide_entry_default_to_2d():
    worker = _read("web/game-worker.js")
    entry = _read("web/pyodide_main.py")
    assert "globalThis.roamView3d  = e.data.view3d === true;" in worker
    assert '_VIEW_3D = bool(getattr(_js, "roamView3d", False))' in entry
    assert "drawsWorldFromView=_VIEW_3D" in entry
    assert "world_view_sink = None\nif _VIEW_3D:" in entry
