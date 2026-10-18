def collectLightSources(room):
    """Return every light source in the room, in tile coordinates, as a list of
    (tileX, tileY, radiusTiles, entityClassName) tuples.

    An entity is a light source when it has getLightRadius() (Torch, Campfire,
    GoldenLantern). Read-only: it only walks the room's grid.
    """
    sources = []
    grid = room.getGrid()
    for location in list(grid.getLocations().values()):
        if location.getNumEntities() == 0:
            continue
        for entity in list(location.getEntities().values()):
            if hasattr(entity, "getLightRadius"):
                sources.append(
                    (
                        location.getX(),
                        location.getY(),
                        entity.getLightRadius(),
                        entity.__class__.__name__,
                    )
                )
    return sources
