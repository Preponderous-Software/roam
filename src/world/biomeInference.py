from collections import Counter

from world.roomType import RoomType

_ROCK_CLASS_NAMES = ("Stone", "CoalOre", "IronOre", "GoldOre")


def inferBiomeFromClassNames(classNames, z=0):
    """Return the RoomType a room most likely was generated as, from the
    class names of every entity on it.

    Pure: reads nothing but its arguments. It is a rendering hint only (for
    example, how high a 3D view draws the room's terrain), never game state,
    and its result is never persisted.
    """
    counts = Counter(classNames)
    if z < 0 or counts["CaveFloor"] > 0:
        return RoomType.CAVE
    if counts["JungleWood"] > 0 or counts["Banana"] > 0:
        return RoomType.JUNGLE
    if counts["Grass"] == 0 and sum(counts[name] for name in _ROCK_CLASS_NAMES) > 0:
        return RoomType.MOUNTAIN
    # Oak trees always grow leaves around them. Oak logs with no leaves and a
    # wood floor are the starting home's walls, which the generator builds in
    # whatever room the world starts in.
    if counts["Leaves"] > 0 or (counts["OakWood"] > 0 and counts["WoodFloor"] == 0):
        return RoomType.FOREST
    if counts["Grass"] > 0:
        return RoomType.GRASSLAND
    return RoomType.EMPTY


def inferBiome(room):
    """Return the room's biome: its in-memory roomType when it has one,
    otherwise one inferred from its tile contents.

    Room.roomType is not persisted, so a room reloaded from a save has None.
    """
    roomType = room.getRoomType()
    if roomType is not None:
        return roomType
    classNames = []
    grid = room.getGrid()
    for location in list(grid.getLocations().values()):
        for entity in list(location.getEntities().values()):
            classNames.append(entity.__class__.__name__)
    return inferBiomeFromClassNames(classNames, room.getZ())
