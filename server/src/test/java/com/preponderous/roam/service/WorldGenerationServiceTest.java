package com.preponderous.roam.service;

import com.preponderous.roam.model.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class WorldGenerationServiceTest {

    @Autowired
    private WorldGenerationService worldGenerationService;

    @Test
    void testGenerateRoom() {
        WorldConfig config = WorldConfig.getDefault();
        World world = new World(config);
        
        Room room = worldGenerationService.generateRoom(world, 0, 0, 0L);
        
        assertNotNull(room);
        assertEquals(0, room.getRoomX());
        assertEquals(0, room.getRoomY());
        assertEquals(config.getRoomWidth(), room.getWidth());
        assertEquals(config.getRoomHeight(), room.getHeight());
        
        // Verify tiles are initialized
        Tile[][] tiles = room.getTiles();
        assertNotNull(tiles);
        assertEquals(config.getRoomHeight(), tiles.length);
        assertEquals(config.getRoomWidth(), tiles[0].length);
        
        // Verify at least one tile has a biome
        boolean hasBiome = false;
        for (int y = 0; y < room.getHeight(); y++) {
            for (int x = 0; x < room.getWidth(); x++) {
                if (tiles[y][x].getBiome() != null) {
                    hasBiome = true;
                    break;
                }
            }
        }
        assertTrue(hasBiome);
    }

    @Test
    void testGetOrGenerateRoom() {
        WorldConfig config = WorldConfig.getDefault();
        World world = new World(config);
        
        Room room1 = worldGenerationService.getOrGenerateRoom(world, 1, 1);
        Room room2 = worldGenerationService.getOrGenerateRoom(world, 1, 1);
        
        assertNotNull(room1);
        assertNotNull(room2);
        assertSame(room1, room2); // Should return the same instance
        
        assertTrue(world.hasRoom(1, 1));
    }

    @Test
    void testRoomGeneration_DifferentCoordinates() {
        WorldConfig config = WorldConfig.getDefault();
        World world = new World(config);
        
        Room room1 = worldGenerationService.generateRoom(world, 0, 0, 0L);
        Room room2 = worldGenerationService.generateRoom(world, 1, 1, 0L);
        
        assertNotNull(room1);
        assertNotNull(room2);
        assertNotSame(room1, room2);
        assertEquals(0, room1.getRoomX());
        assertEquals(0, room1.getRoomY());
        assertEquals(1, room2.getRoomX());
        assertEquals(1, room2.getRoomY());
    }

    @Test
    void testResourceDistribution() {
        WorldConfig config = new WorldConfig(12345L, 32, 32, 1.0, 0.0); // 100% resources
        World world = new World(config);
        
        Room room = worldGenerationService.generateRoom(world, 0, 0, 0L);
        
        // With 100% density, most tiles should have resources
        int tilesWithResources = 0;
        for (int y = 0; y < room.getHeight(); y++) {
            for (int x = 0; x < room.getWidth(); x++) {
                if (room.getTile(x, y).hasResource()) {
                    tilesWithResources++;
                }
            }
        }
        
        assertTrue(tilesWithResources > 0);
    }

    @Test
    void testHazardPlacement() {
        WorldConfig config = new WorldConfig(12345L, 32, 32, 0.0, 1.0); // 100% hazards
        World world = new World(config);
        
        Room room = worldGenerationService.generateRoom(world, 0, 0, 0L);
        
        // With 100% density, most tiles should have hazards
        int tilesWithHazards = 0;
        for (int y = 0; y < room.getHeight(); y++) {
            for (int x = 0; x < room.getWidth(); x++) {
                if (room.getTile(x, y).hasHazard()) {
                    tilesWithHazards++;
                }
            }
        }
        
        assertTrue(tilesWithHazards > 0);
    }

    @Test
    void testDeterministicGeneration() {
        long seed = 54321L;
        WorldConfig config1 = new WorldConfig(seed, 32, 32, 0.1, 0.05);
        WorldConfig config2 = new WorldConfig(seed, 32, 32, 0.1, 0.05);
        
        World world1 = new World(config1);
        World world2 = new World(config2);
        
        Room room1 = worldGenerationService.generateRoom(world1, 5, 5, 0L);
        Room room2 = worldGenerationService.generateRoom(world2, 5, 5, 0L);
        
        // Same seed and coordinates should produce identical rooms
        assertEquals(room1.getRoomX(), room2.getRoomX());
        assertEquals(room1.getRoomY(), room2.getRoomY());
        
        // Check first tile for identical biome
        assertEquals(room1.getTile(0, 0).getBiome(), room2.getTile(0, 0).getBiome());
    }
}
