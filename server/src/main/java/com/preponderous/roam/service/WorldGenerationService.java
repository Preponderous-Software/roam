package com.preponderous.roam.service;

import com.preponderous.roam.model.*;
import org.springframework.stereotype.Service;

import java.util.Random;

/**
 * Service for procedural world generation.
 * Generates rooms with biomes, resources, and hazards.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class WorldGenerationService {
    private static final String[] RESOURCE_TYPES = {"Wood", "Stone", "Iron", "Gold", "Herbs"};
    private static final String[] HAZARD_TYPES = {"Spike Trap", "Poisonous Plant", "Lava Pool", "Ice Patch"};

    /**
     * Generate a new room at the specified coordinates.
     */
    public Room generateRoom(World world, int roomX, int roomY) {
        WorldConfig config = world.getConfig();
        Random random = new Random(config.getSeed() + roomX * 1000L + roomY);
        
        Room room = new Room(roomX, roomY, config.getRoomWidth(), config.getRoomHeight());
        
        // Generate biome distribution using Perlin-like noise simulation
        generateBiomes(room, random);
        
        // Distribute resources
        distributeResources(room, random, config.getResourceDensity());
        
        // Place hazards
        placeHazards(room, random, config.getHazardDensity());
        
        return room;
    }

    /**
     * Generate biome distribution for a room.
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
     */
    public Room getOrGenerateRoom(World world, int roomX, int roomY) {
        if (world.hasRoom(roomX, roomY)) {
            return world.getRoom(roomX, roomY);
        }
        
        Room room = generateRoom(world, roomX, roomY);
        world.addRoom(room);
        return room;
    }
}
