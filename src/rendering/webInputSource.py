import queue
import time

from rendering.inputEvent import EventType, InputEvent
from rendering.textInputSource import TextInputSource


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# WebSocket implementation of InputSource (web-frontend epic). Reuses all of
# TextInputSource's ANSI parsing (arrow keys, control chars, movement key
# de-bounce) — the only difference is the char source: instead of os.read on
# stdin, characters arrive via feed() from the WebSocket handler and are
# buffered in a thread-safe queue.
#
# Unlike TextInputSource (which always returns (0,0) / all-False for mouse),
# this class tracks real mouse state so the game's existing click handling
# (gather on left-click, place on right-click, hotbar slot selection) works
# when the browser sends tap/click events as JSON mouse messages.
class WebInputSource(TextInputSource):
    def __init__(self):
        self._inputQueue = queue.Queue()
        self._mousePos = (0, 0)
        self._mouseButtons = [False, False, False]  # left, middle, right
        super().__init__(charReader=self._readFromQueue)

    def feed(self, data: str):
        """Deliver a burst of raw terminal bytes received from xterm.js."""
        if data:
            self._inputQueue.put(data)

    def consumeLeftClick(self):
        """Clear the left-button-down state after a button callback fires.

        Called by WebRenderer.drawButton() to prevent the same tap from
        triggering the callback on every frame until the mouse_up arrives.
        """
        self._mouseButtons[0] = False

    def updateMouse(self, x, y, button, isDown):
        """Update mouse state and queue a MOUSE_DOWN or MOUSE_UP event.

        Called by WebSession when a JSON mouse message arrives from the browser.
        button follows SDL convention: 1=left, 2=middle, 3=right.
        Thread-safe under CPython's GIL via the parent's queueEvent().
        """
        self._mousePos = (x, y)
        idx = button - 1
        if 0 <= idx < 3:
            self._mouseButtons[idx] = isDown
        evtType = EventType.MOUSE_DOWN if isDown else EventType.MOUSE_UP
        self.queueEvent(InputEvent(evtType, position=(x, y), button=button))

    def moveMouse(self, x, y):
        """Update mouse position and queue a MOUSE_MOTION event.

        Sets _mousePos before queuing so getMousePosition() returns the right
        coords when the game loop processes the event (e.g. hudDragManager).
        """
        self._mousePos = (x, y)
        self.queueEvent(InputEvent(EventType.MOUSE_MOTION, position=(x, y)))

    def getMousePosition(self):
        return self._mousePos

    def getMouseButtons(self):
        return tuple(self._mouseButtons)

    def _readFromQueue(self):
        try:
            return self._inputQueue.get_nowait()
        except queue.Empty:
            # Pace the idle game loop the same way TextInputSource's select()
            # timeout does — avoids a busy-spin when no input is pending.
            time.sleep(0.02)
            return ""
