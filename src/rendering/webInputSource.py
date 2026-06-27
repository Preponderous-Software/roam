import queue
import time

from rendering.textInputSource import TextInputSource


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# WebSocket implementation of InputSource (web-frontend epic). Reuses all of
# TextInputSource's ANSI parsing (arrow keys, control chars, movement key
# de-bounce) — the only difference is the char source: instead of os.read on
# stdin, characters arrive via feed() from the WebSocket handler and are
# buffered in a thread-safe queue.
class WebInputSource(TextInputSource):
    def __init__(self):
        self._inputQueue = queue.Queue()
        super().__init__(charReader=self._readFromQueue)

    def feed(self, data: str):
        """Deliver a burst of raw terminal bytes received from xterm.js."""
        if data:
            self._inputQueue.put(data)

    def _readFromQueue(self):
        try:
            return self._inputQueue.get_nowait()
        except queue.Empty:
            # Pace the idle game loop the same way TextInputSource's select()
            # timeout does — avoids a busy-spin when no input is pending.
            time.sleep(0.02)
            return ""
