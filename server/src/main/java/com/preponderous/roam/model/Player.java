package com.preponderous.roam.model;

import java.util.HashSet;
import java.util.Set;

/**
 * Represents a player in the game.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Player extends LivingEntity {
    public static final int DEFAULT_MOVEMENT_SPEED = 6;
    public static final int DEFAULT_GATHER_SPEED = 30;
    public static final int DEFAULT_PLACE_SPEED = 30;
    public static final double DEFAULT_PLAYER_ENERGY = 100.0;
    
    private int direction; // -1 when not moving
    private int lastDirection;
    private Inventory inventory;
    private boolean gathering;
    private boolean placing;
    private long tickLastMoved;
    private long tickLastGathered;
    private long tickLastPlaced;
    private int movementSpeed;
    private int gatherSpeed;
    private int placeSpeed;
    private boolean crouching;
    private boolean running;
    
    // Position in world space
    private int roomX;
    private int roomY;
    private int tileX;
    private int tileY;
    
    // Stats tracking
    private int score;
    private int roomsExplored;
    private int foodEaten;
    private int numberOfDeaths;
    
    // Track visited rooms for stats
    private Set<String> visitedRooms;

    public Player(long tickCreated) {
        super("Player", "assets/images/player_down.png", DEFAULT_PLAYER_ENERGY, tickCreated);
        this.direction = -1;
        this.lastDirection = -1;
        this.inventory = new Inventory();
        this.gathering = false;
        this.placing = false;
        this.tickLastMoved = -1;
        this.tickLastGathered = -1;
        this.tickLastPlaced = -1;
        this.movementSpeed = DEFAULT_MOVEMENT_SPEED;
        this.gatherSpeed = DEFAULT_GATHER_SPEED;
        this.placeSpeed = DEFAULT_PLACE_SPEED;
        this.crouching = false;
        this.running = false;
        this.setSolid(false);
        
        // Initialize player at starting position (room 0,0, center of room)
        this.roomX = 0;
        this.roomY = 0;
        this.tileX = 0;
        this.tileY = 0;
        
        // Initialize stats
        this.score = 0;
        this.roomsExplored = 1; // Start with 1 since player starts in room (0,0)
        this.foodEaten = 0;
        this.numberOfDeaths = 0;
        
        // Initialize visited rooms set with starting room
        this.visitedRooms = new HashSet<>();
        this.visitedRooms.add("0,0");
    }

    public int getDirection() {
        return direction;
    }

    public void setDirection(int direction) {
        // Validate direction: must be -1 (no movement) or 0-3 (up, left, down, right)
        if (direction < -1 || direction > 3) {
            throw new IllegalArgumentException("Direction must be -1 or 0-3, got: " + direction);
        }
        
        this.lastDirection = this.direction;
        this.direction = direction;

        if (direction == 0) {
            setImagePath("assets/images/player_up.png");
        } else if (direction == 1) {
            setImagePath("assets/images/player_left.png");
        } else if (direction == 2) {
            setImagePath("assets/images/player_down.png");
        } else if (direction == 3) {
            setImagePath("assets/images/player_right.png");
        }
    }

    public int getLastDirection() {
        return lastDirection;
    }

    public Inventory getInventory() {
        return inventory;
    }

    public void setInventory(Inventory inventory) {
        this.inventory = inventory;
    }

    public boolean isGathering() {
        return gathering;
    }

    public void setGathering(boolean gathering) {
        this.gathering = gathering;
    }

    public boolean isPlacing() {
        return placing;
    }

    public void setPlacing(boolean placing) {
        this.placing = placing;
    }

    public boolean isDead() {
        return getEnergy() < 1;
    }

    public long getTickLastMoved() {
        return tickLastMoved;
    }

    public void setTickLastMoved(long tick) {
        this.tickLastMoved = tick;
    }

    public int getMovementSpeed() {
        return movementSpeed;
    }

    public void setMovementSpeed(int newSpeed) {
        this.movementSpeed = newSpeed;
    }

    public long getTickLastGathered() {
        return tickLastGathered;
    }

    public void setTickLastGathered(long tick) {
        this.tickLastGathered = tick;
    }

    public int getGatherSpeed() {
        return gatherSpeed;
    }

    public void setGatherSpeed(int newSpeed) {
        this.gatherSpeed = newSpeed;
    }

    public long getTickLastPlaced() {
        return tickLastPlaced;
    }

    public void setTickLastPlaced(long tick) {
        this.tickLastPlaced = tick;
    }

    public int getPlaceSpeed() {
        return placeSpeed;
    }

    public void setPlaceSpeed(int newSpeed) {
        this.placeSpeed = newSpeed;
    }

    public boolean isCrouching() {
        return crouching;
    }

    public void setCrouching(boolean crouching) {
        this.crouching = crouching;
    }

    public boolean isRunning() {
        return running;
    }

    public void setRunning(boolean running) {
        this.running = running;
    }

    public boolean isMoving() {
        return direction != -1;
    }

    public int getRoomX() {
        return roomX;
    }

    public void setRoomX(int roomX) {
        this.roomX = roomX;
    }

    public int getRoomY() {
        return roomY;
    }

    public void setRoomY(int roomY) {
        this.roomY = roomY;
    }

    public int getTileX() {
        return tileX;
    }

    public void setTileX(int tileX) {
        this.tileX = tileX;
    }

    public int getTileY() {
        return tileY;
    }

    public void setTileY(int tileY) {
        this.tileY = tileY;
    }

    public int getScore() {
        return score;
    }

    public void setScore(int score) {
        this.score = score;
    }

    public void incrementScore() {
        this.score++;
    }

    public int getRoomsExplored() {
        return roomsExplored;
    }

    public void setRoomsExplored(int roomsExplored) {
        this.roomsExplored = roomsExplored;
    }

    public void incrementRoomsExplored() {
        this.roomsExplored++;
    }

    public int getFoodEaten() {
        return foodEaten;
    }

    public void setFoodEaten(int foodEaten) {
        this.foodEaten = foodEaten;
    }

    public void incrementFoodEaten() {
        this.foodEaten++;
    }

    public int getNumberOfDeaths() {
        return numberOfDeaths;
    }

    public void setNumberOfDeaths(int numberOfDeaths) {
        this.numberOfDeaths = numberOfDeaths;
    }

    public void incrementNumberOfDeaths() {
        this.numberOfDeaths++;
    }
    
    public Set<String> getVisitedRooms() {
        return visitedRooms;
    }
    
    public void setVisitedRooms(Set<String> visitedRooms) {
        this.visitedRooms = visitedRooms;
    }
    
    /**
     * Mark a room as visited. If it's a new room, increments roomsExplored.
     * 
     * @param roomX the room X coordinate
     * @param roomY the room Y coordinate
     * @return true if this is a newly visited room, false if already visited
     */
    public boolean visitRoom(int roomX, int roomY) {
        String roomKey = roomX + "," + roomY;
        boolean isNewRoom = visitedRooms.add(roomKey);
        if (isNewRoom) {
            incrementRoomsExplored();
        }
        return isNewRoom;
    }
}
