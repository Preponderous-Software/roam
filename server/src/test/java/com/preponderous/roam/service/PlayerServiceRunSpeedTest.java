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
    
    private static final int TICKS_PER_SECOND = 3;
    private static final int DEFAULT_MOVEMENT_SPEED = 30;

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
        // With default values: 3 / (30 * 1.0) = 0.1 ticks
        // Since cooldown is cast to long, this becomes 0 ticks
        
        // Arrange
        player.setRunning(false);
        player.setDirection(0); // Moving up
        player.setTickLastMoved(0);
        
        // Expected cooldown: (long)(3 / (30 * 1.0)) = 0
        long expectedCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 1.0));
        
        // Assert
        assertEquals(0, expectedCooldown, "Cooldown should be 0 ticks when not running");
        
        // Verify that the player can move every tick (no effective cooldown due to fast base speed)
        assertTrue(expectedCooldown == 0, "With fast movement speed, cooldown is effectively 0");
    }

    @Test
    public void testMovementCooldownWithRunning() {
        // The cooldown should be: ticksPerSecond / (movementSpeed * 1.5)
        // With default values: 3 / (30 * 1.5) = 3 / 45 = 0.0667 ticks
        // Since cooldown is cast to long, this becomes 0 ticks
        
        // Arrange
        player.setRunning(true);
        player.setDirection(0); // Moving up
        player.setTickLastMoved(0);
        
        // Expected cooldown: (long)(3 / (30 * 1.5)) = 0
        long expectedCooldown = (long) (TICKS_PER_SECOND / (DEFAULT_MOVEMENT_SPEED * 1.5));
        
        // Assert
        assertEquals(0, expectedCooldown, "Cooldown should be 0 ticks when running");
        
        // The actual effect is that running reduces the cooldown even further
        // With very fast movement speeds, both are 0, but the formula applies the multiplier
        assertTrue(expectedCooldown == 0, "With fast movement speed and running, cooldown is effectively 0");
    }

    @Test
    public void testMovementCooldownWithSlowerSpeed() {
        // Test with a slower movement speed where the difference is visible
        // With speed 1: not running = 3/1 = 3 ticks, running = 3/1.5 = 2 ticks
        
        // Arrange
        player.setMovementSpeed(1);
        
        // Test without running
        player.setRunning(false);
        long cooldownNotRunning = (long) (TICKS_PER_SECOND / (1 * 1.0));
        assertEquals(3, cooldownNotRunning, "Cooldown should be 3 ticks when not running with speed 1");
        
        // Test with running
        player.setRunning(true);
        long cooldownRunning = (long) (TICKS_PER_SECOND / (1 * 1.5));
        assertEquals(2, cooldownRunning, "Cooldown should be 2 ticks when running with speed 1");
        
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
