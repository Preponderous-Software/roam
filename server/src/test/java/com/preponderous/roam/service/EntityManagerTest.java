package com.preponderous.roam.service;

import com.preponderous.roam.model.Entity;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.WorldConfig;
import com.preponderous.roam.model.entity.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class EntityManagerTest {

    @Autowired
    private EntityManager entityManager;
    
    @Autowired
    private WorldGenerationService worldGenerationService;

    @Test
    void testSpawnInitialEntities() {
        WorldConfig config = WorldConfig.getDefault();
        World world = new World(config);
        Room room = worldGenerationService.generateRoom(world, 0, 0, 0L);
        
        // Room should have entities spawned
        assertFalse(room.getEntitiesList().isEmpty(), "Room should have entities");
        
        // Check that different entity types exist
        boolean hasTree = room.getEntitiesList().stream().anyMatch(e -> e instanceof Tree);
        boolean hasRock = room.getEntitiesList().stream().anyMatch(e -> e instanceof Rock);
        boolean hasBush = room.getEntitiesList().stream().anyMatch(e -> e instanceof Bush);
        boolean hasGrass = room.getEntitiesList().stream().anyMatch(e -> e instanceof Grass);
        boolean hasLeaves = room.getEntitiesList().stream().anyMatch(e -> e instanceof Leaves);
        
        // At least one type of harvestable should exist (probabilistic but very likely)
        assertTrue(hasTree || hasRock || hasBush, "Room should have at least one harvestable entity");
        
        // Grass and leaves should be present (high spawn rates make this very likely)
        assertTrue(hasGrass || hasLeaves, "Room should have grass or leaves");
    }

    @Test
    void testEntitySpawningIsDeterministic() {
        long seed = 12345L;
        WorldConfig config1 = new WorldConfig(seed, 32, 32, 0.1, 0.05);
        WorldConfig config2 = new WorldConfig(seed, 32, 32, 0.1, 0.05);
        
        World world1 = new World(config1);
        World world2 = new World(config2);
        
        Room room1 = worldGenerationService.generateRoom(world1, 5, 5, 0L);
        Room room2 = worldGenerationService.generateRoom(world2, 5, 5, 0L);
        
        // Same seed should produce same number of entities
        assertEquals(room1.getEntitiesList().size(), room2.getEntitiesList().size(),
                    "Same seed should produce same number of entities");
    }

    @Test
    void testUpdateEntities() {
        WorldConfig config = WorldConfig.getDefault();
        World world = new World(config);
        Room room = worldGenerationService.generateRoom(world, 0, 0, 0L);
        
        int initialEntityCount = room.getEntitiesList().size();
        
        // Update entities (should remove depleted harvestables if any)
        entityManager.updateEntities(room, 100L);
        
        // Count should be same or less (no new entities spawned, possibly removed depleted ones)
        assertTrue(room.getEntitiesList().size() <= initialEntityCount,
                  "Entity count should not increase during update");
    }

    @Test
    void testDespawnEntity() {
        WorldConfig config = WorldConfig.getDefault();
        World world = new World(config);
        Room room = worldGenerationService.generateRoom(world, 0, 0, 0L);
        
        // Get an entity to despawn
        if (!room.getEntitiesList().isEmpty()) {
            Entity entity = room.getEntitiesList().get(0);
            String entityId = entity.getId();
            
            // Despawn it
            boolean removed = entityManager.despawnEntity(room, entityId);
            
            assertTrue(removed, "Entity should be despawned");
            assertNull(room.getEntity(entityId), "Entity should no longer exist in room");
        }
    }
    
    @Test
    void testTreeHarvesting() {
        Tree tree = new Tree();
        
        assertTrue(tree.canHarvest(), "New tree should be harvestable");
        assertEquals(0, tree.getHarvestCount(), "New tree harvest count should be 0");
        
        tree.harvest();
        assertEquals(1, tree.getHarvestCount(), "Harvest count should increase");
        
        tree.harvest();
        tree.harvest();
        assertFalse(tree.canHarvest(), "Tree should be depleted after max harvests");
        assertTrue(tree.isDepleted(), "Tree should be marked as depleted");
    }
    
    @Test
    void testGrassAndLeavesEntities() {
        // Test Grass entity
        Grass grass = new Grass();
        assertEquals("Grass", grass.getName(), "Grass name should be 'Grass'");
        assertFalse(grass.isSolid(), "Grass should not be solid");
        assertEquals(1, grass.getQuantity(), "Grass quantity should be 1");
        assertEquals("assets/images/grass.png", grass.getImagePath(), "Grass image path should match");
        
        // Test Leaves entity
        Leaves leaves = new Leaves();
        assertEquals("Leaves", leaves.getName(), "Leaves name should be 'Leaves'");
        assertFalse(leaves.isSolid(), "Leaves should not be solid");
        assertEquals(1, leaves.getQuantity(), "Leaves quantity should be 1");
        assertEquals("assets/images/leaves.png", leaves.getImagePath(), "Leaves image path should match");
    }
}
