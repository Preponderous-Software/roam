"""Guard rails for the browser Saves panel (web/saves.js + web/index.html).

The behaviour itself is exercised end to end in a real browser by
tests/integration/test_save_export_import.js; these checks pin the few
properties that keep an import from ever losing a save, so a later edit that
breaks one fails here first.
"""

import os
import re

WEB = os.path.join(os.path.dirname(__file__), "..", "..", "web")


def _read(name):
    with open(os.path.join(WEB, name), encoding="utf-8") as f:
        return f.read()


def test_the_page_loads_the_panel_before_its_own_script():
    page = _read("index.html")
    assert page.index('<script src="/web/saves.js"></script>') < page.index(
        '"use strict";'
    )


def test_page_writes_nothing_to_indexeddb_once_stopped_for_an_import():
    page = _read("index.html")
    body = page[page.index("function _idbWrite(files, removed) {") :]
    body = body[: body.index("\n  }\n")]
    # Checked on entry and again when the transaction would be created.
    assert body.count("if (_savesStopped)") == 2
    assert re.search(r"function stopForSaves\(\) \{\s*_savesStopped = true;", page)
    assert "worker.terminate()" in page


def test_import_never_overwrites_clears_or_deletes_a_save():
    panel = _read("saves.js")
    # The only writes to the game's store are add(), which fails rather than
    # overwrite; put() and delete() appear only for the backups store.
    assert "store.add(value, path)" in panel
    for line in panel.splitlines():
        code = line.split("//")[0]
        if re.search(r"\.(put|delete)\(", code):
            assert "BACKUP_STORE" in code, line
        assert ".clear(" not in code, line


def test_a_backup_is_written_before_the_import():
    panel = _read("saves.js")
    body = panel[panel.index("async function applyImport(") :]
    assert body.index("writeBackup(") < body.index("addToStore(")
    assert body.index("stopGame()") < body.index("readStore()")
