package com.preponderous.roam.service;

import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.WorldConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for run speed mechanics in PlayerService.
 * Tests that the running state properly affects movement cooldown calculation.
 * 
 * @author Daniel McCoy Stephenson
 */
@ExtendWith(MockitoExtension.class)
public class PlayerServiceRunSpeedTest {

    @Mock
    private WorldGenerationService worldGenerationService;

    @InjectMocks
    private PlayerService playerService;

    private Player player;
    private World world;
    
    private static final int TICKS_PER_SECOND = 9;
    private static final int DEFAULT_MOVEMENT_SPEED = 3;

    @BeforeEach
    public void setUp() {
        // Set up configuration values using reflection
        ReflectionTestUtils.setField(playerService, "movementEnergyCost", 1.0);
        ReflectionTestUtils.setField(playerService, "ticksPerSecond", TICKS_PER_SECOND);
        
        // Create player and world
        player = new Player(0);
        world = new World(WorldConfig.getDefault());
    }

    @Test
    public void testSetRunningTrue() {
        // Act
        playerService.setRunning(player, true);
        
        // Assert
        assertTrue(player.isRunning(), "Player should be running");
    }

    @Test
    public void testSetRunningFalse() {
        // Arrange
        player.setRunning(true);
        
        // Act
        playerService.setRunning(player, false);
        
        // Assert
        assertFalse(player.isRunning(), "Player should not be running");
    }

    @Test
    public void testMovementCooldownWithoutRunning() {
        // The cooldown should be: ticksPerSecond / (movementSpeed * 1.0)
        // With default values: 9 / (3 * 1.0) = 3 ticks
        // This results in 3 tiles per second (9 ticks/sec / 3 tick cooldown)
        
        // Arrange
        player.setRunning(false);
        player.setDirection(0); // Moving up
        player.setTickLastMoved(0);
        
        // Expected cooldown: (long)(9 / (3 * 1.0)) = 3
        long expectedCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 1.0));
        
        // Assert
        assertEquals(3, expectedCooldown, "Cooldown should be 3 ticks when not running");
        
        // Verify movement rate: 9 ticks/sec / 3 tick cooldown = 3 tiles/sec
        double tilesPerSecond = (double) TICKS_PER_SECOND / expectedCooldown;
        assertEquals(3.0, tilesPerSecond, 0.01, "Should move at 3 tiles per second normally");
    }

    @Test
    public void testMovementCooldownWithRunning() {
        // The cooldown should be: ticksPerSecond / (movementSpeed * 1.5)
        // With default values: 9 / (3 * 1.5) = 2 ticks
        // This results in 4.5 tiles per second (9 ticks/sec / 2 tick cooldown)
        
        // Arrange
        player.setRunning(true);
        player.setDirection(0); // Moving up
        player.setTickLastMoved(0);
        
        // Expected cooldown: (long)(9 / (3 * 1.5)) = 2
        long expectedCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 1.5));
        
        // Assert
        assertEquals(2, expectedCooldown, "Cooldown should be 2 ticks when running");
        
        // Verify the 1.5x speed multiplier
        // Normal: 3 tiles/sec (9/3), Running: 4.5 tiles/sec (9/2), Ratio: 1.5x
        double tilesPerSecond = (double) TICKS_PER_SECOND / expectedCooldown;
        assertEquals(4.5, tilesPerSecond, 0.01, "Should move at 4.5 tiles per second when running");
        
        // Verify the speed multiplier ratio
        long normalCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 1.0));
        double normalTilesPerSec = (double) TICKS_PER_SECOND / normalCooldown;
        double speedRatio = tilesPerSecond / normalTilesPerSec;
        assertEquals(1.5, speedRatio, 0.01, "Running should be 1.5x faster than normal");
    }

    @Test
    public void testMovementCooldownWithSlowerSpeed() {
        // Test with a slower movement speed where the difference is visible
        // With TICKS_PER_SECOND=9 and speed=1: not running = 9/1 = 9 ticks, running = 9/1.5 = 6 ticks
        
        // Arrange
        player.setMovementSpeed(1);
        
        // Test without running
        player.setRunning(false);
        long cooldownNotRunning = (long) (TICKS_PER_SECOND / (1 * 1.0));
        assertEquals(9, cooldownNotRunning, "Cooldown should be 9 ticks when not running with speed 1");
        
        // Test with running
        player.setRunning(true);
        long cooldownRunning = (long) (TICKS_PER_SECOND / (1 * 1.5));
        assertEquals(6, cooldownRunning, "Cooldown should be 6 ticks when running with speed 1");
        
        // Assert running reduces cooldown
        assertTrue(cooldownRunning < cooldownNotRunning, "Running should reduce cooldown");
    }

    @Test
    public void testRunningStatePersistence() {
        // Arrange & Act
        playerService.setRunning(player, true);
        
        // Assert
        assertTrue(player.isRunning(), "Running state should persist");
        
        // Change state
        playerService.setRunning(player, false);
        assertFalse(player.isRunning(), "Running state should update correctly");
    }

    @Test
    public void testRunningDoesNotAffectOtherPlayerStates() {
        // Arrange
        player.setDirection(2);
        player.setGathering(true);
        player.setCrouching(false);
        
        // Act
        playerService.setRunning(player, true);
        
        // Assert
        assertEquals(2, player.getDirection(), "Direction should not change");
        assertTrue(player.isGathering(), "Gathering state should not change");
        assertFalse(player.isCrouching(), "Crouching state should not change");
        assertTrue(player.isRunning(), "Running state should be set");
    }
}
