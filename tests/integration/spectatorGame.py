"""Run a real text-mode game in a fresh world and keep it running, for the
spectator browser smoke test (tests/integration/test_spectator_smoke.js).

The REST API must be enabled first (CI sets ``restEnabled: true`` in its
workspace copy of config.yml). Prints READY once the world is ticking, keeps
the game's terminal output drained so it never blocks, and on SIGTERM/SIGINT
quits the game and removes the throwaway save (TextPlaythrough's cleanup).

    python3 tests/integration/spectatorGame.py [--boot-timeout SECONDS]
"""

import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textPlaythrough import TextPlaythrough  # noqa: E402

_stopping = []


def _stop(signum, frame):
    _stopping.append(signum)


def main(argv):
    bootTimeout = None
    if "--boot-timeout" in argv:
        bootTimeout = float(argv[argv.index("--boot-timeout") + 1])
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    with TextPlaythrough(saveName="_spectator_smoke", bootTimeout=bootTimeout) as play:
        play.expect("Roam")
        play.send("\r")
        play.expect("Select Save")
        play.send("c")
        play.expect("Enter save name")
        play.send(play.getSaveName() + "\r")
        play.expect("Tick", timeout=30)
        sys.stdout.write("READY\n")
        sys.stdout.flush()
        while not _stopping:
            play.drain(0.5)
            play.resetBuffer()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
