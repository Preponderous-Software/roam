package com.preponderous.roam.service;

import com.preponderous.roam.model.Entity;
import com.preponderous.roam.model.LivingEntity;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.entity.*;
import org.springframework.stereotype.Service;

/**
 * Service for handling interactions between the player and entities.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class EntityInteractionService {
    
    /**
     * Attempt to harvest a resource from a harvestable entity (Tree, Rock, Bush).
     * 
     * @param entity the entity to harvest
     * @param player the player doing the harvesting
     * @return the harvested resource entity, or null if harvesting failed
     */
    public Entity harvestEntity(Entity entity, Player player) {
        if (entity instanceof Tree) {
            Tree tree = (Tree) entity;
            if (tree.canHarvest()) {
                tree.harvest();
                Wood wood = new Wood();
                player.getInventory().placeIntoFirstAvailableInventorySlot("Wood");
                return wood;
            }
        } else if (entity instanceof Rock) {
            Rock rock = (Rock) entity;
            if (rock.canHarvest()) {
                rock.harvest();
                Stone stone = new Stone();
                player.getInventory().placeIntoFirstAvailableInventorySlot("Stone");
                return stone;
            }
        } else if (entity instanceof Bush) {
            Bush bush = (Bush) entity;
            if (bush.canHarvest()) {
                bush.harvest();
                Berry berry = new Berry();
                player.getInventory().placeIntoFirstAvailableInventorySlot("Berry");
                return berry;
            }
        }
        return null;
    }
    
    /**
     * Attempt to gather a resource entity (Apple, Berry, Wood, Stone).
     * 
     * @param entity the entity to gather
     * @param player the player doing the gathering
     * @param room the room containing the entity
     * @return true if gathering was successful
     */
    public boolean gatherResource(Entity entity, Player player, Room room) {
        if (entity instanceof Apple) {
            boolean added = player.getInventory().placeIntoFirstAvailableInventorySlot("Apple");
            if (added) {
                room.removeEntity(entity.getId());
                return true;
            }
        } else if (entity instanceof Berry) {
            boolean added = player.getInventory().placeIntoFirstAvailableInventorySlot("Berry");
            if (added) {
                room.removeEntity(entity.getId());
                return true;
            }
        } else if (entity instanceof Wood) {
            boolean added = player.getInventory().placeIntoFirstAvailableInventorySlot("Wood");
            if (added) {
                room.removeEntity(entity.getId());
                return true;
            }
        } else if (entity instanceof Stone) {
            boolean added = player.getInventory().placeIntoFirstAvailableInventorySlot("Stone");
            if (added) {
                room.removeEntity(entity.getId());
                return true;
            }
        }
        return false;
    }
    
    /**
     * Attempt to hunt/attack a living entity (wildlife).
     * 
     * @param entity the entity to hunt
     * @param player the player doing the hunting
     * @param room the room containing the entity
     * @param damage the damage to deal
     * @return true if the entity was killed
     */
    public boolean huntEntity(LivingEntity entity, Player player, Room room, double damage) {
        entity.removeEnergy(damage);
        
        if (entity.getEnergy() <= 0) {
            // Entity is dead, drop meat/food
            if (entity instanceof Bear) {
                player.getInventory().placeIntoFirstAvailableInventorySlot("Bear Meat");
                player.getInventory().placeIntoFirstAvailableInventorySlot("Bear Meat");
                player.getInventory().placeIntoFirstAvailableInventorySlot("Bear Meat");
            } else if (entity instanceof Deer) {
                player.getInventory().placeIntoFirstAvailableInventorySlot("Deer Meat");
                player.getInventory().placeIntoFirstAvailableInventorySlot("Deer Meat");
            } else if (entity instanceof Chicken) {
                player.getInventory().placeIntoFirstAvailableInventorySlot("Chicken Meat");
            }
            
            // Remove entity from room
            room.removeEntity(entity.getId());
            return true;
        }
        
        return false;
    }
    
    /**
     * Get the entity at or near a player's position.
     * 
     * @param player the player
     * @param room the room to search
     * @return the nearest entity, or null if none found
     */
    public Entity getEntityAtPlayerPosition(Player player, Room room) {
        String playerLocationId = player.getRoomX() + "," + player.getRoomY() + "," + 
                                 player.getTileX() + "," + player.getTileY();
        
        return room.getEntitiesList().stream()
            .filter(entity -> playerLocationId.equals(entity.getLocationId()))
            .findFirst()
            .orElse(null);
    }
    
    /**
     * Get entity in front of player based on direction.
     * 
     * @param player the player
     * @param room the room to search
     * @return the entity in front of player, or null if none found
     */
    public Entity getEntityInFrontOfPlayer(Player player, Room room) {
        int direction = player.getLastDirection() != -1 ? player.getLastDirection() : 2; // Default to down
        int targetX = player.getTileX();
        int targetY = player.getTileY();
        
        switch (direction) {
            case 0: // up
                targetY--;
                break;
            case 1: // left
                targetX--;
                break;
            case 2: // down
                targetY++;
                break;
            case 3: // right
                targetX++;
                break;
        }
        
        String targetLocationId = player.getRoomX() + "," + player.getRoomY() + "," + 
                                 targetX + "," + targetY;
        
        return room.getEntitiesList().stream()
            .filter(entity -> targetLocationId.equals(entity.getLocationId()))
            .findFirst()
            .orElse(null);
    }
    
    /**
     * Get entity at a specific tile location.
     * 
     * @param roomX the room X coordinate
     * @param roomY the room Y coordinate
     * @param tileX the tile X coordinate
     * @param tileY the tile Y coordinate
     * @param room the room to search
     * @return the entity at the specified location, or null if none found
     */
    public Entity getEntityAtTile(int roomX, int roomY, int tileX, int tileY, Room room) {
        String targetLocationId = roomX + "," + roomY + "," + tileX + "," + tileY;
        
        return room.getEntitiesList().stream()
            .filter(entity -> targetLocationId.equals(entity.getLocationId()))
            .findFirst()
            .orElse(null);
    }
}
