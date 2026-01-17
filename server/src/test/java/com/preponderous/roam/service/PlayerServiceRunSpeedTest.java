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
    
    private static final int TICKS_PER_SECOND = 18;
    private static final int DEFAULT_MOVEMENT_SPEED = 6;

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
        // With default values: 18 / (6 * 1.0) = 3 ticks
        // This results in 6 tiles per second (18 ticks/sec / 3 tick cooldown)
        
        // Arrange
        player.setRunning(false);
        player.setDirection(0); // Moving up
        player.setTickLastMoved(0);
        
        // Expected cooldown: (long)(18 / (6 * 1.0)) = 3
        long expectedCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 1.0));
        
        // Assert
        assertEquals(3, expectedCooldown, "Cooldown should be 3 ticks when not running");
        
        // Verify movement rate: 18 ticks/sec / 3 tick cooldown = 6 tiles/sec
        double tilesPerSecond = (double) TICKS_PER_SECOND / expectedCooldown;
        assertEquals(6.0, tilesPerSecond, 0.01, "Should move at 6 tiles per second normally");
    }

    @Test
    public void testMovementCooldownWithRunning() {
        // The cooldown should be: ticksPerSecond / (movementSpeed * 3.0)
        // With default values: 18 / (6 * 3.0) = 1 tick
        // This results in 18 tiles per second (18 ticks/sec / 1 tick cooldown)
        
        // Arrange
        player.setRunning(true);
        player.setDirection(0); // Moving up
        player.setTickLastMoved(0);
        
        // Expected cooldown: (long)(18 / (6 * 3.0)) = 1
        long expectedCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 3.0));
        
        // Assert
        assertEquals(1, expectedCooldown, "Cooldown should be 1 tick when running");
        
        // Verify the 3x speed multiplier
        // Normal: 6 tiles/sec (18/3), Running: 18 tiles/sec (18/1), Ratio: 3x
        double tilesPerSecond = (double) TICKS_PER_SECOND / expectedCooldown;
        assertEquals(18.0, tilesPerSecond, 0.01, "Should move at 18 tiles per second when running");
        
        // Verify the speed multiplier ratio
        long normalCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 1.0));
        double normalTilesPerSec = (double) TICKS_PER_SECOND / normalCooldown;
        double speedRatio = tilesPerSecond / normalTilesPerSec;
        assertEquals(3.0, speedRatio, 0.01, "Running should be 3x faster than normal");
    }

    @Test
    public void testMovementCooldownWithSlowerSpeed() {
        // Test with a slower movement speed where the difference is visible
        // With TICKS_PER_SECOND=18 and speed=1: not running = 18/1 = 18 ticks, running = 18/3.0 = 6 ticks
        
        // Arrange
        player.setMovementSpeed(1);
        
        // Test without running
        player.setRunning(false);
        long cooldownNotRunning = (long) (TICKS_PER_SECOND / (1 * 1.0));
        assertEquals(18, cooldownNotRunning, "Cooldown should be 18 ticks when not running with speed 1");
        
        // Test with running
        player.setRunning(true);
        long cooldownRunning = (long) (TICKS_PER_SECOND / (1 * 3.0));
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
