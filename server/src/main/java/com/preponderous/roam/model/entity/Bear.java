package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.LivingEntity;

/**
 * Represents a bear wildlife entity.
 * Bears are aggressive predators with high health.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Bear extends LivingEntity {
    public static final double DEFAULT_ENERGY = 80.0;
    public static final int DEFAULT_MOVE_SPEED = 20;
    public static final double AGGRESSION_RANGE = 5.0;
    
    private int moveSpeed;
    private double aggressionRange;
    private boolean aggressive;

    public Bear(long tickCreated) {
        super("Bear", "assets/images/bear.png", DEFAULT_ENERGY, tickCreated);
        this.moveSpeed = DEFAULT_MOVE_SPEED;
        this.aggressionRange = AGGRESSION_RANGE;
        this.aggressive = true;
        this.setSolid(true);
    }
    
    /**
     * Constructor for persistence - creates bear with specific ID.
     */
    public Bear(String id, long tickCreated) {
        super(id, "Bear", "assets/images/bear.png", DEFAULT_ENERGY, tickCreated);
        this.moveSpeed = DEFAULT_MOVE_SPEED;
        this.aggressionRange = AGGRESSION_RANGE;
        this.aggressive = true;
        this.setSolid(true);
    }

    public int getMoveSpeed() {
        return moveSpeed;
    }

    public void setMoveSpeed(int moveSpeed) {
        this.moveSpeed = moveSpeed;
    }

    public double getAggressionRange() {
        return aggressionRange;
    }

    public void setAggressionRange(double aggressionRange) {
        this.aggressionRange = aggressionRange;
    }

    public boolean isAggressive() {
        return aggressive;
    }

    public void setAggressive(boolean aggressive) {
        this.aggressive = aggressive;
    }
}
