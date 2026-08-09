# Filename conventions for room captures and stitched map images.
#
# The world is keyed by (x, y, z), so every level needs its own captures and
# its own stitched map. Surface files (z = 0) keep the legacy unsuffixed names
# so saves made before per-level maps existed load unchanged -- the same
# convention Config.getRoomFilePath uses for room JSON.


# @author Daniel McCoy Stephenson
# @since August 9th, 2026
def getMapImageFilename(z=0):
    """Return the filename of the stitched map image for level ``z``."""
    if z == 0:
        return "mapImage.png"
    return "mapImage_z" + str(z) + ".png"


def getRoomImageFilename(x, y, z=0):
    """Return the filename of the captured room image at ``(x, y, z)``."""
    base = str(x) + "_" + str(y)
    if z == 0:
        return base + ".png"
    return base + "_" + str(z) + ".png"


def parseRoomImageFilename(filename):
    """Return the ``(x, y, z)`` a room capture belongs to, or None if the name
    is not a room capture. A name with no third component is a surface capture,
    which is what makes pre-per-level saves readable."""
    parts = filename.rsplit(".", 1)[0].split("_")
    if len(parts) not in (2, 3):
        return None
    try:
        x = int(parts[0])
        y = int(parts[1])
        z = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        return None
    return (x, y, z)
