import time

from rendering.clock import Clock


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Frame pacing for the text frontend (epic #433 / #239): a plain time-based
# limiter so the terminal loop runs at most `fps` times per second.
class TextClock(Clock):
    def __init__(self):
        self._lastTick = time.monotonic()

    def tick(self, fps):
        if fps <= 0:
            self._lastTick = time.monotonic()
            return 0
        targetSeconds = 1.0 / fps
        elapsed = time.monotonic() - self._lastTick
        if elapsed < targetSeconds:
            time.sleep(targetSeconds - elapsed)
        now = time.monotonic()
        result = now - self._lastTick
        self._lastTick = now
        return int(result * 1000)
