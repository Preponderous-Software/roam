# @author Claude, on behalf of Daniel McCoy Stephenson
"""Python side of Roam's bridge to arcade's achievements and leaderboards.

On arcade (https://roam.play.danielstephenson.dev) the browser build installs a
sink here (web/pyodide_main.py) that posts each report to the page, which hands
it to arcade-social's client (web/arcade-scores.js). Everywhere else - the
desktop and text frontends, tests, the browser build served from any other
host - no sink is installed and every call is a no-op.

Reporting is fire-and-forget and can never affect play or saves:

- no call raises, whatever the sink does;
- nothing waits for an answer (the page posts in the background, and only for
  a signed-in player on arcade);
- each achievement is reported at most once per session, and a board only
  when the value beats what this session already reported, so re-checking
  every second costs nothing.
"""

from gameLogging.logger import getLogger

_logger = getLogger(__name__)

_sink = None
_reportedUnlocks = set()
_reportedBests = {}


def install(sink):
    """Send every report to ``sink(message)`` (a dict) from now on."""
    global _sink
    _sink = sink


def isActive():
    """True when reports go somewhere (the browser build on arcade)."""
    return _sink is not None


def reset():
    """Forget the sink and what was reported (for tests)."""
    global _sink
    _sink = None
    _reportedUnlocks.clear()
    _reportedBests.clear()


def unlock(achievementId, title=None):
    """Report an achievement; repeats within the session are dropped."""
    if _sink is None or achievementId in _reportedUnlocks:
        return
    _reportedUnlocks.add(achievementId)
    message = {"kind": "unlock", "achievement": achievementId}
    if title:
        message["title"] = title
    _send(message)


def submitScore(board, value):
    """Report a leaderboard value when it beats this session's last report."""
    if _sink is None:
        return
    try:
        value = int(value)
    except (TypeError, ValueError):
        return
    if value <= _reportedBests.get(board, 0):
        return
    _reportedBests[board] = value
    _send({"kind": "score", "board": board, "value": value})


def _send(message):
    try:
        _sink(message)
    except Exception as e:  # a report must never reach the game loop
        _logger.warning("arcade report dropped", kind=message["kind"], error=str(e))
