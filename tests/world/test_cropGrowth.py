from unittest.mock import MagicMock

from entity.youngCrop import YoungCrop
from entity.matureCrop import MatureCrop
from src.world.room import Room


def createRoom():
    graphik = MagicMock()
    room = Room("TestRoom", 3, (0, 128, 0), 0, 0, graphik)
    return room


def test_tick_crops_young_to_mature():
    room = createRoom()
    config = MagicMock()
    config.cropGrowthTicks = 100

    # Place a YoungCrop at tick 0
    locations = room.getGrid().getLocations()
    locationId = list(locations.keys())[0]
    location = locations[locationId]
    youngCrop = YoungCrop(0)
    room.addEntityToLocation(youngCrop, location)

    # After 100 ticks, crop should mature
    room.tickCrops(100, config)

    entities = list(location.getEntities().values())
    matureCrops = [e for e in entities if isinstance(e, MatureCrop)]
    youngCrops = [e for e in entities if isinstance(e, YoungCrop)]
    assert len(matureCrops) == 1
    assert len(youngCrops) == 0
    assert matureCrops[0].getTickPlanted() == 0


def test_tick_crops_young_not_ready():
    room = createRoom()
    config = MagicMock()
    config.cropGrowthTicks = 100

    locations = room.getGrid().getLocations()
    locationId = list(locations.keys())[0]
    location = locations[locationId]
    youngCrop = YoungCrop(0)
    room.addEntityToLocation(youngCrop, location)

    # After 50 ticks (less than cropGrowthTicks), should still be YoungCrop
    room.tickCrops(50, config)

    entities = list(location.getEntities().values())
    youngCrops = [e for e in entities if isinstance(e, YoungCrop)]
    matureCrops = [e for e in entities if isinstance(e, MatureCrop)]
    assert len(youngCrops) == 1
    assert len(matureCrops) == 0


def test_tick_crops_mature_stays_mature():
    room = createRoom()
    config = MagicMock()
    config.cropGrowthTicks = 100

    locations = room.getGrid().getLocations()
    locationId = list(locations.keys())[0]
    location = locations[locationId]
    matureCrop = MatureCrop(0)
    room.addEntityToLocation(matureCrop, location)

    # MatureCrop should remain (waiting for harvest)
    room.tickCrops(200, config)

    entities = list(location.getEntities().values())
    matureCrops = [e for e in entities if isinstance(e, MatureCrop)]
    assert len(matureCrops) == 1
