# @author Daniel McCoy Stephenson
# @since April 18th, 2026
#
# Shared layout constants for the hotbar HUD element.
# Referenced by ui/status.py, screen/worldScreen.py, and tests.

HOTBAR_SLOT_SIZE = 50
HOTBAR_SLOT_GAP = 5
HOTBAR_PADDING = 5
HOTBAR_BOTTOM_OFFSET = HOTBAR_SLOT_SIZE * 3


def getHotbarTop(displayHeight):
    return displayHeight - HOTBAR_BOTTOM_OFFSET - HOTBAR_PADDING
