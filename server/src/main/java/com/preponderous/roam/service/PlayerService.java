package com.preponderous.roam.service;

import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Service for managing player state and actions.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class PlayerService {
    
    @Autowired
    private WorldGenerationService worldGenerationService;

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
        } else if (newTileX >= currentRoom.getWidth()) {
            newRoomX++;
            newTileX = 0;
        }

        if (newTileY < 0) {
            newRoomY--;
            newTileY = worldGenerationService.getOrGenerateRoom(world, newRoomX, newRoomY, currentTick).getHeight() - 1;
        } else if (newTileY >= currentRoom.getHeight()) {
            newRoomY++;
            newTileY = 0;
        }

        // Get the destination room
        Room destinationRoom = worldGenerationService.getOrGenerateRoom(world, newRoomX, newRoomY, currentTick);

        // Check for collisions with solid entities at destination
        String destinationLocationId = newRoomX + "," + newRoomY + "," + newTileX + "," + newTileY;
        boolean blocked = destinationRoom.getEntitiesList().stream()
            .anyMatch(entity -> entity.isSolid() && 
                     destinationLocationId.equals(entity.getLocationId()));

        if (blocked) {
            return false; // Movement blocked by solid entity
        }

        // Update player position
        player.setRoomX(newRoomX);
        player.setRoomY(newRoomY);
        player.setTileX(newTileX);
        player.setTileY(newTileY);

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
}
