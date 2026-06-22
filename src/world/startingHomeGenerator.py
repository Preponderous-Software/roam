from entity.apple import Apple
from entity.banana import Banana
from entity.bed import Bed
from entity.chest import Chest
from entity.oakWood import OakWood
from entity.torch import Torch
from entity.woodFloor import WoodFloor
from gameLogging.logger import getLogger
from world.room import Room

_logger = getLogger(__name__)


# @author Claude
# @since June 21st, 2026
class StartingHomeGenerator:
    """Sets up a brand-new player's starting situation.

    When a fresh world is generated, this builds a small home at the center of
    the origin room (a square of Oak Wood walls with a wood floor, a doorway, a
    bed and a chest) and grants the player a little starting food so they don't
    starve before getting established. It is only meant to run once, for a new
    world.
    """

    # Side length, in tiles, of the home (walls included). Must be odd so the
    # home has a single center tile for the player to spawn on.
    SIZE = 7

    def generate(self, room: Room):
        """Build the starting home in ``room`` and return the location where
        the player should spawn (the center tile). Returns -1 if the room is
        too small to hold the home, in which case nothing is built.
        """
        grid = room.getGrid()
        size = grid.getColumns()
        half = self.SIZE // 2
        center = size // 2
        left = center - half
        right = center + half
        top = center - half
        bottom = center + half

        if left < 0 or top < 0 or right >= size or bottom >= size:
            _logger.warning(
                "room too small for starting home; skipping",
                gridSize=size,
                homeSize=self.SIZE,
            )
            return grid.getLocationByCoordinates(center, center)

        # Leave a doorway in the bottom-center wall so the player can leave.
        doorX, doorY = center, bottom

        for x in range(left, right + 1):
            for y in range(top, bottom + 1):
                location = grid.getLocationByCoordinates(x, y)
                if location == -1:
                    continue
                onBorder = x in (left, right) or y in (top, bottom)
                isDoorway = x == doorX and y == doorY
                if onBorder and not isDoorway:
                    room.addEntityToLocation(OakWood(), location)
                else:
                    room.addEntityToLocation(WoodFloor(), location)

        # Furnish the interior: a bed in one corner and a chest in another.
        bedLocation = grid.getLocationByCoordinates(left + 1, top + 1)
        if bedLocation != -1:
            room.addEntityToLocation(Bed(), bedLocation)
        chestLocation = grid.getLocationByCoordinates(right - 1, top + 1)
        if chestLocation != -1:
            room.addEntityToLocation(Chest(), chestLocation)

        # A torch for light, on a free bottom corner (the bed and chest occupy
        # the two top corners).
        torchLocation = grid.getLocationByCoordinates(left + 1, bottom - 1)
        if torchLocation != -1:
            room.addEntityToLocation(Torch(), torchLocation)

        _logger.info("starting home generated", roomX=room.getX(), roomY=room.getY())
        return grid.getLocationByCoordinates(center, center)

    def grantStartingItems(self, player):
        """Give the player a small amount of starting food."""
        inventory = player.getInventory()
        for _ in range(5):
            inventory.placeIntoFirstAvailableInventorySlot(Apple())
        for _ in range(3):
            inventory.placeIntoFirstAvailableInventorySlot(Banana())
        _logger.info("granted starting items to player")
