import datetime
import uuid
from src.lib.pyenvlib.entity import Entity


def test_initialization():
    entity = Entity("TestEntity")
    
    # Test that basic properties are set
    assert entity.getName() == "TestEntity"
    assert isinstance(entity.getID(), uuid.UUID)
    assert entity.getEnvironmentID() == -1
    assert entity.getGridID() == -1
    assert entity.getLocationID() == -1
    
    # Test creation date is recent
    now = datetime.datetime.now()
    creation_time = entity.getCreationDate()
    assert isinstance(creation_time, datetime.datetime)
    time_diff = (now - creation_time).total_seconds()
    assert time_diff < 1  # Should be created within the last second


def test_unique_ids():
    entity1 = Entity("Entity1")
    entity2 = Entity("Entity2")
    
    # Each entity should have a unique ID
    assert entity1.getID() != entity2.getID()


def test_setters():
    entity = Entity("TestEntity")
    
    # Test setEnvironmentID
    entity.setEnvironmentID("env123")
    assert entity.getEnvironmentID() == "env123"
    
    # Test setGridID  
    entity.setGridID("grid456")
    assert entity.getGridID() == "grid456"
    
    # Test setLocationID
    entity.setLocationID("loc789")
    assert entity.getLocationID() == "loc789"


def test_string_representation():
    entity = Entity("TestEntity")
    
    # Test __str__ method - Entity uses default object representation
    str_repr = str(entity)
    assert "Entity object" in str_repr
    
    # Test that the entity has the expected name via getName()
    assert entity.getName() == "TestEntity"


def test_id_consistency():
    entity = Entity("TestEntity")
    
    # ID should be consistent across multiple calls
    id1 = entity.getID()
    id2 = entity.getID()
    assert id1 == id2