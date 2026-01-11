package com.preponderous.roam.service;

import com.preponderous.roam.model.Entity;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.entity.*;
import org.springframework.stereotype.Service;

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
        
        // Spawn trees
        for (int i = 0; i < width * height * TREE_SPAWN_RATE; i++) {
            if (random.nextDouble() < TREE_SPAWN_RATE) {
                Tree tree = new Tree();
                int x = random.nextInt(width);
                int y = random.nextInt(height);
                tree.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
                room.addEntity(tree);
            }
        }
        
        // Spawn rocks
        for (int i = 0; i < width * height * ROCK_SPAWN_RATE; i++) {
            if (random.nextDouble() < ROCK_SPAWN_RATE) {
                Rock rock = new Rock();
                int x = random.nextInt(width);
                int y = random.nextInt(height);
                rock.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
                room.addEntity(rock);
            }
        }
        
        // Spawn bushes
        for (int i = 0; i < width * height * BUSH_SPAWN_RATE; i++) {
            if (random.nextDouble() < BUSH_SPAWN_RATE) {
                Bush bush = new Bush();
                int x = random.nextInt(width);
                int y = random.nextInt(height);
                bush.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
                room.addEntity(bush);
            }
        }
        
        // Spawn bears
        for (int i = 0; i < width * height * BEAR_SPAWN_RATE; i++) {
            if (random.nextDouble() < BEAR_SPAWN_RATE) {
                Bear bear = new Bear(currentTick);
                int x = random.nextInt(width);
                int y = random.nextInt(height);
                bear.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
                room.addEntity(bear);
            }
        }
        
        // Spawn deer
        for (int i = 0; i < width * height * DEER_SPAWN_RATE; i++) {
            if (random.nextDouble() < DEER_SPAWN_RATE) {
                Deer deer = new Deer(currentTick);
                int x = random.nextInt(width);
                int y = random.nextInt(height);
                deer.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
                room.addEntity(deer);
            }
        }
        
        // Spawn chickens
        for (int i = 0; i < width * height * CHICKEN_SPAWN_RATE; i++) {
            if (random.nextDouble() < CHICKEN_SPAWN_RATE) {
                Chicken chicken = new Chicken(currentTick);
                int x = random.nextInt(width);
                int y = random.nextInt(height);
                chicken.setLocationId(room.getRoomX() + "," + room.getRoomY() + "," + x + "," + y);
                room.addEntity(chicken);
            }
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
        // For now, basic lifecycle management
        // Future: Implement AI movement, reproduction, resource respawning, etc.
        
        // Remove depleted harvestable entities
        room.getEntitiesList().stream()
            .filter(entity -> entity instanceof Tree && ((Tree) entity).isDepleted())
            .forEach(entity -> room.removeEntity(entity.getId()));
            
        room.getEntitiesList().stream()
            .filter(entity -> entity instanceof Rock && ((Rock) entity).isDepleted())
            .forEach(entity -> room.removeEntity(entity.getId()));
            
        room.getEntitiesList().stream()
            .filter(entity -> entity instanceof Bush && ((Bush) entity).isDepleted())
            .forEach(entity -> room.removeEntity(entity.getId()));
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
