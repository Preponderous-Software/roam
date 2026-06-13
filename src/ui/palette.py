# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# Shared color palette for the UI and rendering layers.
#
# Colors are kept as plain (R, G, B) tuples so they remain backend-neutral:
# the pygame renderer consumes them directly today, and a future text or web
# renderer can map the same named constants to its own color model. Prefer a
# named constant here over an inline RGB literal so colors stay consistent and
# a frontend has a single place to reinterpret them.

# Grayscale ramp, lightest to darkest.
WHITE = (255, 255, 255)
LIGHT_GRAY = (220, 220, 220)
GRAY = (200, 200, 200)
MEDIUM_GRAY = (180, 180, 180)
DIM_GRAY = (140, 140, 140)
DARK_GRAY = (100, 100, 100)
DARKER_GRAY = (60, 60, 60)
CHARCOAL = (50, 50, 50)
NEAR_BLACK = (30, 30, 30)
BLACK = (0, 0, 0)

# Primary accents.
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)

# A deliberately garish color used to flag missing/!invalid assets in-game.
DEBUG_MAGENTA = (255, 0, 255)
