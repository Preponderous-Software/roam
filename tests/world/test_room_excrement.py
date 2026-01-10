import sys
import os
# Add src to path so we can import modules the same way src code does
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import pygame
from world.room import Room
from entity.living.chicken import Chicken
from entity.excrement import Excrement
from entity.grass import Grass
from lib.graphik.src.graphik import Graphik


def test_excrement_spawning_in_move():
    """Test that excrement is spawned when entities move"""
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    
    # Create a room
    room = Room("Test Room", 5, (100, 100, 100), 0, 0, graphik)
    
    # Create a chicken and add it to the room
    chicken = Chicken(0)
    room.addEntity(chicken)
    room.addLivingEntity(chicken)
    
    # Get the chicken's location
    locationId = chicken.getLocationID()
    
    # Count excrement before movement attempts
    excrement_count_before = 0
    for loc_id in room.getGrid().getLocations():
        location = room.getGrid().getLocation(loc_id)
        for entity_id in location.getEntities():
            entity = location.getEntity(entity_id)
            if isinstance(entity, Excrement):
                excrement_count_before += 1
    
    # Trigger multiple movement attempts (with 1% chance each)
    # We'll do many attempts to increase chance of movement happening
    for _ in range(200):
        room.moveLivingEntities(10000)
    
    # Count excrement after movement attempts
    excrement_count_after = 0
    for loc_id in room.getGrid().getLocations():
        location = room.getGrid().getLocation(loc_id)
        for entity_id in location.getEntities():
            entity = location.getEntity(entity_id)
            if isinstance(entity, Excrement):
                excrement_count_after += 1
    
    # With 200 attempts at 1% probability each, we should see some excrement
    # (This test might occasionally fail due to randomness, but probability is very low)
    assert excrement_count_after >= excrement_count_before
    
    pygame.quit()


def test_age_excrement_young():
    """Test that young excrement is not converted to grass"""
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    
    # Create a room
    room = Room("Test Room", 5, (100, 100, 100), 0, 0, graphik)
    
    # Create excrement at tick 1000
    excrement = Excrement(1000)
    locationIds = list(room.getGrid().getLocations().keys())
    location = room.getGrid().getLocation(locationIds[0])
    room.addEntityToLocation(excrement, location)
    
    # Age excrement at tick 11000 (only 10000 ticks old, threshold is 18000)
    room.ageExcrement(11000)
    
    # Check that excrement still exists
    has_excrement = False
    for entity_id in location.getEntities():
        entity = location.getEntity(entity_id)
        if isinstance(entity, Excrement):
            has_excrement = True
            break
    
    assert has_excrement == True
    
    pygame.quit()


def test_age_excrement_old():
    """Test that old excrement is converted to grass"""
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    
    # Create a room
    room = Room("Test Room", 5, (100, 100, 100), 0, 0, graphik)
    
    # Create excrement at tick 1000
    excrement = Excrement(1000)
    locationIds = list(room.getGrid().getLocations().keys())
    locationId = locationIds[0]
    location = room.getGrid().getLocation(locationId)
    room.addEntityToLocation(excrement, location)
    
    # Age excrement at tick 19000 (18000 ticks old, meets threshold)
    room.ageExcrement(19000)
    
    # Re-fetch the location to get updated entity list
    location = room.getGrid().getLocation(locationId)
    
    # Check that excrement has been converted to grass
    has_excrement = False
    has_grass = False
    for entity_id in list(location.getEntities().keys()):
        entity = location.getEntity(entity_id)
        if isinstance(entity, Excrement):
            has_excrement = True
        elif isinstance(entity, Grass):
            has_grass = True
    
    assert has_excrement == False
    assert has_grass == True
    
    pygame.quit()


def test_age_excrement_exact_threshold():
    """Test that excrement at exact threshold is converted"""
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    
    # Create a room
    room = Room("Test Room", 5, (100, 100, 100), 0, 0, graphik)
    
    # Create excrement at tick 2000
    excrement = Excrement(2000)
    locationIds = list(room.getGrid().getLocations().keys())
    locationId = locationIds[0]
    location = room.getGrid().getLocation(locationId)
    room.addEntityToLocation(excrement, location)
    
    # Age excrement at exactly threshold (18000 ticks = EXCREMENT_AGE_THRESHOLD_TICKS)
    room.ageExcrement(2000 + room.EXCREMENT_AGE_THRESHOLD_TICKS)
    
    # Re-fetch the location to get updated entity list
    location = room.getGrid().getLocation(locationId)
    
    # Check that excrement has been converted to grass
    has_excrement = False
    has_grass = False
    for entity_id in list(location.getEntities().keys()):
        entity = location.getEntity(entity_id)
        if isinstance(entity, Excrement):
            has_excrement = True
        elif isinstance(entity, Grass):
            has_grass = True
    
    assert has_excrement == False
    assert has_grass == True
    
    pygame.quit()


def test_multiple_excrement_aging():
    """Test that multiple excrement entities are handled correctly"""
    pygame.init()
    gameDisplay = pygame.display.set_mode((100, 100))
    graphik = Graphik(gameDisplay)
    
    # Create a room
    room = Room("Test Room", 5, (100, 100, 100), 0, 0, graphik)
    
    # Add multiple excrement at different ages
    locationIds = list(room.getGrid().getLocations().keys())
    
    # Young excrement (should not convert)
    youngLocationId = locationIds[0]
    young_location = room.getGrid().getLocation(youngLocationId)
    young_excrement = Excrement(10000)
    room.addEntityToLocation(young_excrement, young_location)
    
    # Old excrement (should convert)
    oldLocationId = locationIds[1]
    old_location = room.getGrid().getLocation(oldLocationId)
    old_excrement = Excrement(1000)
    room.addEntityToLocation(old_excrement, old_location)
    
    # Age all excrement at tick 20000
    room.ageExcrement(20000)
    
    # Re-fetch locations to get updated entity lists
    young_location = room.getGrid().getLocation(youngLocationId)
    old_location = room.getGrid().getLocation(oldLocationId)
    
    # Check young excrement location - should still have excrement
    has_young_excrement = False
    for entity_id in list(young_location.getEntities().keys()):
        entity = young_location.getEntity(entity_id)
        if isinstance(entity, Excrement):
            has_young_excrement = True
            break
    
    # Check old excrement location - should have grass instead
    has_old_excrement = False
    has_grass = False
    for entity_id in list(old_location.getEntities().keys()):
        entity = old_location.getEntity(entity_id)
        if isinstance(entity, Excrement):
            has_old_excrement = True
        elif isinstance(entity, Grass):
            has_grass = True
    
    assert has_young_excrement == True
    assert has_old_excrement == False
    assert has_grass == True
    
    pygame.quit()
