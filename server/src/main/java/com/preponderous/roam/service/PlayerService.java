package com.preponderous.roam.service;

import com.preponderous.roam.dto.websocket.PlayerPositionUpdate;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import com.preponderous.roam.websocket.WebSocketMessageService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Service for managing player state and actions.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class PlayerService {
    private static final Logger logger = LoggerFactory.getLogger(PlayerService.class);
    
    @Autowired
    private WorldGenerationService worldGenerationService;
    
    @Autowired(required = false)
    private WebSocketMessageService webSocketMessageService;
    
    @org.springframework.beans.factory.annotation.Value("${roam.gameplay.movement-energy-cost:1.0}")
    private double movementEnergyCost;

    @org.springframework.beans.factory.annotation.Value("${roam.gameplay.ticks-per-second:3}")
    private int ticksPerSecond;

    /**
     * Update player direction.
     */
    public void setDirection(Player player, int direction) {
        player.setDirection(direction);
    }

    /**
     * Update player gathering state.
     */
    public void setGathering(Player player, boolean gathering) {
        player.setGathering(gathering);
    }

    /**
     * Update player placing state.
     */
    public void setPlacing(Player player, boolean placing) {
        player.setPlacing(placing);
    }

    /**
     * Update player crouching state.
     */
    public void setCrouching(Player player, boolean crouching) {
        player.setCrouching(crouching);
    }

    /**
     * Update player running state.
     */
    public void setRunning(Player player, boolean running) {
        player.setRunning(running);
    }

    /**
     * Add energy to player.
     */
    public void addEnergy(Player player, double amount) {
        player.addEnergy(amount);
    }

    /**
     * Remove energy from player.
     */
    public void removeEnergy(Player player, double amount) {
        player.removeEnergy(amount);
    }

    /**
     * Update player tick last moved.
     */
    public void setTickLastMoved(Player player, long tick) {
        player.setTickLastMoved(tick);
    }

    /**
     * Update player tick last gathered.
     */
    public void setTickLastGathered(Player player, long tick) {
        player.setTickLastGathered(tick);
    }

    /**
     * Update player tick last placed.
     */
    public void setTickLastPlaced(Player player, long tick) {
        player.setTickLastPlaced(tick);
    }

    /**
     * Set player movement speed.
     */
    public void setMovementSpeed(Player player, int speed) {
        player.setMovementSpeed(speed);
    }

    /**
     * Set player gather speed.
     */
    public void setGatherSpeed(Player player, int speed) {
        player.setGatherSpeed(speed);
    }

    /**
     * Set player place speed.
     */
    public void setPlaceSpeed(Player player, int speed) {
        player.setPlaceSpeed(speed);
    }

    /**
     * Move player in a direction, handling room transitions and collisions.
     * Direction: 0=up, 1=left, 2=down, 3=right
     * 
     * Applies movement speed cooldown based on player's movement speed and running state.
     * When running, speed multiplier of 1.5x is applied.
     * 
     * @param player the player to move
     * @param world the world containing rooms
     * @param currentTick current game tick for room generation
     * @return true if movement was successful, false if blocked
     */
    public boolean movePlayer(Player player, World world, long currentTick) {
        int direction = player.getDirection();
        if (direction == -1) {
            return false; // Not moving
        }

        // Calculate movement cooldown based on speed and running state
        double speedMultiplier = player.isRunning() ? 1.5 : 1.0;
        long cooldown = (long) (ticksPerSecond / (player.getMovementSpeed() * speedMultiplier));
        
        // Check if still on cooldown
        if (currentTick < player.getTickLastMoved() + cooldown) {
            return false; // Still on cooldown
        }

        int currentRoomX = player.getRoomX();
        int currentRoomY = player.getRoomY();
        int currentTileX = player.getTileX();
        int currentTileY = player.getTileY();

        int newRoomX = currentRoomX;
        int newRoomY = currentRoomY;
        int newTileX = currentTileX;
        int newTileY = currentTileY;

        // Calculate new position based on direction
        switch (direction) {
            case 0: // up
                newTileY--;
                break;
            case 1: // left
                newTileX--;
                break;
            case 2: // down
                newTileY++;
                break;
            case 3: // right
                newTileX++;
                break;
        }

        // Get or generate current room
        Room currentRoom = worldGenerationService.getOrGenerateRoom(world, currentRoomX, currentRoomY, currentTick);
        
        // Handle room transitions
        if (newTileX < 0) {
            newRoomX--;
            newTileX = worldGenerationService.getOrGenerateRoom(world, newRoomX, newRoomY, currentTick).getWidth() - 1;
            logger.info("Player transitioning to room ({}, {}) from west", newRoomX, newRoomY);
        } else if (newTileX >= currentRoom.getWidth()) {
            newRoomX++;
            newTileX = 0;
            logger.info("Player transitioning to room ({}, {}) from east", newRoomX, newRoomY);
        }

        if (newTileY < 0) {
            newRoomY--;
            newTileY = worldGenerationService.getOrGenerateRoom(world, newRoomX, newRoomY, currentTick).getHeight() - 1;
            logger.info("Player transitioning to room ({}, {}) from north", newRoomX, newRoomY);
        } else if (newTileY >= currentRoom.getHeight()) {
            newRoomY++;
            newTileY = 0;
            logger.info("Player transitioning to room ({}, {}) from south", newRoomX, newRoomY);
        }

        // Get the destination room
        Room destinationRoom = worldGenerationService.getOrGenerateRoom(world, newRoomX, newRoomY, currentTick);

        // Check for collisions with solid entities at destination
        String destinationLocationId = newRoomX + "," + newRoomY + "," + newTileX + "," + newTileY;
        boolean blocked = destinationRoom.getEntitiesList().stream()
            .anyMatch(entity -> entity.isSolid() && 
                     destinationLocationId.equals(entity.getLocationId()));

        if (blocked) {
            logger.debug("Player movement blocked by solid entity at ({}, {}, {}, {})", newRoomX, newRoomY, newTileX, newTileY);
            return false; // Movement blocked by solid entity
        }

        // Update player position
        logger.debug("Player moved from ({}, {}, {}, {}) to ({}, {}, {}, {})", 
                    currentRoomX, currentRoomY, currentTileX, currentTileY,
                    newRoomX, newRoomY, newTileX, newTileY);
        player.setRoomX(newRoomX);
        player.setRoomY(newRoomY);
        player.setTileX(newTileX);
        player.setTileY(newTileY);
        
        // Update tick last moved to current tick
        player.setTickLastMoved(currentTick);
        
        // Apply movement energy cost
        player.removeEnergy(movementEnergyCost);
        
        // Broadcast position update via WebSocket (sessionId provided by caller)
        // Will be called from GameService with proper sessionId

        return true;
    }

    /**
     * Set player position directly.
     * 
     * @param player the player to position
     * @param roomX room X coordinate
     * @param roomY room Y coordinate
     * @param tileX tile X coordinate within room
     * @param tileY tile Y coordinate within room
     */
    public void setPlayerPosition(Player player, int roomX, int roomY, int tileX, int tileY) {
        player.setRoomX(roomX);
        player.setRoomY(roomY);
        player.setTileX(tileX);
        player.setTileY(tileY);
    }

    /**
     * Broadcast player position update via WebSocket.
     * 
     * @param sessionId the session ID (null if not available)
     * @param player the player
     * @param username the username (null if not available)
     */
    public void broadcastPlayerPosition(String sessionId, Player player, String username) {
        if (webSocketMessageService != null && sessionId != null) {
            PlayerPositionUpdate update = new PlayerPositionUpdate();
            update.setUsername(username);
            update.setRoomX(player.getRoomX());
            update.setRoomY(player.getRoomY());
            update.setTileX(player.getTileX());
            update.setTileY(player.getTileY());
            update.setDirection(player.getDirection());
            update.setGathering(player.isGathering());
            update.setPlacing(player.isPlacing());
            update.setCrouching(player.isCrouching());
            update.setRunning(player.isRunning());
            
            webSocketMessageService.broadcastPlayerPosition(sessionId, update);
        }
    }
}
