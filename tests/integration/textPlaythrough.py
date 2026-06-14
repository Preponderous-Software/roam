import os
import re
import select
import signal
import subprocess
import sys
import time

# Repo root: tests/integration/ -> tests/ -> <repo>. The game loads assets and
# resolves the saves directory relative to this, so the child runs here.
REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)

_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


# @author Claude
# @since June 14th, 2026
#
# A reusable end-to-end driver for the text/terminal frontend (epic #433 / the
# text-UI payoff #239). It launches `roam.py --text` under a pseudo-terminal so
# the game sees a real interactive TTY (cbreak mode, arrow escape sequences,
# Enter as CR), then lets a test send keystrokes and wait for expected screen
# text to appear. This exercises the whole stack a unit test cannot: the real
# process, the InputSource decoding, the Renderer/Clock loop, and clean
# shutdown. Bugs first found this way include the world-entry geometry.Rect
# crash, cbreak Enter translation, and the "c opens naming and types itself"
# batch. POSIX only (it needs pty); skip elsewhere.
#
# Use as a context manager so the child is always reaped and the terminal
# released:
#     with TextPlaythrough() as game:
#         game.expect("Roam")          # main menu painted
#         game.send("\r")              # Enter -> save selection
#         ...
#     assert game.cleanExit()          # no traceback on the child's stderr
class TextPlaythrough:
    def __init__(self, saveName=None, bootTimeout=10.0):
        # A unique, self-cleaning save name keeps runs from colliding and from
        # leaving state in the repo's saves/ directory.
        self._saveName = saveName or ("_pytest_play_%d" % os.getpid())
        self._bootTimeout = bootTimeout
        self._proc = None
        self._master = None
        self._buffer = ""  # ANSI-stripped output seen so far
        self._stderr = ""

    # --- lifecycle ---

    def __enter__(self):
        import pty

        master, slave = pty.openpty()
        env = dict(os.environ)
        env["SDL_VIDEODRIVER"] = "dummy"
        env["SDL_AUDIODRIVER"] = "dummy"
        self._proc = subprocess.Popen(
            [sys.executable, "src/roam.py", "--text"],
            stdin=slave,
            stdout=slave,
            stderr=subprocess.PIPE,
            cwd=REPO_ROOT,
            env=env,
            close_fds=True,
        )
        os.close(slave)
        self._master = master
        return self

    def __exit__(self, excType, excValue, traceback):
        # Ask the game to quit the way a Ctrl+C user would, then reap it.
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.send_signal(signal.SIGINT)
                self._proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                self._proc.kill()
        if self._proc is not None and self._proc.stderr is not None:
            self._stderr = self._proc.stderr.read().decode("utf-8", "ignore")
        if self._master is not None:
            try:
                os.close(self._master)
            except OSError:
                pass
        self._cleanupSave()
        return False

    def _cleanupSave(self):
        import shutil

        savePath = os.path.join(REPO_ROOT, "saves", self._saveName)
        shutil.rmtree(savePath, ignore_errors=True)

    # --- driving ---

    def getSaveName(self):
        return self._saveName

    def send(self, keys):
        os.write(self._master, keys.encode())

    def _pump(self, timeout):
        # Drain whatever the child has emitted within the window into the
        # rolling buffer; tolerate the fd closing as the child exits.
        deadline = time.time() + timeout
        while time.time() < deadline:
            ready, _, _ = select.select([self._master], [], [], 0.1)
            if not ready:
                continue
            try:
                chunk = os.read(self._master, 65536)
            except OSError:
                break
            if not chunk:
                break
            self._buffer += _ANSI.sub("", chunk.decode("utf-8", "ignore"))

    def expect(self, text, timeout=None):
        """Wait until `text` appears in the (ANSI-stripped) output. Returns the
        accumulated buffer on success; raises AssertionError on timeout so a
        failing playthrough names the screen it was waiting for."""
        timeout = self._bootTimeout if timeout is None else timeout
        deadline = time.time() + timeout
        while time.time() < deadline:
            if text in self._buffer:
                return self._buffer
            self._pump(0.2)
        raise AssertionError(
            "timed out after %.1fs waiting for %r; last output:\n%s"
            % (timeout, text, self.tail())
        )

    def drain(self, seconds=0.5):
        self._pump(seconds)
        return self._buffer

    # --- inspection ---

    def tail(self, lines=25):
        kept = [line for line in self._buffer.splitlines() if line.strip()]
        return "\n".join(kept[-lines:])

    def getStderr(self):
        return self._stderr

    def cleanExit(self):
        # The text frontend must shut down without dumping a Python traceback
        # (a crash also leaves the user's terminal stuck in cbreak mode).
        return "Traceback (most recent call last)" not in self._stderr
