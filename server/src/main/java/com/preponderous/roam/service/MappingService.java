package com.preponderous.roam.service;

import com.preponderous.roam.dto.*;
import com.preponderous.roam.model.*;
import com.preponderous.roam.model.entity.*;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Service for mapping between domain models and DTOs.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class MappingService {

    public SessionDTO toSessionDTO(GameState gameState) {
        SessionDTO dto = new SessionDTO();
        dto.setSessionId(gameState.getSessionId());
        dto.setOwnerId(gameState.getOwnerId());
        dto.setCurrentTick(gameState.getCurrentTick());
        
        // Map all players
        Map<String, PlayerDTO> playerDTOs = new HashMap<>();
        for (Map.Entry<String, Player> entry : gameState.getPlayers().entrySet()) {
            playerDTOs.put(entry.getKey(), toPlayerDTO(entry.getValue()));
        }
        dto.setPlayers(playerDTOs);
        
        // Set the owner's player for backward compatibility
        dto.setPlayer(playerDTOs.get(gameState.getOwnerId()));
        
        // Set multiplayer metadata
        dto.setPlayerCount(gameState.getPlayerCount());
        dto.setMaxPlayers(GameState.MAX_PLAYERS_PER_SESSION);
        dto.setFull(gameState.isFull());
        
        return dto;
    }

    public PlayerDTO toPlayerDTO(Player player) {
        PlayerDTO dto = new PlayerDTO();
        dto.setId(player.getId());
        dto.setUserId(player.getUserId());
        dto.setName(player.getName());
        dto.setEnergy(player.getEnergy());
        dto.setTargetEnergy(player.getTargetEnergy());
        dto.setDirection(player.getDirection());
        dto.setLastDirection(player.getLastDirection());
        dto.setGathering(player.isGathering());
        dto.setPlacing(player.isPlacing());
        dto.setCrouching(player.isCrouching());
        dto.setMoving(player.isMoving());
        dto.setDead(player.isDead());
        dto.setTickLastMoved(player.getTickLastMoved());
        dto.setTickLastGathered(player.getTickLastGathered());
        dto.setTickLastPlaced(player.getTickLastPlaced());
        dto.setMovementSpeed(player.getMovementSpeed());
        dto.setGatherSpeed(player.getGatherSpeed());
        dto.setPlaceSpeed(player.getPlaceSpeed());
        dto.setInventory(toInventoryDTO(player.getInventory()));
        dto.setRoomX(player.getRoomX());
        dto.setRoomY(player.getRoomY());
        dto.setTileX(player.getTileX());
        dto.setTileY(player.getTileY());
        return dto;
    }

    public InventoryDTO toInventoryDTO(Inventory inventory) {
        InventoryDTO dto = new InventoryDTO();
        
        List<InventorySlotDTO> slotDTOs = new ArrayList<>();
        for (InventorySlot slot : inventory.getInventorySlots()) {
            slotDTOs.add(toInventorySlotDTO(slot));
        }
        
        dto.setSlots(slotDTOs);
        dto.setSelectedSlotIndex(inventory.getSelectedInventorySlotIndex());
        dto.setNumFreeSlots(inventory.getNumFreeInventorySlots());
        dto.setNumTakenSlots(inventory.getNumTakenInventorySlots());
        dto.setNumItems(inventory.getNumItems());
        
        return dto;
    }

    public InventorySlotDTO toInventorySlotDTO(InventorySlot slot) {
        InventorySlotDTO dto = new InventorySlotDTO();
        dto.setItemName(slot.getItemName());
        dto.setNumItems(slot.getNumItems());
        dto.setMaxStackSize(slot.getMaxStackSize());
        dto.setEmpty(slot.isEmpty());
        return dto;
    }

    /**
     * Converts a World domain model to a WorldDTO for API responses.
     * Returns only world configuration by default to avoid very large responses.
     * For worlds with many loaded rooms, use toWorldDTOWithRooms() instead if
     * the full room list is needed.
     * 
     * @param world the World domain model to convert
     * @return a WorldDTO containing world configuration only
     */
    public WorldDTO toWorldDTO(World world) {
        WorldDTO dto = new WorldDTO();
        WorldConfig config = world.getConfig();
        
        dto.setSeed(config.getSeed());
        dto.setRoomWidth(config.getRoomWidth());
        dto.setRoomHeight(config.getRoomHeight());
        dto.setResourceDensity(config.getResourceDensity());
        dto.setHazardDensity(config.getHazardDensity());
        
        // Return only world configuration by default to avoid very large responses.
        // Call toWorldDTOWithRooms(world) explicitly if rooms should be included.
        dto.setRooms(new ArrayList<>());
        
        return dto;
    }

    /**
     * Creates a WorldDTO including all loaded rooms.
     * This method preserves the original behavior of including all rooms
     * and may result in large responses for worlds with many loaded rooms.
     * Use toWorldDTO(world) for configuration-only responses.
     * 
     * @param world the World domain model to convert
     * @return a WorldDTO containing world configuration and all loaded rooms
     */
    public WorldDTO toWorldDTOWithRooms(World world) {
        WorldDTO dto = toWorldDTO(world);
        
        List<RoomDTO> roomDTOs = world.getRooms().values().stream()
            .map(this::toRoomDTO)
            .collect(Collectors.toList());
        dto.setRooms(roomDTOs);
        
        return dto;
    }

    /**
     * Converts a Room domain model to a RoomDTO for API responses.
     * 
     * @param room the Room domain model to convert
     * @return a RoomDTO containing all room data including tiles and entities
     */
    public RoomDTO toRoomDTO(Room room) {
        RoomDTO dto = new RoomDTO();
        dto.setRoomX(room.getRoomX());
        dto.setRoomY(room.getRoomY());
        dto.setWidth(room.getWidth());
        dto.setHeight(room.getHeight());
        
        List<TileDTO> tileDTOs = new ArrayList<>();
        Tile[][] tiles = room.getTiles();
        for (int y = 0; y < room.getHeight(); y++) {
            for (int x = 0; x < room.getWidth(); x++) {
                tileDTOs.add(toTileDTO(tiles[y][x]));
            }
        }
        dto.setTiles(tileDTOs);
        
        List<EntityDTO> entityDTOs = room.getEntitiesList().stream()
            .map(this::toEntityDTO)
            .collect(Collectors.toList());
        dto.setEntities(entityDTOs);
        
        return dto;
    }

    /**
     * Converts a Tile domain model to a TileDTO for API responses.
     * 
     * @param tile the Tile domain model to convert
     * @return a TileDTO containing all tile data
     */
    public TileDTO toTileDTO(Tile tile) {
        TileDTO dto = new TileDTO();
        dto.setX(tile.getX());
        dto.setY(tile.getY());
        dto.setBiome(tile.getBiome().getDisplayName());
        dto.setBiomeColor(tile.getBiome().getColor());
        dto.setResourceType(tile.getResourceType());
        dto.setResourceAmount(tile.getResourceAmount());
        dto.setHasHazard(tile.hasHazard());
        dto.setHazardType(tile.getHazardType());
        return dto;
    }

    /**
     * Converts an Entity domain model to an EntityDTO for API responses.
     * 
     * @param entity the Entity domain model to convert
     * @return an EntityDTO containing all entity data
     */
    public EntityDTO toEntityDTO(Entity entity) {
        EntityDTO dto = new EntityDTO();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setType(entity.getClass().getSimpleName());
        dto.setImagePath(entity.getImagePath());
        dto.setLocationId(entity.getLocationId());
        dto.setSolid(entity.isSolid());
        
        // Add type-specific fields
        if (entity instanceof LivingEntity) {
            LivingEntity living = (LivingEntity) entity;
            dto.setEnergy(living.getEnergy());
            dto.setTargetEnergy(living.getTargetEnergy());
        }
        
        if (entity instanceof Tree) {
            Tree tree = (Tree) entity;
            dto.setHarvestCount(tree.getHarvestCount());
            dto.setMaxHarvestCount(tree.getMaxHarvestCount());
            dto.setCanHarvest(tree.canHarvest());
        }
        
        if (entity instanceof Rock) {
            Rock rock = (Rock) entity;
            dto.setHarvestCount(rock.getHarvestCount());
            dto.setMaxHarvestCount(rock.getMaxHarvestCount());
            dto.setCanHarvest(rock.canHarvest());
        }
        
        if (entity instanceof Bush) {
            Bush bush = (Bush) entity;
            dto.setHarvestCount(bush.getHarvestCount());
            dto.setMaxHarvestCount(bush.getMaxHarvestCount());
            dto.setCanHarvest(bush.canHarvest());
        }
        
        if (entity instanceof Apple) {
            Apple apple = (Apple) entity;
            dto.setEnergyValue(apple.getEnergyValue());
        }
        
        if (entity instanceof Berry) {
            Berry berry = (Berry) entity;
            dto.setEnergyValue(berry.getEnergyValue());
        }
        
        if (entity instanceof Wood) {
            Wood wood = (Wood) entity;
            dto.setQuantity(wood.getQuantity());
        }
        
        if (entity instanceof Stone) {
            Stone stone = (Stone) entity;
            dto.setQuantity(stone.getQuantity());
        }
        
        if (entity instanceof Bear) {
            Bear bear = (Bear) entity;
            dto.setMoveSpeed(bear.getMoveSpeed());
            dto.setAggressionRange(bear.getAggressionRange());
            dto.setAggressive(bear.isAggressive());
        }
        
        if (entity instanceof Deer) {
            Deer deer = (Deer) entity;
            dto.setMoveSpeed(deer.getMoveSpeed());
            dto.setFleeRange(deer.getFleeRange());
        }
        
        if (entity instanceof Chicken) {
            Chicken chicken = (Chicken) entity;
            dto.setMoveSpeed(chicken.getMoveSpeed());
            dto.setFleeRange(chicken.getFleeRange());
        }
        
        return dto;
    }
}
