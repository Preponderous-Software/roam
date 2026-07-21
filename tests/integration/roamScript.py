import os
import re
import shlex
import sys

from textPlaythrough import REPO_ROOT, TextPlaythrough

# @author Claude
# @since July 20th, 2026
#
# A tiny line-oriented DSL for scripting `TextPlaythrough` runs, so a
# functionality-verification pass can be written as a plain-text `.roamscript`
# file instead of a bespoke Python driver per scenario. Each non-blank,
# non-comment line is one command:
#
#     expect TEXT [timeout=N]             wait for TEXT to appear on screen
#     send KEYS...                        type keys (named: enter, esc, tab,
#                                          backspace, space, up/down/left/right,
#                                          ctrl+c; any other token is sent as
#                                          its literal characters)
#     assertContains TEXT [timeout=N]     TEXT must already be on screen
#     assertNotContains TEXT [timeout=N]  TEXT must NOT appear within timeout
#     assertPathExists PATH               a repo-relative path must exist
#     wait SECONDS                        pace the script; asserts nothing
#
# `{saveName}` in any argument is replaced with the run's generated save
# name. Quote an argument (`"like this"`) to keep spaces together as one
# TEXT/PATH; unquoted words are joined with a single space. Lines starting
# with `#` and blank lines are ignored.
#
# A script never needs to ask for a clean-exit check: runScript() always
# verifies the child exited without a traceback after the last line, mirroring
# the `assert game.cleanExit()` convention in test_text_playthrough.py.
#
# See docs/roamscript.md for the full grammar and worked examples.

_TIMEOUT_TOKEN = re.compile(r"^timeout=(\d+(?:\.\d+)?)$")

_KEY_MAP = {
    "enter": "\r",
    "return": "\r",
    "esc": "\x1b",
    "escape": "\x1b",
    "tab": "\t",
    "backspace": "\x7f",
    "space": " ",
    "up": "\x1b[A",
    "down": "\x1b[B",
    "right": "\x1b[C",
    "left": "\x1b[D",
    "ctrl+c": "\x03",
}


class RoamScriptError(Exception):
    """A script step failed to parse or run. The message is prefixed with
    `path:line: command:` so a failing script names exactly the line that
    broke, the way a traceback would for hand-written Python."""


class Step:
    __slots__ = ("lineNumber", "command", "rest")

    def __init__(self, lineNumber, command, rest):
        self.lineNumber = lineNumber
        self.command = command
        self.rest = rest


def parseScript(text):
    """Parse `.roamscript` source into a list of Step objects. Raises
    RoamScriptError on an unrecognized command so a typo fails fast, before
    the game process is even launched."""
    steps = []
    for lineNumber, rawLine in enumerate(text.splitlines(), start=1):
        line = rawLine.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        command = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        if command not in _HANDLERS:
            raise RoamScriptError(
                "line %d: unknown command %r (expected one of: %s)"
                % (lineNumber, command, ", ".join(sorted(_HANDLERS)))
            )
        steps.append(Step(lineNumber, command, rest))
    return steps


def loadScript(path):
    with open(path, "r", encoding="utf-8") as f:
        return parseScript(f.read())


def _substitute(text, game):
    return text.replace("{saveName}", game.getSaveName())


def _splitTimeout(tokens, default):
    if tokens and _TIMEOUT_TOKEN.match(tokens[-1]):
        return tokens[:-1], float(_TIMEOUT_TOKEN.match(tokens[-1]).group(1))
    return tokens, default


def _handleExpect(game, rest):
    tokens = shlex.split(_substitute(rest, game))
    tokens, timeout = _splitTimeout(tokens, None)
    game.expect(" ".join(tokens), timeout=timeout)


def _handleSend(game, rest):
    tokens = shlex.split(_substitute(rest, game))
    game.send("".join(_KEY_MAP.get(token.lower(), token) for token in tokens))


def _handleAssertContains(game, rest):
    tokens = shlex.split(_substitute(rest, game))
    tokens, timeout = _splitTimeout(tokens, 1.0)
    game.expect(" ".join(tokens), timeout=timeout)


def _handleAssertNotContains(game, rest):
    tokens = shlex.split(_substitute(rest, game))
    tokens, timeout = _splitTimeout(tokens, 0.5)
    text = " ".join(tokens)
    buffer = game.drain(timeout)
    if text in buffer:
        raise AssertionError(
            "found %r but expected it absent; last output:\n%s" % (text, game.tail())
        )


def _handleAssertPathExists(game, rest):
    tokens = shlex.split(_substitute(rest, game))
    if len(tokens) != 1:
        raise RoamScriptError("assertPathExists takes exactly one path argument")
    fullPath = os.path.join(REPO_ROOT, tokens[0])
    if not os.path.exists(fullPath):
        raise AssertionError("path does not exist: %s" % fullPath)


def _handleWait(game, rest):
    tokens = shlex.split(rest)
    if len(tokens) != 1:
        raise RoamScriptError("wait takes exactly one number of seconds")
    game.drain(float(tokens[0]))


_HANDLERS = {
    "expect": _handleExpect,
    "send": _handleSend,
    "assertContains": _handleAssertContains,
    "assertNotContains": _handleAssertNotContains,
    "assertPathExists": _handleAssertPathExists,
    "wait": _handleWait,
}


def runScript(path, saveName=None, bootTimeout=None, verbose=False):
    """Run a `.roamscript` file end to end against a fresh TextPlaythrough.
    Raises RoamScriptError on a bad or failing step (including a non-clean
    exit after the last line). Returns the TextPlaythrough for callers that
    want to inspect it further (e.g. game.tail()).

    `bootTimeout` overrides the default wait for the *first* `expect` (an
    individual step's own `timeout=N` always wins) — useful on machines
    slower to import/boot the game than the CI runner this default is
    tuned for."""
    steps = loadScript(path)
    playthroughKwargs = {} if bootTimeout is None else {"bootTimeout": bootTimeout}
    with TextPlaythrough(saveName=saveName, **playthroughKwargs) as game:
        for step in steps:
            if verbose:
                print("  %-18s %s" % (step.command, step.rest))
            try:
                _HANDLERS[step.command](game, step.rest)
            except (AssertionError, RoamScriptError) as e:
                raise RoamScriptError(
                    "%s:%d: %s: %s" % (path, step.lineNumber, step.command, e)
                ) from e
    if not game.cleanExit():
        raise RoamScriptError(
            "%s: game did not exit cleanly:\n%s" % (path, game.getStderr())
        )
    return game


def main(argv):
    import argparse

    parser = argparse.ArgumentParser(description="Run a .roamscript file.")
    parser.add_argument("script", help="path to a .roamscript file")
    parser.add_argument(
        "--boot-timeout",
        type=float,
        default=None,
        help="override the default wait for the first `expect` "
        "(e.g. on a machine slower to boot the game than CI)",
    )
    args = parser.parse_args(argv[1:])
    print(args.script)
    try:
        runScript(args.script, bootTimeout=args.boot_timeout, verbose=True)
    except RoamScriptError as e:
        print("FAIL: %s" % e)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
