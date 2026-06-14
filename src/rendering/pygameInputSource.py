import pygame

from rendering.inputEvent import EventType, InputEvent
from rendering.inputSource import InputSource
from rendering.keyCode import fromInt


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# pygame implementation of the input seam (frontend-abstraction epic #433,
# Phase 4). Translates native pygame events and key/mouse state into the
# backend-neutral InputEvent / KeyCode model so screens never touch pygame.
class PygameInputSource(InputSource):
    # pygame event type -> neutral EventType for the simple (no extra data) cases.
    _SIMPLE_TYPES = {
        pygame.QUIT: EventType.QUIT,
        pygame.MOUSEMOTION: EventType.MOUSE_MOTION,
        pygame.WINDOWFOCUSLOST: EventType.FOCUS_LOST,
        pygame.WINDOWFOCUSGAINED: EventType.FOCUS_GAINED,
    }

    def pollEvents(self):
        events = []
        for event in pygame.event.get():
            translated = self._translate(event)
            if translated is not None:
                events.append(translated)
        return events

    def _translate(self, event):
        eventType = event.type
        if eventType in (pygame.KEYDOWN, pygame.KEYUP):
            neutral = EventType.KEY_DOWN if eventType == pygame.KEYDOWN else EventType.KEY_UP
            return InputEvent(neutral, key=fromInt(event.key))
        if eventType in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            neutral = (
                EventType.MOUSE_DOWN
                if eventType == pygame.MOUSEBUTTONDOWN
                else EventType.MOUSE_UP
            )
            return InputEvent(neutral, position=event.pos, button=event.button)
        if eventType == pygame.MOUSEMOTION:
            return InputEvent(EventType.MOUSE_MOTION, position=event.pos)
        if eventType == pygame.MOUSEWHEEL:
            return InputEvent(EventType.MOUSE_WHEEL, scrollY=event.y)
        if eventType == pygame.TEXTINPUT:
            return InputEvent(EventType.TEXT_INPUT, text=event.text)
        if eventType in (pygame.VIDEORESIZE, pygame.WINDOWRESIZED):
            # VIDEORESIZE carries .size; WINDOWRESIZED carries .x/.y (the new
            # width/height). Normalize both to a (width, height) tuple.
            size = getattr(event, "size", None)
            if size is None:
                size = (event.x, event.y)
            return InputEvent(EventType.WINDOW_RESIZE, size=size)
        if eventType in self._SIMPLE_TYPES:
            return InputEvent(self._SIMPLE_TYPES[eventType])
        return InputEvent(EventType.OTHER)

    def isPressed(self, keyCode):
        if keyCode is None:
            return False
        pressed = pygame.key.get_pressed()
        index = int(keyCode)
        # pygame.key.get_pressed() is indexed by keycode but only spans the
        # lower range; large SDL keycodes (arrows, modifiers) fall outside it.
        # Guard so an out-of-range query is a clean False rather than a crash.
        if 0 <= index < len(pressed):
            return bool(pressed[index])
        return False

    def getMousePosition(self):
        return pygame.mouse.get_pos()

    def getMouseButtons(self):
        return pygame.mouse.get_pressed()
