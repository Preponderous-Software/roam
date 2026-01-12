package com.preponderous.roam.persistence;

import com.preponderous.roam.model.*;
import com.preponderous.roam.model.entity.*;
import com.preponderous.roam.persistence.service.PersistenceService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests to verify that entity IDs are preserved across save/load cycles.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
@ActiveProfiles("test")
public class EntityIdPersistenceTest {
    
    @Autowired
    private PersistenceService persistenceService;
    
    @Test
    public void testEntityIdsPreservedForStaticEntities() {
        // Given: Create entities and capture their IDs
        String sessionId = "test-id-preservation-static";
        WorldConfig worldConfig = new WorldConfig(99999L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, 0L, world);
        
        Room room = new Room(0, 0, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room);
        
        Tree tree = new Tree();
        String treeId = tree.getId();
        tree.setHarvestCount(2);
        room.addEntity(tree);
        
        Rock rock = new Rock();
        String rockId = rock.getId();
        rock.setHarvestCount(1);
        room.addEntity(rock);
        
        Apple apple = new Apple();
        String appleId = apple.getId();
        apple.setEnergyValue(18.0);
        room.addEntity(apple);
        
        // When: Save and load
        persistenceService.saveGameState(gameState);
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        
        // Then: Verify IDs are preserved
        assertTrue(loadedState.isPresent());
        Room loadedRoom = loadedState.get().getWorld().getRoom(0, 0);
        assertNotNull(loadedRoom);
        assertEquals(3, loadedRoom.getEntitiesList().size());
        
        // Find and verify tree ID
        Tree loadedTree = (Tree) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Tree)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedTree);
        assertEquals(treeId, loadedTree.getId(), "Tree ID should be preserved");
        assertEquals(2, loadedTree.getHarvestCount());
        
        // Find and verify rock ID
        Rock loadedRock = (Rock) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Rock)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedRock);
        assertEquals(rockId, loadedRock.getId(), "Rock ID should be preserved");
        assertEquals(1, loadedRock.getHarvestCount());
        
        // Find and verify apple ID
        Apple loadedApple = (Apple) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Apple)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedApple);
        assertEquals(appleId, loadedApple.getId(), "Apple ID should be preserved");
        assertEquals(18.0, loadedApple.getEnergyValue(), 0.01);
    }
    
    @Test
    public void testEntityIdsPreservedForLivingEntities() {
        // Given: Create living entities and capture their IDs
        String sessionId = "test-id-preservation-living";
        WorldConfig worldConfig = new WorldConfig(88888L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, 0L, world);
        
        Room room = new Room(0, 0, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room);
        
        Deer deer = new Deer(100L);
        String deerId = deer.getId();
        deer.setEnergy(45.0);
        deer.setMoveSpeed(32);
        room.addEntity(deer);
        
        Bear bear = new Bear(150L);
        String bearId = bear.getId();
        bear.setEnergy(75.0);
        bear.setAggressive(false);
        room.addEntity(bear);
        
        Chicken chicken = new Chicken(200L);
        String chickenId = chicken.getId();
        chicken.setEnergy(25.0);
        room.addEntity(chicken);
        
        // When: Save and load
        persistenceService.saveGameState(gameState);
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        
        // Then: Verify IDs are preserved
        assertTrue(loadedState.isPresent());
        Room loadedRoom = loadedState.get().getWorld().getRoom(0, 0);
        assertNotNull(loadedRoom);
        assertEquals(3, loadedRoom.getEntitiesList().size());
        
        // Find and verify deer ID
        Deer loadedDeer = (Deer) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Deer)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedDeer);
        assertEquals(deerId, loadedDeer.getId(), "Deer ID should be preserved");
        assertEquals(45.0, loadedDeer.getEnergy(), 0.01);
        assertEquals(32, loadedDeer.getMoveSpeed());
        
        // Find and verify bear ID
        Bear loadedBear = (Bear) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Bear)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedBear);
        assertEquals(bearId, loadedBear.getId(), "Bear ID should be preserved");
        assertEquals(75.0, loadedBear.getEnergy(), 0.01);
        assertFalse(loadedBear.isAggressive());
        
        // Find and verify chicken ID
        Chicken loadedChicken = (Chicken) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Chicken)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedChicken);
        assertEquals(chickenId, loadedChicken.getId(), "Chicken ID should be preserved");
        assertEquals(25.0, loadedChicken.getEnergy(), 0.01);
    }
    
    @Test
    public void testEntityIdsPreservedAcrossMultipleSaveCycles() {
        // Given: Create an entity
        String sessionId = "test-multi-save-id-preservation";
        WorldConfig worldConfig = new WorldConfig(77777L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, 0L, world);
        
        Room room = new Room(0, 0, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room);
        
        Tree tree = new Tree();
        String originalTreeId = tree.getId();
        tree.setHarvestCount(1);
        room.addEntity(tree);
        
        // When: Save, load, modify, save again, load again
        persistenceService.saveGameState(gameState);
        
        Optional<GameState> loaded1 = persistenceService.loadGameState(sessionId);
        assertTrue(loaded1.isPresent());
        Room room1 = loaded1.get().getWorld().getRoom(0, 0);
        Tree tree1 = (Tree) room1.getEntitiesList().get(0);
        String firstLoadId = tree1.getId();
        assertEquals(originalTreeId, firstLoadId, "ID should match after first load");
        
        // Modify the tree
        tree1.setHarvestCount(2);
        persistenceService.saveGameState(loaded1.get());
        
        // Load again
        Optional<GameState> loaded2 = persistenceService.loadGameState(sessionId);
        assertTrue(loaded2.isPresent());
        Room room2 = loaded2.get().getWorld().getRoom(0, 0);
        Tree tree2 = (Tree) room2.getEntitiesList().get(0);
        String secondLoadId = tree2.getId();
        
        // Then: ID should still be the same
        assertEquals(originalTreeId, secondLoadId, "ID should be preserved across multiple save/load cycles");
        assertEquals(2, tree2.getHarvestCount(), "Modified state should be preserved");
    }
}
