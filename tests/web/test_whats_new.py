"""The browser build's What's new panel (web/whats_new.py, web/whats-new.js).

Its entries come from CHANGELOG.md's "## What's new" section; the panel only
reads them and shows them. The guards at the end pin that it can never reach
the saves: no browser database, no Worker, no stopping the game.
"""

import json
import os
import re

import whats_new

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
WEB = os.path.join(REPO, "web")


def _read(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8") as f:
        return f.read()


SAMPLE = """# Changelog

Intro.

## What's new

Some prose that is not an entry.

- **2026-10-03 — Saves panel:** the new **Saves** button downloads `every` world.
- **2026-10-02 - Hyphen dash:** a plain hyphen works too.
- not an entry
- **2026-13 — Bad date:** skipped.

## Commit History Summary

- **2026-01-01 — Elsewhere:** not in the section.
"""


def test_parse_reads_only_the_whats_new_section():
    assert whats_new.parse(SAMPLE) == [
        {
            "date": "2026-10-03",
            "title": "Saves panel",
            "text": "The new Saves button downloads every world.",
        },
        {
            "date": "2026-10-02",
            "title": "Hyphen dash",
            "text": "A plain hyphen works too.",
        },
    ]


def test_parse_without_the_section_is_empty():
    assert whats_new.parse("# Changelog\n\n## Commit History Summary\n") == []


def test_parse_keeps_at_most_max_entries():
    lines = "\n".join(
        f"- **2026-01-{day:02d} — Entry {day}:** text." for day in range(1, 30)
    )
    entries = whats_new.parse("## What's new\n\n" + lines + "\n")
    assert len(entries) == whats_new.MAX_ENTRIES
    assert entries[0]["title"] == "Entry 1"


def test_build_writes_the_json_the_panel_reads(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "whats-new.json"
    entries = whats_new.build(str(changelog), str(out))
    assert json.loads(out.read_text(encoding="utf-8")) == {"entries": entries}
    assert len(entries) == 2


def test_the_real_changelog_has_entries_newest_first():
    entries = whats_new.parse(_read("CHANGELOG.md"))
    assert len(entries) >= 4
    dates = [entry["date"] for entry in entries]
    assert dates == sorted(dates, reverse=True)
    titles = " ".join(entry["title"].lower() for entry in entries)
    for topic in ("saves", "achievements", "touch"):
        assert topic in titles, topic


def test_build_zip_writes_whats_new_json():
    assert "whats_new.py" in _read("web", "build_zip.py")
    assert "web/whats-new.json" in _read(".gitignore")


def test_page_loads_the_panel_and_wires_both_buttons():
    page = _read("web", "index.html")
    assert '<script src="/web/whats-new.js"></script>' in page
    assert page.index('<script src="/web/whats-new.js"></script>') < page.index(
        '"use strict";'
    )
    assert 'id="whats-new-touch"' in page and 'id="whats-new-desktop"' in page
    assert "window.RoamWhatsNew.attach({ button: whatsNewButton })" in page
    # The touch button sits in the d-pad's top-right corner, right after the up arrow.
    assert re.search(
        r'data-key="up">▲</button>\s*<button[^>]*id="whats-new-touch"', page
    )


def test_the_panel_never_touches_the_saves():
    panel = _read("web", "whats-new.js")
    code = "\n".join(line.split("//")[0] for line in panel.splitlines())
    for forbidden in (
        "indexedDB",
        "IDB",
        "idb",
        "roam-saves",
        "postMessage",
        "Worker",
        "worker",
        "_savesStopped",
        "BroadcastChannel",
        "sessionStorage",
        "caches.",
        "location.reload",
    ):
        assert forbidden not in code, forbidden
    # localStorage holds only the seen marker, behind try/catch.
    assert code.count("localStorage") == 2
    assert 'SEEN_KEY = "roam.whats-new.seen"' in code


def test_the_page_does_not_hand_the_panel_anything_but_its_button():
    page = _read("web", "index.html")
    start = page.index("// ── what's new")
    block = page[start : page.index("</script>", start)]
    assert "_savesStopped" not in block
    assert "worker" not in block.lower()
    assert "_idb" not in block
