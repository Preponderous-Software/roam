package com.preponderous.roam.service;

import com.preponderous.roam.model.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Random;

/**
 * Service for procedural world generation.
 * Generates rooms with biomes, resources, hazards, and entities.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class WorldGenerationService {
    private static final String[] RESOURCE_TYPES = {"Wood", "Stone", "Iron", "Gold", "Herbs"};
    private static final String[] HAZARD_TYPES = {"Spike Trap", "Poisonous Plant", "Lava Pool", "Ice Patch"};

    @Autowired
    private EntityManager entityManager;

    /**
     * Generate a new room at the specified coordinates.
     * Uses deterministic random generation based on world seed and room coordinates.
     * 
     * @param world the World containing generation configuration
     * @param roomX the X coordinate of the room in world space
     * @param roomY the Y coordinate of the room in world space
     * @param currentTick the current game tick for entity timestamps
     * @return a newly generated Room with biomes, resources, hazards, and entities
     */
    public Room generateRoom(World world, int roomX, int roomY, long currentTick) {
        WorldConfig config = world.getConfig();
        Random random = new Random(config.getSeed() + roomX * 1000L + roomY);
        
        Room room = new Room(roomX, roomY, config.getRoomWidth(), config.getRoomHeight());
        
        // Generate biome distribution using Perlin-like noise simulation
        generateBiomes(room, random);
        
        // Distribute resources
        distributeResources(room, random, config.getResourceDensity());
        
        // Place hazards
        placeHazards(room, random, config.getHazardDensity());
        
        // Spawn entities
        entityManager.spawnInitialEntities(room, world, currentTick);
        
        return room;
    }

    /**
     * Generate biome distribution for a room.
     * Creates a dominant biome (70%) with variation (30%) for natural appearance.
     * 
     * @param room the Room to populate with biomes
     * @param random the Random instance for deterministic generation
     */
    private void generateBiomes(Room room, Random random) {
        int width = room.getWidth();
        int height = room.getHeight();
        
        // Select a dominant biome for the room
        Biome dominantBiome = Biome.values()[random.nextInt(Biome.values().length)];
        
        // Fill the room with variations
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                Biome biome;
                
                // 70% chance of dominant biome, 30% chance of random variation
                if (random.nextDouble() < 0.7) {
                    biome = dominantBiome;
                } else {
                    biome = Biome.values()[random.nextInt(Biome.values().length)];
                }
                
                Tile tile = new Tile(x, y, biome);
                room.setTile(x, y, tile);
            }
        }
    }

    /**
     * Distribute resources across the room.
     * Places resources probabilistically based on density parameter.
     * 
     * @param room the Room to populate with resources
     * @param random the Random instance for deterministic generation
     * @param density the probability (0.0-1.0) of a tile containing resources
     */
    private void distributeResources(Room room, Random random, double density) {
        int width = room.getWidth();
        int height = room.getHeight();
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                if (random.nextDouble() < density) {
                    Tile tile = room.getTile(x, y);
                    if (tile != null) {
                        String resourceType = RESOURCE_TYPES[random.nextInt(RESOURCE_TYPES.length)];
                        int resourceAmount = 1 + random.nextInt(5); // 1-5 units
                        
                        tile.setResourceType(resourceType);
                        tile.setResourceAmount(resourceAmount);
                    }
                }
            }
        }
    }

    /**
     * Place environmental hazards in the room.
     * Hazards are only placed on tiles without resources.
     * 
     * @param room the Room to populate with hazards
     * @param random the Random instance for deterministic generation
     * @param density the probability (0.0-1.0) of a tile containing a hazard
     */
    private void placeHazards(Room room, Random random, double density) {
        int width = room.getWidth();
        int height = room.getHeight();
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                if (random.nextDouble() < density) {
                    Tile tile = room.getTile(x, y);
                    if (tile != null && !tile.hasResource()) {
                        String hazardType = HAZARD_TYPES[random.nextInt(HAZARD_TYPES.length)];
                        
                        tile.setHasHazard(true);
                        tile.setHazardType(hazardType);
                    }
                }
            }
        }
    }

    /**
     * Get or generate a room for the world.
     * Thread-safe implementation using synchronized block to prevent race conditions
     * where multiple threads might generate the same room simultaneously.
     * 
     * @param world the World containing generation configuration and room storage
     * @param roomX the X coordinate of the room in world space
     * @param roomY the Y coordinate of the room in world space
     * @param currentTick the current game tick for entity timestamps
     * @return the Room at the specified coordinates (existing or newly generated)
     */
    public Room getOrGenerateRoom(World world, int roomX, int roomY, long currentTick) {
        // Fast path: try to get an existing room without locking.
        Room existingRoom = world.getRoom(roomX, roomY);
        if (existingRoom != null) {
            return existingRoom;
        }

        // Synchronize to avoid generating the same room multiple times concurrently.
        synchronized (world) {
            // Re-check in case another thread created the room while we were waiting.
            existingRoom = world.getRoom(roomX, roomY);
            if (existingRoom != null) {
                return existingRoom;
            }

            Room room = generateRoom(world, roomX, roomY, currentTick);
            world.addRoom(room);
            return room;
        }
    }
    
    /**
     * Get or generate a room for the world (without tick parameter for backward compatibility).
     * 
     * @param world the World containing generation configuration and room storage
     * @param roomX the X coordinate of the room in world space
     * @param roomY the Y coordinate of the room in world space
     * @return the Room at the specified coordinates (existing or newly generated)
     */
    public Room getOrGenerateRoom(World world, int roomX, int roomY) {
        return getOrGenerateRoom(world, roomX, roomY, 0L);
    }
}
