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
 * Integration tests for entity persistence.
 * Validates that all entity types are correctly saved and loaded.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
@ActiveProfiles("test")
public class EntityPersistenceTest {
    
    @Autowired
    private PersistenceService persistenceService;
    
    @Test
    public void testTreePersistence() {
        // Given: Create a game state with a tree
        String sessionId = "test-tree-session";
        WorldConfig worldConfig = new WorldConfig(12345L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, 0L, world);
        
        // Add a tree to the starting room
        Room room = new Room(0, 0, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room);
        Tree tree = new Tree();
        tree.setHarvestCount(2);
        tree.setMaxHarvestCount(5);
        tree.setLocationId("0,0");
        room.addEntity(tree);
        
        // When: Save and load
        persistenceService.saveGameState(gameState);
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        
        // Then: Verify tree was persisted
        assertTrue(loadedState.isPresent());
        Room loadedRoom = loadedState.get().getWorld().getRoom(0, 0);
        assertNotNull(loadedRoom);
        assertEquals(1, loadedRoom.getEntitiesList().size());
        
        Entity loadedEntity = loadedRoom.getEntitiesList().get(0);
        assertTrue(loadedEntity instanceof Tree);
        Tree loadedTree = (Tree) loadedEntity;
        assertEquals(2, loadedTree.getHarvestCount());
        assertEquals(5, loadedTree.getMaxHarvestCount());
        assertEquals("0,0", loadedTree.getLocationId());
        assertTrue(loadedTree.isSolid());
    }
    
    @Test
    public void testAnimalPersistence() {
        // Given: Create a game state with animals
        String sessionId = "test-animal-session";
        WorldConfig worldConfig = new WorldConfig(54321L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, 0L, world);
        
        Room room = new Room(0, 0, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room);
        
        // Add a deer
        Deer deer = new Deer(100L);
        deer.setEnergy(45.0);
        deer.setMoveSpeed(30);
        deer.setFleeRange(5.0);
        room.addEntity(deer);
        
        // Add a bear
        Bear bear = new Bear(150L);
        bear.setEnergy(70.0);
        bear.setMoveSpeed(25);
        bear.setAggressionRange(6.0);
        bear.setAggressive(true);
        room.addEntity(bear);
        
        // When: Save and load
        persistenceService.saveGameState(gameState);
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        
        // Then: Verify animals were persisted
        assertTrue(loadedState.isPresent());
        Room loadedRoom = loadedState.get().getWorld().getRoom(0, 0);
        assertNotNull(loadedRoom);
        assertEquals(2, loadedRoom.getEntitiesList().size());
        
        // Find deer
        Deer loadedDeer = (Deer) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Deer)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedDeer);
        assertEquals(45.0, loadedDeer.getEnergy(), 0.01);
        assertEquals(30, loadedDeer.getMoveSpeed());
        assertEquals(5.0, loadedDeer.getFleeRange(), 0.01);
        
        // Find bear
        Bear loadedBear = (Bear) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Bear)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedBear);
        assertEquals(70.0, loadedBear.getEnergy(), 0.01);
        assertEquals(25, loadedBear.getMoveSpeed());
        assertEquals(6.0, loadedBear.getAggressionRange(), 0.01);
        assertTrue(loadedBear.isAggressive());
    }
    
    @Test
    public void testConsumablePersistence() {
        // Given: Create a game state with consumables
        String sessionId = "test-consumable-session";
        WorldConfig worldConfig = new WorldConfig(99999L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, 0L, world);
        
        Room room = new Room(0, 0, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room);
        
        // Add consumables
        Apple apple = new Apple();
        apple.setEnergyValue(20.0);
        room.addEntity(apple);
        
        Berry berry = new Berry();
        berry.setEnergyValue(12.0);
        room.addEntity(berry);
        
        Wood wood = new Wood();
        wood.setQuantity(3);
        room.addEntity(wood);
        
        Stone stone = new Stone();
        stone.setQuantity(2);
        room.addEntity(stone);
        
        // When: Save and load
        persistenceService.saveGameState(gameState);
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        
        // Then: Verify consumables were persisted
        assertTrue(loadedState.isPresent());
        Room loadedRoom = loadedState.get().getWorld().getRoom(0, 0);
        assertNotNull(loadedRoom);
        assertEquals(4, loadedRoom.getEntitiesList().size());
        
        // Verify apple
        Apple loadedApple = (Apple) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Apple)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedApple);
        assertEquals(20.0, loadedApple.getEnergyValue(), 0.01);
        
        // Verify berry
        Berry loadedBerry = (Berry) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Berry)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedBerry);
        assertEquals(12.0, loadedBerry.getEnergyValue(), 0.01);
        
        // Verify wood
        Wood loadedWood = (Wood) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Wood)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedWood);
        assertEquals(3, loadedWood.getQuantity());
        
        // Verify stone
        Stone loadedStone = (Stone) loadedRoom.getEntitiesList().stream()
            .filter(e -> e instanceof Stone)
            .findFirst()
            .orElse(null);
        assertNotNull(loadedStone);
        assertEquals(2, loadedStone.getQuantity());
    }
    
    @Test
    public void testMultipleEntityTypesInMultipleRooms() {
        // Given: Create a game state with multiple rooms and various entities
        String sessionId = "test-multi-room-session";
        WorldConfig worldConfig = new WorldConfig(11111L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, 0L, world);
        
        // Room 0,0 - Trees and rocks
        Room room1 = new Room(0, 0, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room1);
        Tree tree1 = new Tree();
        tree1.setHarvestCount(1);
        room1.addEntity(tree1);
        
        Rock rock1 = new Rock();
        rock1.setHarvestCount(2);
        room1.addEntity(rock1);
        
        // Room 1,1 - Animals
        Room room2 = new Room(1, 1, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room2);
        Chicken chicken = new Chicken(200L);
        chicken.setMoveSpeed(28);
        room2.addEntity(chicken);
        
        // Room -1,-1 - Bushes and berries
        Room room3 = new Room(-1, -1, worldConfig.getRoomWidth(), worldConfig.getRoomHeight());
        world.addRoom(room3);
        Bush bush = new Bush();
        bush.setHarvestCount(1);
        room3.addEntity(bush);
        
        Berry berry = new Berry();
        berry.setEnergyValue(8.0);
        room3.addEntity(berry);
        
        // When: Save and load
        persistenceService.saveGameState(gameState);
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        
        // Then: Verify all rooms and entities
        assertTrue(loadedState.isPresent());
        World loadedWorld = loadedState.get().getWorld();
        
        // Check room 0,0
        Room loadedRoom1 = loadedWorld.getRoom(0, 0);
        assertNotNull(loadedRoom1);
        assertEquals(2, loadedRoom1.getEntitiesList().size());
        assertTrue(loadedRoom1.getEntitiesList().stream().anyMatch(e -> e instanceof Tree));
        assertTrue(loadedRoom1.getEntitiesList().stream().anyMatch(e -> e instanceof Rock));
        
        // Check room 1,1
        Room loadedRoom2 = loadedWorld.getRoom(1, 1);
        assertNotNull(loadedRoom2);
        assertEquals(1, loadedRoom2.getEntitiesList().size());
        assertTrue(loadedRoom2.getEntitiesList().get(0) instanceof Chicken);
        
        // Check room -1,-1
        Room loadedRoom3 = loadedWorld.getRoom(-1, -1);
        assertNotNull(loadedRoom3);
        assertEquals(2, loadedRoom3.getEntitiesList().size());
        assertTrue(loadedRoom3.getEntitiesList().stream().anyMatch(e -> e instanceof Bush));
        assertTrue(loadedRoom3.getEntitiesList().stream().anyMatch(e -> e instanceof Berry));
    }
}
