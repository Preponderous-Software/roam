from rendering.inputSource import InputSource


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# A headless InputSource that reports no input (frontend-abstraction epic #433,
# Phase 5). The input counterpart to NullRenderer: it lets game/screen logic run
# its event loop against the InputSource interface with no pygame and no real
# devices. pollEvents yields nothing and the pointer is quiescent, so a screen
# driven by it simply renders frames until its own logic requests a transition.
# A scripted sequence of event frames may be supplied for tests that need to
# feed input deterministically.
class NullInputSource(InputSource):
    def __init__(self, eventFrames=None):
        # eventFrames: optional list of InputEvent lists, returned one per
        # pollEvents() call; once exhausted, pollEvents() returns [] forever.
        self._eventFrames = list(eventFrames) if eventFrames is not None else []

    def pollEvents(self):
        if self._eventFrames:
            return self._eventFrames.pop(0)
        return []

    def isPressed(self, keyCode):
        return False

    def getMousePosition(self):
        return (0, 0)

    def getMouseButtons(self):
        return (False, False, False)
