from rendering.clock import Clock


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Headless Clock that never blocks (epic #433 / #463). The frame-pacing
# counterpart to NullRenderer/NullInputSource: a screen loop driven by it runs
# as fast as it can, which is what a test or headless frontend wants.
class NullClock(Clock):
    def tick(self, fps):
        return 0
