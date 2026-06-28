try:
    import pygame as _pygame

    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# OS display query, kept here (a frontend-adjacent module) so backend-neutral
# code — notably Config, which computes a default window size before the
# frontend builds the window — can ask for the screen size without importing
# pygame itself (frontend-abstraction epic #433, follow-up #463). A text/web
# frontend would provide its own equivalent.
def getScreenSize():
    """Return the OS screen size as an (width, height) tuple.

    Returns a safe default when pygame is not available (e.g. Pyodide/WASM).
    Initializes the display subsystem first (idempotent) so the query works
    regardless of construction order — Config may run before the frontend has
    created the window."""
    if not _PYGAME_AVAILABLE:
        return (1920, 1080)
    _pygame.display.init()
    info = _pygame.display.Info()
    return (info.current_w, info.current_h)
