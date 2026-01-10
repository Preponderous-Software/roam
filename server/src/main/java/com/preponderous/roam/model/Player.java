package com.preponderous.roam.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents a player in the game.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Player extends LivingEntity {
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

    public Player(long tickCreated) {
        super("Player", "assets/images/player_down.png", 100, tickCreated);
        this.direction = -1;
        this.lastDirection = -1;
        this.inventory = new Inventory();
        this.gathering = false;
        this.placing = false;
        this.tickLastMoved = -1;
        this.tickLastGathered = -1;
        this.tickLastPlaced = -1;
        this.movementSpeed = 30;
        this.gatherSpeed = 30;
        this.placeSpeed = 30;
        this.crouching = false;
        this.setSolid(false);
    }

    public int getDirection() {
        return direction;
    }

    public void setDirection(int direction) {
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

    public boolean isMoving() {
        return direction != -1;
    }
}
