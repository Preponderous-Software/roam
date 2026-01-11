package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents a wood resource entity.
 * Wood can be gathered from trees and used for crafting.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Wood extends Entity {
    private int quantity;

    public Wood() {
        super("Wood", "assets/images/wood.png");
        this.quantity = 1;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates wood with specific ID.
     */
    public Wood(String id) {
        super(id, "Wood", "assets/images/wood.png");
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
