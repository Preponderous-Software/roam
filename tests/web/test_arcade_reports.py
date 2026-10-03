"""The page side of Roam's arcade achievements (web/index.html + the vendored
web/arcade-scores.js): the Worker's reports reach arcade-social's client, and
nothing about them can stop the game."""

import hashlib
import json
import os
import shutil
import subprocess

import pytest

WEB = os.path.join(os.path.dirname(__file__), "..", "..", "web")

# arcade-social clients/js/arcade-scores.js at a8ff7e6 (0.1.0), vendored as is.
# Refresh it by copying the file again and updating this hash.
ARCADE_SCORES_SHA256 = (
    "4652a5c964ccc3e945fc596c8a901143351f3fae6696bd24641b68c33f765b55"
)


def _read(name):
    with open(os.path.join(WEB, name), encoding="utf-8") as f:
        return f.read()


def test_the_client_is_vendored_unchanged():
    with open(os.path.join(WEB, "arcade-scores.js"), "rb") as f:
        # A Windows checkout may turn LF into CRLF; the pin is of the LF file.
        content = f.read().replace(b"\r\n", b"\n")
    assert hashlib.sha256(content).hexdigest() == ARCADE_SCORES_SHA256


def test_the_page_loads_the_client_before_its_own_script():
    page = _read("index.html")
    assert page.index('<script src="/web/arcade-scores.js"></script>') < page.index(
        '"use strict";'
    )


def test_the_worker_messages_reach_the_reporter():
    page = _read("index.html")
    assert "if (d.type === 'arcade') { reportToArcade(d); return; }" in page


def test_the_browser_build_installs_the_bridge():
    main = _read("pyodide_main.py")
    install = main.index("arcadeBridge.install(")
    # Installed before the game (and its first world load) starts.
    assert install < main.index("roam = Roam(")


def _reporterSource():
    page = _read("index.html")
    start = page.index("  // Unlocks that arrive together")
    end = page.index("  // ── key sequences")
    return page[start:end]


SCRIPT = r"""
const vm = require("vm");
const calls = [];
const toast = { textContent: "", classes: new Set(), parts: [],
  classList: { add(c) { toast.classes.add(c); }, remove(c) { toast.classes.delete(c); } },
  append(...xs) { toast.parts.push(...xs.map(x => typeof x === "string" ? x : x.textContent)); } };
const scenario = process.argv[2];
const client = {
  unlock(id) { calls.push(["unlock", id]);
    if (scenario === "throws") throw new Error("boom");
    return Promise.resolve(scenario === "repeat" ? { newlyUnlocked: false } : { newlyUnlocked: true }); },
  submitScore(board, value) { calls.push(["score", board, value]); return Promise.resolve(null); },
};
const sandbox = {
  window: scenario === "absent" ? {} : { ArcadeScores: client },
  document: { getElementById: () => toast, createElement: () => ({}) },
  console: { warn() {} }, setTimeout: (fn) => { timers.push(fn); return timers.length; }, clearTimeout() {}, Promise,
};
const timers = [];
vm.createContext(sandbox);
vm.runInContext(process.argv[1] + `
reportToArcade({ type: "arcade", kind: "unlock", achievement: "hearth", title: "Hearth" });
reportToArcade({ type: "arcade", kind: "score", board: "most-days", value: 3 });
reportToArcade({ type: "arcade", kind: "nonsense" });
` + (scenario === "two" ? `reportToArcade({ type: "arcade", kind: "unlock", achievement: "wanderer", title: "Wanderer" });` : ""), sandbox);
setTimeout(() => {}, 0);
Promise.resolve().then(() => Promise.resolve()).then(() => {
  const shownFirst = toast.parts.join("");
  if (scenario === "two") { for (let i = 0; i < timers.length && i < 20; i++) timers[i](); }
  console.log(JSON.stringify({ calls, toast: shownFirst, all: toast.parts.join("|"),
    shown: scenario === "two" ? null : toast.classes.has("shown") }));
});
"""


def _run(scenario):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    out = subprocess.run(
        [node, "-e", SCRIPT, _reporterSource(), scenario],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    ).stdout
    return json.loads(out)


def test_reports_go_to_the_client_and_a_new_unlock_shows_a_toast():
    result = _run("ok")
    assert result["calls"] == [["unlock", "hearth"], ["score", "most-days", 3]]
    assert result["shown"]
    assert result["toast"] == "Achievement unlocked: Hearth"


def test_unlocks_that_arrive_together_are_shown_in_turn():
    result = _run("two")
    assert result["toast"] == "Achievement unlocked: Hearth"
    assert result["all"] == (
        "Achievement unlocked: |Hearth|Achievement unlocked: |Wanderer"
    )


def test_an_unlock_the_player_already_had_shows_nothing():
    result = _run("repeat")
    assert result["calls"][0] == ["unlock", "hearth"]
    assert not result["shown"]


def test_a_missing_client_is_a_no_op():
    assert _run("absent")["calls"] == []


def test_a_throwing_client_never_escapes_the_reporter():
    result = _run("throws")
    # The unlock threw; the score after it was still sent.
    assert result["calls"] == [["unlock", "hearth"], ["score", "most-days", 3]]
    assert not result["shown"]
