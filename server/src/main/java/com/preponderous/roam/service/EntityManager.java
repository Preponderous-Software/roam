package com.preponderous.roam.service;

import com.preponderous.roam.model.Entity;
import com.preponderous.roam.model.LivingEntity;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.entity.*;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Service for managing entity lifecycle, spawning, and behavior.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class EntityManager {
    // Spawn rates per room (0.0 to 1.0)
    public static final double TREE_SPAWN_RATE = 0.05;
    public static final double ROCK_SPAWN_RATE = 0.03;
    public static final double BUSH_SPAWN_RATE = 0.04;
    public static final double BEAR_SPAWN_RATE = 0.01;
    public static final double DEER_SPAWN_RATE = 0.02;
    public static final double CHICKEN_SPAWN_RATE = 0.03;
    
    /**
     * Spawn initial entities in a room based on the world seed and room coordinates.
     * Uses deterministic random generation for consistent results.
     * 
     * @param room the Room to populate with entities
     * @param world the World containing generation configuration
     * @param currentTick the current game tick for entity creation timestamps
     */
    public void spawnInitialEntities(Room room, World world, long currentTick) {
        long seed = world.getConfig().getSeed() + room.getRoomX() * 10000L + room.getRoomY() * 100L;
        Random random = new Random(seed);
        
        int width = room.getWidth();
        int height = room.getHeight();
        int totalTiles = width * height;
        
        // Spawn trees - calculate expected count based on spawn rate
        int expectedTrees = (int) (totalTiles * TREE_SPAWN_RATE);
        for (int i = 0; i < expectedTrees; i++) {
            Tree tree = new Tree();
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            tree.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
            room.addEntity(tree);
        }
        
        // Spawn rocks
        int expectedRocks = (int) (totalTiles * ROCK_SPAWN_RATE);
        for (int i = 0; i < expectedRocks; i++) {
            Rock rock = new Rock();
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            rock.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
            room.addEntity(rock);
        }
        
        // Spawn bushes
        int expectedBushes = (int) (totalTiles * BUSH_SPAWN_RATE);
        for (int i = 0; i < expectedBushes; i++) {
            Bush bush = new Bush();
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            bush.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
            room.addEntity(bush);
        }
        
        // Spawn bears
        int expectedBears = (int) (totalTiles * BEAR_SPAWN_RATE);
        for (int i = 0; i < expectedBears; i++) {
            Bear bear = new Bear(currentTick);
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            bear.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
            room.addEntity(bear);
        }
        
        // Spawn deer
        int expectedDeer = (int) (totalTiles * DEER_SPAWN_RATE);
        for (int i = 0; i < expectedDeer; i++) {
            Deer deer = new Deer(currentTick);
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            deer.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
            room.addEntity(deer);
        }
        
        // Spawn chickens
        int expectedChickens = (int) (totalTiles * CHICKEN_SPAWN_RATE);
        for (int i = 0; i < expectedChickens; i++) {
            Chicken chicken = new Chicken(currentTick);
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            chicken.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
            room.addEntity(chicken);
        }
    }
    
    /**
     * Update all entities in a room for the current tick.
     * Handles entity AI, behavior, and lifecycle management.
     * 
     * @param room the Room containing entities to update
     * @param currentTick the current game tick
     */
    public void updateEntities(Room room, long currentTick) {
        // Basic lifecycle management and simple AI
        
        // Collect depleted harvestable entities to remove
        List<String> entitiesToRemove = new ArrayList<>();
        
        Random random = new Random(currentTick + room.getRoomX() * 1000L + room.getRoomY());
        
        for (Entity entity : room.getEntitiesList()) {
            // Remove depleted harvestables
            if ((entity instanceof Tree && ((Tree) entity).isDepleted()) ||
                (entity instanceof Rock && ((Rock) entity).isDepleted()) ||
                (entity instanceof Bush && ((Bush) entity).isDepleted())) {
                entitiesToRemove.add(entity.getId());
            }
            
            // Simple AI for wildlife - random movement every few ticks
            if (entity instanceof LivingEntity && currentTick % 10 == 0) {
                // 30% chance to move
                if (random.nextDouble() < 0.3) {
                    String[] locationParts = entity.getLocationId().split(",");
                    if (locationParts.length >= 4) {
                        int roomX = Integer.parseInt(locationParts[0]);
                        int roomY = Integer.parseInt(locationParts[1]);
                        int tileX = Integer.parseInt(locationParts[2]);
                        int tileY = Integer.parseInt(locationParts[3]);
                        
                        // Try to move in a random direction
                        int direction = random.nextInt(4); // 0=up, 1=left, 2=down, 3=right
                        int newTileX = tileX;
                        int newTileY = tileY;
                        
                        switch (direction) {
                            case 0: newTileY--; break; // up
                            case 1: newTileX--; break; // left
                            case 2: newTileY++; break; // down
                            case 3: newTileX++; break; // right
                        }
                        
                        // Keep within room bounds
                        if (newTileX >= 0 && newTileX < room.getWidth() &&
                            newTileY >= 0 && newTileY < room.getHeight()) {
                            
                            // Check if destination is occupied by a solid entity
                            String newLocationId = roomX + "," + roomY + "," + newTileX + "," + newTileY;
                            boolean occupied = room.getEntitiesList().stream()
                                .anyMatch(e -> e.isSolid() && newLocationId.equals(e.getLocationId()));
                            
                            if (!occupied) {
                                entity.setLocationId(newLocationId);
                            }
                        }
                    }
                }
            }
        }
        
        // Remove all depleted entities
        for (String entityId : entitiesToRemove) {
            room.removeEntity(entityId);
        }
    }
    
    /**
     * Despawn an entity from a room.
     * 
     * @param room the Room containing the entity
     * @param entityId the ID of the entity to despawn
     * @return true if the entity was removed, false if not found
     */
    public boolean despawnEntity(Room room, String entityId) {
        if (room.getEntity(entityId) != null) {
            room.removeEntity(entityId);
            return true;
        }
        return false;
    }
}
