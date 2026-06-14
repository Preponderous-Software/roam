from rendering.inputEvent import EventType
from screen.screenType import ScreenType


# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# Base class for the menu/UI screens that share the standard run loop
# (frontend-abstraction epic #433): poll events, draw a frame, present it,
# until a screen transition is requested. It owns the loop, the common QUIT
# handling, and the present() call so individual screens stop duplicating that
# skeleton. Events come from the backend-neutral InputSource as InputEvents, so
# no screen touches pygame's event queue. Subclasses set self.renderer /
# self.inputSource / self.nextScreen / self.changeScreen (typically in their
# @component constructor) and override:
#   - handleEvent(event): act on a non-QUIT InputEvent
#   - draw(): clear and render one frame through self.renderer
#   - onStart(): optional per-run setup before the loop
#   - onExit(): optional cleanup after the loop
# worldScreen is intentionally not a Screen — it has its own game loop.
class Screen:
    def run(self):
        self.onStart()
        while not self.changeScreen:
            for event in self.inputSource.pollEvents():
                if event.type == EventType.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                self.handleEvent(event)
            self.draw()
            self.renderer.present()
        self.changeScreen = False
        self.onExit()
        return self.nextScreen

    def onStart(self):
        pass

    def onExit(self):
        pass

    def handleEvent(self, event):
        pass

    def draw(self):
        pass
