package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents a grass resource entity.
 * Grass can be gathered from the ground and used for crafting.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Grass extends Entity {
    private int quantity;

    public Grass() {
        super("Grass", "assets/images/grass.png");
        this.quantity = 1;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates grass with specific ID.
     */
    public Grass(String id) {
        super(id, "Grass", "assets/images/grass.png");
        this.quantity = 1;
        this.setSolid(false);
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }
}
