"""Guard rails against the save wipe tak#18 fixed (web/game-worker.js and
web/index.html).

A sync must never wipe a stored world. tests/integration/test_failed_restore.js
proves it end to end in a browser; these checks pin the properties it relies
on so an edit that breaks one fails here first.
"""

import os
import re

WEB = os.path.join(os.path.dirname(__file__), "..", "..", "web")


def _read(name):
    with open(os.path.join(WEB, name), encoding="utf-8") as f:
        return f.read()


def _function(source, header):
    body = source[source.index(header) :]
    return body[
        : body.index("\n  }\n") if header.startswith("  ") else body.index("\n}\n")
    ]


def test_a_failed_or_partial_restore_never_syncs():
    worker = _read("game-worker.js")
    restore = _function(worker, "async function loadSavesFromIDB(pyodide) {")
    # Every way out of the restore reports success or failure.
    assert restore.count("return false;") == 2  # a file not written back; a read error
    assert restore.count("return true;") == 1
    assert "const restored = await loadSavesFromIDB(pyodide);" in worker
    assert re.search(
        r"if \(restored\) \{\s*// [^\n]*\n\s*globalThis\.syncSaves = makeSyncSaves\(",
        worker,
    )
    # syncSaves is installed in exactly one place, the restored branch.
    assert worker.count("globalThis.syncSaves =") == 1
    assert "type: 'nosave'" in worker


def test_the_page_shows_the_notice():
    page = _read("index.html")
    assert "if (d.type === 'nosave') { showSavesNotice(d.msg); return; }" in page
    assert 'notice.setAttribute("role", "alert");' in page


def test_a_sync_never_clears_the_store():
    page = _read("index.html")
    write = _function(page, "  function _idbWrite(files, removed) {")
    assert ".clear()" not in write
    assert "store.put(content, path)" in write
    # A stored file is deleted only when its world is one the sync carries or
    # one the game said it removed.
    assert "worlds.has(world)" in write
    assert write.count("store.delete(") == 1
    assert "_idbWrite(d.files, d.removed)" in page


def test_only_the_game_can_name_a_removed_world():
    worker = _read("game-worker.js")
    assert "globalThis.noteSavedWorldRemoved = (name) =>" in worker
    assert "removed: [...removedWorlds]" in worker
