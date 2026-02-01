package com.preponderous.roam.dto;

/**
 * DTO for player state information.
 * 
 * @author Daniel McCoy Stephenson
 */
public class PlayerDTO {
    private String id;
    private String name;
    private double energy;
    private double targetEnergy;
    private int direction;
    private int lastDirection;
    private boolean gathering;
    private boolean placing;
    private boolean crouching;
    private boolean running;
    private boolean moving;
    private boolean dead;
    private long tickLastMoved;
    private long tickLastGathered;
    private long tickLastPlaced;
    private int movementSpeed;
    private int gatherSpeed;
    private int placeSpeed;
    private InventoryDTO inventory;
    
    // Position in world space
    private int roomX;
    private int roomY;
    private int tileX;
    private int tileY;
    
    // Stats
    private int score;
    private int roomsExplored;
    private int foodEaten;
    private int numberOfDeaths;

    public PlayerDTO() {
    }

    // Getters and setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public double getEnergy() {
        return energy;
    }

    public void setEnergy(double energy) {
        this.energy = energy;
    }

    public double getTargetEnergy() {
        return targetEnergy;
    }

    public void setTargetEnergy(double targetEnergy) {
        this.targetEnergy = targetEnergy;
    }

    public int getDirection() {
        return direction;
    }

    public void setDirection(int direction) {
        this.direction = direction;
    }

    public int getLastDirection() {
        return lastDirection;
    }

    public void setLastDirection(int lastDirection) {
        this.lastDirection = lastDirection;
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
        return moving;
    }

    public void setMoving(boolean moving) {
        this.moving = moving;
    }

    public boolean isDead() {
        return dead;
    }

    public void setDead(boolean dead) {
        this.dead = dead;
    }

    public long getTickLastMoved() {
        return tickLastMoved;
    }

    public void setTickLastMoved(long tickLastMoved) {
        this.tickLastMoved = tickLastMoved;
    }

    public long getTickLastGathered() {
        return tickLastGathered;
    }

    public void setTickLastGathered(long tickLastGathered) {
        this.tickLastGathered = tickLastGathered;
    }

    public long getTickLastPlaced() {
        return tickLastPlaced;
    }

    public void setTickLastPlaced(long tickLastPlaced) {
        this.tickLastPlaced = tickLastPlaced;
    }

    public int getMovementSpeed() {
        return movementSpeed;
    }

    public void setMovementSpeed(int movementSpeed) {
        this.movementSpeed = movementSpeed;
    }

    public int getGatherSpeed() {
        return gatherSpeed;
    }

    public void setGatherSpeed(int gatherSpeed) {
        this.gatherSpeed = gatherSpeed;
    }

    public int getPlaceSpeed() {
        return placeSpeed;
    }

    public void setPlaceSpeed(int placeSpeed) {
        this.placeSpeed = placeSpeed;
    }

    public InventoryDTO getInventory() {
        return inventory;
    }

    public void setInventory(InventoryDTO inventory) {
        this.inventory = inventory;
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

    public int getRoomsExplored() {
        return roomsExplored;
    }

    public void setRoomsExplored(int roomsExplored) {
        this.roomsExplored = roomsExplored;
    }

    public int getFoodEaten() {
        return foodEaten;
    }

    public void setFoodEaten(int foodEaten) {
        this.foodEaten = foodEaten;
    }

    public int getNumberOfDeaths() {
        return numberOfDeaths;
    }

    public void setNumberOfDeaths(int numberOfDeaths) {
        this.numberOfDeaths = numberOfDeaths;
    }
}
