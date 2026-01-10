"""Tests for the world generator service"""
import pytest
from server.services.worldGenerator import WorldGenerator, BiomeType


def test_world_generator_initialization():
    """Test world generator initializes with default parameters"""
    generator = WorldGenerator()
    assert generator.seed is not None
    assert generator.grid_size == 17


def test_world_generator_with_seed():
    """Test world generator with custom seed"""
    seed = 12345
    generator = WorldGenerator(seed=seed)
    assert generator.seed == seed


def test_world_generator_reproducibility():
    """Test that same seed produces same results"""
    seed = 42
    gen1 = WorldGenerator(seed=seed)
    gen2 = WorldGenerator(seed=seed)
    
    room1 = gen1.generate_room_data(0, 0)
    room2 = gen2.generate_room_data(0, 0)
    
    assert room1["biome"] == room2["biome"]
    assert room1["background_color"] == room2["background_color"]


def test_generate_world_config():
    """Test world config generation"""
    generator = WorldGenerator(seed=123, grid_size=20)
    config = generator.generate_world_config()
    
    assert config["seed"] == 123
    assert config["grid_size"] == 20
    assert "biomes" in config
    assert len(config["biomes"]) == 4


def test_generate_room_data():
    """Test room data generation"""
    generator = WorldGenerator(seed=456)
    room = generator.generate_room_data(5, 10)
    
    assert room["x"] == 5
    assert room["y"] == 10
    assert "biome" in room
    assert room["biome"] in [
        BiomeType.GRASSLAND,
        BiomeType.FOREST,
        BiomeType.JUNGLE,
        BiomeType.MOUNTAIN
    ]
    assert "terrain_features" in room
    assert "resources" in room
    assert "environmental_objects" in room
    assert "background_color" in room
    assert len(room["background_color"]) == 3


def test_biome_selection():
    """Test that biome selection is deterministic"""
    generator = WorldGenerator(seed=789)
    biome1 = generator.generate_room_data(3, 3)["biome"]
    biome2 = generator.generate_room_data(3, 3)["biome"]
    
    assert biome1 == biome2


def test_different_coordinates_can_have_different_biomes():
    """Test that different coordinates can generate different biomes"""
    generator = WorldGenerator(seed=100)
    
    # Generate multiple rooms
    rooms = [generator.generate_room_data(x, y) for x in range(10) for y in range(10)]
    biomes = set(room["biome"] for room in rooms)
    
    # Should have at least 2 different biomes in 100 rooms
    assert len(biomes) >= 2


def test_generate_world_overview():
    """Test world overview generation"""
    generator = WorldGenerator(seed=200)
    overview = generator.generate_world_overview(radius=5)
    
    assert overview["seed"] == 200
    assert overview["radius"] == 5
    assert "total_rooms" in overview
    assert overview["total_rooms"] == 11 * 11  # (2*5+1)^2
    assert "biome_distribution" in overview
    assert "rooms" in overview
    
    # Check biome distribution
    dist = overview["biome_distribution"]
    assert dist[BiomeType.GRASSLAND] >= 0
    assert dist[BiomeType.FOREST] >= 0
    assert dist[BiomeType.JUNGLE] >= 0
    assert dist[BiomeType.MOUNTAIN] >= 0
    
    # Total should equal total rooms
    total = sum(dist.values())
    assert total == overview["total_rooms"]


def test_grassland_features():
    """Test grassland biome generates appropriate features"""
    generator = WorldGenerator(seed=300)
    
    # Find a grassland room
    for x in range(20):
        for y in range(20):
            room = generator.generate_room_data(x, y)
            if room["biome"] == BiomeType.GRASSLAND:
                # Should have grass
                feature_types = [f["type"] for f in room["terrain_features"]]
                assert "grass" in feature_types
                return
    
    # If no grassland found in 400 rooms, the test should still pass
    # as biome distribution is random


def test_mountain_features():
    """Test mountain biome generates appropriate features"""
    generator = WorldGenerator(seed=400)
    
    # Find a mountain room
    for x in range(20):
        for y in range(20):
            room = generator.generate_room_data(x, y)
            if room["biome"] == BiomeType.MOUNTAIN:
                # Should have stone
                feature_types = [f["type"] for f in room["terrain_features"]]
                assert "stone" in feature_types
                # Should have full density
                stone_feature = next(f for f in room["terrain_features"] if f["type"] == "stone")
                assert stone_feature["density"] == 1.0
                return
