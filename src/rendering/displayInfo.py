import pygame


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

    Initializes the display subsystem first (idempotent) so the query works
    regardless of construction order — Config may run before the frontend has
    created the window."""
    pygame.display.init()
    info = pygame.display.Info()
    return (info.current_w, info.current_h)
