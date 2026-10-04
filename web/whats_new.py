#!/usr/bin/env python3
"""Build web/whats-new.json from the "What's new" section of CHANGELOG.md.

The browser build shows a small **What's new** panel (web/whats-new.js). Its
entries are not written twice: they are the bullets of CHANGELOG.md's
``## What's new`` section, one per line, in the form

    - **2026-10-03 — Saves panel:** what changed, in plain words.

and ``web/build_zip.py`` writes them to ``web/whats-new.json`` (a generated
file, like game.zip) as ``{"entries": [{"date", "title", "text"}, ...]}``.
A bullet that does not match the form is skipped, so a typo can only drop
an entry, never break the build.

Usage (from the repository root):
    python3 web/whats_new.py [CHANGELOG] [OUT]
"""

import json
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SECTION = "## What's new"
MAX_ENTRIES = 12
_BULLET = re.compile(
    r"^- \*\*(?P<date>\d{4}-\d{2}-\d{2})\s*[—–-]\s*(?P<title>[^*]+?):\*\*\s+(?P<text>\S.*)$"
)
_MARKUP = re.compile(r"\*\*|`")


def _plain(text):
    return _MARKUP.sub("", text).strip()


def _capitalized(text):
    return text[:1].upper() + text[1:]


def parse(markdown):
    """The entries of the ``## What's new`` section, in file order."""
    entries = []
    inside = False
    for line in markdown.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line.strip() == SECTION
            continue
        if not inside:
            continue
        match = _BULLET.match(line.strip())
        if match:
            entries.append(
                {
                    "date": match.group("date"),
                    "title": _plain(match.group("title")),
                    "text": _capitalized(_plain(match.group("text"))),
                }
            )
    return entries[:MAX_ENTRIES]


def build(changelog=None, out=None):
    """Write the JSON file and return its entries."""
    changelog = changelog or os.path.join(ROOT, "CHANGELOG.md")
    out = out or os.path.join(ROOT, "web", "whats-new.json")
    with open(changelog, encoding="utf-8") as f:
        entries = parse(f.read())
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return entries


if __name__ == "__main__":
    args = sys.argv[1:]
    found = build(*(args + [None, None])[:2])
    print(f"Wrote {len(found)} What's new entries")
