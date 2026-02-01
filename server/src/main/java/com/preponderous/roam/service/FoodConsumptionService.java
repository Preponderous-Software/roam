package com.preponderous.roam.service;

import com.preponderous.roam.model.Entity;
import com.preponderous.roam.model.Inventory;
import com.preponderous.roam.model.InventorySlot;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.entity.Apple;
import com.preponderous.roam.model.entity.Berry;
import com.preponderous.roam.model.entity.BearMeat;
import com.preponderous.roam.model.entity.ChickenMeat;
import com.preponderous.roam.model.entity.DeerMeat;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Service for handling food consumption logic.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class FoodConsumptionService {
    private static final Logger logger = LoggerFactory.getLogger(FoodConsumptionService.class);

    /**
     * Attempt to eat food from inventory when player needs energy.
     * 
     * @param player the player
     * @return true if food was eaten, false otherwise
     */
    public boolean tryEatFromInventory(Player player) {
        if (!player.needsEnergy()) {
            return false;
        }

        Inventory inventory = player.getInventory();
        if (inventory == null) {
            return false;
        }

        // Iterate through inventory slots to find food
        for (InventorySlot slot : inventory.getInventorySlots()) {
            if (slot.isEmpty()) {
                continue;
            }

            String itemName = slot.getItemName();
            double energyValue = getEnergyValueByName(itemName);
            
            if (energyValue > 0) {
                // Found food, eat it
                player.addEnergy(energyValue);
                inventory.removeByItemName(itemName);
                logger.info("Player ate {} from inventory, gained {} energy", 
                    itemName, energyValue);
                return true;
            }
        }

        return false;
    }

    /**
     * Attempt to eat food from the current location when player needs energy.
     * 
     * @param player the player
     * @param room the room the player is in
     * @return true if food was eaten, false otherwise
     */
    public boolean tryEatFromLocation(Player player, Room room) {
        if (!player.needsEnergy()) {
            return false;
        }

        if (room == null) {
            return false;
        }

        // Get the location ID where the player is standing
        String locationId = player.getRoomX() + "," + player.getRoomY() + "," + 
                           player.getTileX() + "," + player.getTileY();

        // Look for food entities at the player's location
        List<Entity> entities = room.getEntitiesList();
        for (Entity entity : entities) {
            if (locationId.equals(entity.getLocationId())) {
                double energyValue = getEnergyValue(entity);
                
                if (energyValue > 0) {
                    // Found food, eat it
                    player.addEnergy(energyValue);
                    room.removeEntity(entity.getId());
                    logger.info("Player ate {} from location, gained {} energy", 
                        entity.getName(), energyValue);
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Get the energy value of an entity by name.
     * 
     * @param itemName the item name
     * @return energy value, or 0 if not food
     */
    private double getEnergyValueByName(String itemName) {
        if (itemName == null) {
            return 0.0;
        }
        
        switch (itemName) {
            case "Apple":
                return Apple.ENERGY_VALUE;
            case "Berry":
                return Berry.ENERGY_VALUE;
            case "Chicken Meat":
                return ChickenMeat.ENERGY_VALUE;
            case "Bear Meat":
                return BearMeat.ENERGY_VALUE;
            case "Deer Meat":
                return DeerMeat.ENERGY_VALUE;
            default:
                return 0.0;
        }
    }

    /**
     * Get the energy value of an entity.
     * 
     * @param entity the entity
     * @return energy value, or 0 if not food
     */
    private double getEnergyValue(Entity entity) {
        if (entity instanceof Apple) {
            return ((Apple) entity).getEnergyValue();
        } else if (entity instanceof Berry) {
            return ((Berry) entity).getEnergyValue();
        } else if (entity instanceof ChickenMeat) {
            return ((ChickenMeat) entity).getEnergyValue();
        } else if (entity instanceof BearMeat) {
            return ((BearMeat) entity).getEnergyValue();
        } else if (entity instanceof DeerMeat) {
            return ((DeerMeat) entity).getEnergyValue();
        }
        return 0.0;
    }

    /**
     * Check if an entity is food.
     * 
     * @param entity the entity
     * @return true if the entity is food, false otherwise
     */
    public boolean isFood(Entity entity) {
        return getEnergyValue(entity) > 0;
    }
}
