package com.preponderous.roam.persistence.service;

import com.preponderous.roam.model.*;
import com.preponderous.roam.model.entity.*;
import com.preponderous.roam.persistence.entity.*;
import com.preponderous.roam.persistence.repository.GameSessionRepository;
import com.preponderous.roam.persistence.repository.PlayerRepository;
import com.preponderous.roam.persistence.repository.RoomRepository;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * JPA/Hibernate implementation of game state storage.
 * Handles conversion between domain models and JPA entities for database persistence.
 * 
 * <h3>Known Limitations:</h3>
 * <ul>
 *   <li><b>Inventory Slot Preservation:</b> Inventory items are loaded sequentially which may not preserve 
 *       exact slot positions from the original state.</li>
 *   <li><b>Performance:</b> Full collection clearing and re-adding is used for saves. For large worlds, 
 *       consider implementing differential updates to only modify changed data.</li>
 * </ul>
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class PersistenceService implements GameStateStorage {
    
    private static final Logger logger = LoggerFactory.getLogger(PersistenceService.class);
    
    @Autowired
    private GameSessionRepository sessionRepository;
    
    @Autowired
    private PlayerRepository playerRepository;
    
    @Autowired
    private RoomRepository roomRepository;
    
    @PersistenceContext
    private EntityManager entityManager;
    
    /**
     * Save a game state to the database.
     */
    @Override
    @Transactional
    public void saveGameState(GameState gameState) {
        try {
            logger.info("Saving game state for session: {}", gameState.getSessionId());
            
            String sessionId = gameState.getSessionId();
            
            // Check if session already exists
            Optional<GameSessionEntity> existingSession = sessionRepository.findById(sessionId);
            GameSessionEntity sessionEntity;
            
            if (existingSession.isPresent()) {
                sessionEntity = existingSession.get();
                logger.debug("Updating existing session: {}", sessionId);
            } else {
                sessionEntity = new GameSessionEntity();
                sessionEntity.setSessionId(sessionId);
                sessionEntity.setUserId(gameState.getUserId());
                sessionEntity.setCreatedAt(LocalDateTime.now());
                logger.debug("Creating new session: {}", sessionId);
            }
            
            // Update session data
            sessionEntity.setCurrentTick(gameState.getCurrentTick());
            sessionEntity.setUpdatedAt(LocalDateTime.now());
            
            // Save world config
            WorldConfig worldConfig = gameState.getWorld().getConfig();
            sessionEntity.setWorldSeed(worldConfig.getSeed());
            sessionEntity.setWorldRoomWidth(worldConfig.getRoomWidth());
            sessionEntity.setWorldRoomHeight(worldConfig.getRoomHeight());
            sessionEntity.setWorldResourceDensity(worldConfig.getResourceDensity());
            sessionEntity.setWorldHazardDensity(worldConfig.getHazardDensity());
            
            // Save session first
            sessionEntity = sessionRepository.save(sessionEntity);
            
            // Save player
            savePlayer(gameState.getPlayer(), sessionEntity);
            
            // Save rooms
            saveRooms(gameState.getWorld(), sessionEntity);
            
            logger.info("Game state saved successfully for session: {}", sessionId);
        } catch (Exception e) {
            logger.error("Failed to save game state for session: {}", gameState.getSessionId(), e);
            throw new GameStateStorage.StorageException("Failed to save game state", e);
        }
    }
    
    /**
     * Load a game state from the database.
     */
    @Override
    @Transactional(readOnly = true)
    public Optional<GameState> loadGameState(String sessionId) {
        try {
            logger.info("Loading game state for session: {}", sessionId);
            
            Optional<GameSessionEntity> sessionEntityOpt = sessionRepository.findById(sessionId);
            if (sessionEntityOpt.isEmpty()) {
                logger.warn("Session not found: {}", sessionId);
                return Optional.empty();
            }
            
            GameSessionEntity sessionEntity = sessionEntityOpt.get();
            
            // Reconstruct world config
            WorldConfig worldConfig = new WorldConfig(
                sessionEntity.getWorldSeed(),
                sessionEntity.getWorldRoomWidth(),
                sessionEntity.getWorldRoomHeight(),
                sessionEntity.getWorldResourceDensity(),
                sessionEntity.getWorldHazardDensity()
            );
            
            // Create world
            World world = new World(worldConfig);
            
            // Load rooms
            List<RoomEntity> roomEntities = roomRepository.findBySessionId(sessionId);
            for (RoomEntity roomEntity : roomEntities) {
                Room room = convertToRoom(roomEntity);
                world.addRoom(room);
            }
            
            // Create game state
            GameState gameState = new GameState(sessionId, sessionEntity.getUserId(), sessionEntity.getCurrentTick(), world);
            
            // Load player
            Optional<PlayerEntityData> playerEntityOpt = playerRepository.findBySessionId(sessionId);
            if (playerEntityOpt.isPresent()) {
                Player player = convertToPlayer(playerEntityOpt.get());
                // Replace the default player with loaded player
                copyPlayerData(player, gameState.getPlayer());
            }
            
            logger.info("Game state loaded successfully for session: {}", sessionId);
            return Optional.of(gameState);
        } catch (Exception e) {
            logger.error("Failed to load game state for session: {}", sessionId, e);
            throw new GameStateStorage.StorageException("Failed to load game state", e);
        }
    }
    
    /**
     * Delete a game state from the database.
     */
    @Override
    @Transactional
    public void deleteGameState(String sessionId) {
        try {
            logger.info("Deleting game state for session: {}", sessionId);
            sessionRepository.deleteById(sessionId);
            logger.info("Game state deleted successfully for session: {}", sessionId);
        } catch (Exception e) {
            logger.error("Failed to delete game state for session: {}", sessionId, e);
            throw new GameStateStorage.StorageException("Failed to delete game state", e);
        }
    }
    
    /**
     * List all saved game session IDs.
     */
    @Override
    @Transactional(readOnly = true)
    public List<String> listAllSessionIds() {
        try {
            return sessionRepository.findAllByOrderByUpdatedAtDesc()
                    .stream()
                    .map(GameSessionEntity::getSessionId)
                    .toList();
        } catch (Exception e) {
            logger.error("Failed to list session IDs", e);
            throw new GameStateStorage.StorageException("Failed to list session IDs", e);
        }
    }
    
    /**
     * List all saved game sessions with metadata.
     * This method is specific to JPA implementation and provides additional session details.
     */
    @Transactional(readOnly = true)
    public List<GameSessionEntity> listAllSessions() {
        return sessionRepository.findAllByOrderByUpdatedAtDesc();
    }
    
    /**
     * Check if a session exists in the database.
     */
    @Override
    @Transactional(readOnly = true)
    public boolean sessionExists(String sessionId) {
        try {
            return sessionRepository.existsById(sessionId);
        } catch (Exception e) {
            logger.error("Failed to check if session exists: {}", sessionId, e);
            throw new GameStateStorage.StorageException("Failed to check if session exists", e);
        }
    }
    
    // Private helper methods
    
    private void savePlayer(Player player, GameSessionEntity sessionEntity) {
        Optional<PlayerEntityData> existingPlayer = playerRepository.findBySessionId(sessionEntity.getSessionId());
        PlayerEntityData playerEntity;
        
        if (existingPlayer.isPresent()) {
            playerEntity = existingPlayer.get();
        } else {
            playerEntity = new PlayerEntityData();
            playerEntity.setId(player.getId());
            playerEntity.setSession(sessionEntity);
        }
        
        // Update player data
        playerEntity.setName(player.getName());
        playerEntity.setImagePath(player.getImagePath());
        playerEntity.setEnergy(player.getEnergy());
        playerEntity.setTargetEnergy(player.getTargetEnergy());
        playerEntity.setTickCreated(player.getTickCreated());
        playerEntity.setDirection(player.getDirection());
        playerEntity.setLastDirection(player.getLastDirection());
        playerEntity.setGathering(player.isGathering());
        playerEntity.setPlacing(player.isPlacing());
        playerEntity.setCrouching(player.isCrouching());
        playerEntity.setTickLastMoved(player.getTickLastMoved());
        playerEntity.setTickLastGathered(player.getTickLastGathered());
        playerEntity.setTickLastPlaced(player.getTickLastPlaced());
        playerEntity.setMovementSpeed(player.getMovementSpeed());
        playerEntity.setGatherSpeed(player.getGatherSpeed());
        playerEntity.setPlaceSpeed(player.getPlaceSpeed());
        playerEntity.setRoomX(player.getRoomX());
        playerEntity.setRoomY(player.getRoomY());
        playerEntity.setTileX(player.getTileX());
        playerEntity.setTileY(player.getTileY());
        playerEntity.setSelectedInventorySlotIndex(player.getInventory().getSelectedInventorySlotIndex());
        
        playerEntity = playerRepository.save(playerEntity);
        
        // Save inventory
        saveInventory(player.getInventory(), playerEntity);
    }
    
    private void saveInventory(Inventory inventory, PlayerEntityData playerEntity) {
        // Clear existing inventory slots
        playerEntity.getInventorySlots().clear();
        
        // Save new inventory slots
        List<InventorySlot> slots = inventory.getInventorySlots();
        for (int i = 0; i < slots.size(); i++) {
            InventorySlot slot = slots.get(i);
            InventorySlotEntity slotEntity = new InventorySlotEntity();
            slotEntity.setPlayer(playerEntity);
            slotEntity.setSlotIndex(i);
            slotEntity.setItemName(slot.getItemName());
            slotEntity.setNumItems(slot.getNumItems());
            slotEntity.setMaxStackSize(slot.getMaxStackSize());
            playerEntity.addInventorySlot(slotEntity);
        }
    }
    
    private void saveRooms(World world, GameSessionEntity sessionEntity) {
        // Get existing rooms for this session
        List<RoomEntity> existingRooms = roomRepository.findBySessionId(sessionEntity.getSessionId());
        
        // Save all loaded rooms
        for (Room room : world.getRooms().values()) {
            saveRoom(room, sessionEntity, existingRooms);
        }
    }
    
    private void saveRoom(Room room, GameSessionEntity sessionEntity, List<RoomEntity> existingRooms) {
        // Find existing room or create new
        RoomEntity roomEntity = existingRooms.stream()
            .filter(r -> r.getRoomX() == room.getRoomX() && r.getRoomY() == room.getRoomY())
            .findFirst()
            .orElse(new RoomEntity(room.getRoomX(), room.getRoomY(), room.getWidth(), room.getHeight()));
        
        roomEntity.setSession(sessionEntity);
        roomEntity = roomRepository.save(roomEntity);
        
        // Save tiles
        saveTiles(room, roomEntity);
        
        // Save entities
        saveEntities(room, roomEntity);
    }
    
    private void saveTiles(Room room, RoomEntity roomEntity) {
        // Clear existing tiles and flush deletions before inserting new ones
        // This is necessary due to the unique constraint on (room_id, tile_x, tile_y)
        roomEntity.getTiles().clear();
        entityManager.flush();  // Ensure deletions are executed before insertions
        
        Tile[][] tiles = room.getTiles();
        List<TileEntity> newTiles = new ArrayList<>();
        for (int y = 0; y < room.getHeight(); y++) {
            for (int x = 0; x < room.getWidth(); x++) {
                Tile tile = tiles[y][x];
                TileEntity tileEntity = new TileEntity(x, y, tile.getBiome().name());
                tileEntity.setResourceType(tile.getResourceType());
                tileEntity.setResourceAmount(tile.getResourceAmount());
                tileEntity.setHasHazard(tile.hasHazard());
                tileEntity.setHazardType(tile.getHazardType());
                tileEntity.setRoom(roomEntity);
                newTiles.add(tileEntity);
            }
        }
        // Batch add new tiles to reduce individual addTile calls
        roomEntity.getTiles().addAll(newTiles);
    }
    
    private void saveEntities(Room room, RoomEntity roomEntity) {
        // Clear existing entities and flush deletions before inserting new ones
        roomEntity.getEntities().clear();
        entityManager.flush();  // Ensure deletions are executed before insertions
        
        List<GameEntityData> newEntities = new ArrayList<>();
        for (Entity entity : room.getEntitiesList()) {
            GameEntityData entityData = new GameEntityData(
                entity.getId(),
                entity.getClass().getSimpleName(),
                entity.getName(),
                entity.getImagePath()
            );
            entityData.setLocationId(entity.getLocationId());
            entityData.setSolid(entity.isSolid());
            
            // Save LivingEntity fields
            if (entity instanceof LivingEntity) {
                LivingEntity living = (LivingEntity) entity;
                entityData.setEnergy(living.getEnergy());
                entityData.setTargetEnergy(living.getTargetEnergy());
                entityData.setTickCreated(living.getTickCreated());
                entityData.setTickLastReproduced(living.getTickLastReproduced());
            }
            
            // Save entity-specific fields based on type
            if (entity instanceof Tree) {
                Tree tree = (Tree) entity;
                entityData.setHarvestCount(tree.getHarvestCount());
                entityData.setMaxHarvestCount(tree.getMaxHarvestCount());
            } else if (entity instanceof Rock) {
                Rock rock = (Rock) entity;
                entityData.setHarvestCount(rock.getHarvestCount());
                entityData.setMaxHarvestCount(rock.getMaxHarvestCount());
            } else if (entity instanceof Bush) {
                Bush bush = (Bush) entity;
                entityData.setHarvestCount(bush.getHarvestCount());
                entityData.setMaxHarvestCount(bush.getMaxHarvestCount());
            } else if (entity instanceof Apple) {
                Apple apple = (Apple) entity;
                entityData.setEnergyValue(apple.getEnergyValue());
            } else if (entity instanceof Berry) {
                Berry berry = (Berry) entity;
                entityData.setEnergyValue(berry.getEnergyValue());
            } else if (entity instanceof Wood) {
                Wood wood = (Wood) entity;
                entityData.setQuantity(wood.getQuantity());
            } else if (entity instanceof Stone) {
                Stone stone = (Stone) entity;
                entityData.setQuantity(stone.getQuantity());
            } else if (entity instanceof Deer) {
                Deer deer = (Deer) entity;
                entityData.setMoveSpeed(deer.getMoveSpeed());
                entityData.setFleeRange(deer.getFleeRange());
            } else if (entity instanceof Bear) {
                Bear bear = (Bear) entity;
                entityData.setMoveSpeed(bear.getMoveSpeed());
                entityData.setAggressionRange(bear.getAggressionRange());
                entityData.setAggressive(bear.isAggressive());
            } else if (entity instanceof Chicken) {
                Chicken chicken = (Chicken) entity;
                entityData.setMoveSpeed(chicken.getMoveSpeed());
                entityData.setFleeRange(chicken.getFleeRange());
            }
            
            entityData.setRoom(roomEntity);
            newEntities.add(entityData);
        }
        roomEntity.getEntities().addAll(newEntities);
    }
    
    private Room convertToRoom(RoomEntity roomEntity) {
        Room room = new Room(roomEntity.getRoomX(), roomEntity.getRoomY(), 
                           roomEntity.getWidth(), roomEntity.getHeight());
        
        // Load tiles
        for (TileEntity tileEntity : roomEntity.getTiles()) {
            try {
                Tile tile = new Tile(tileEntity.getTileX(), tileEntity.getTileY(), 
                                   Biome.valueOf(tileEntity.getBiome()));
                tile.setResourceType(tileEntity.getResourceType());
                tile.setResourceAmount(tileEntity.getResourceAmount());
                tile.setHasHazard(tileEntity.isHasHazard());
                tile.setHazardType(tileEntity.getHazardType());
                room.setTile(tile.getX(), tile.getY(), tile);
            } catch (IllegalArgumentException e) {
                logger.error("Invalid biome value '{}' for tile at ({}, {}) in room ({}, {}). Skipping tile.", 
                           tileEntity.getBiome(), tileEntity.getTileX(), tileEntity.getTileY(),
                           room.getRoomX(), room.getRoomY());
            }
        }
        
        // Load entities from database
        for (GameEntityData entityData : roomEntity.getEntities()) {
            Entity entity = recreateEntity(entityData);
            if (entity != null) {
                entity.setLocationId(entityData.getLocationId());
                entity.setSolid(entityData.isSolid());
                room.addEntity(entity);
            }
        }
        
        return room;
    }
    
    /**
     * Recreate an entity from stored data based on its type.
     * Preserves the original entity ID.
     */
    private Entity recreateEntity(GameEntityData data) {
        String entityType = data.getEntityType();
        String id = data.getEntityId();
        
        try {
            switch (entityType) {
                case "Tree":
                    Tree tree = new Tree(id);
                    if (data.getHarvestCount() != null) tree.setHarvestCount(data.getHarvestCount());
                    if (data.getMaxHarvestCount() != null) tree.setMaxHarvestCount(data.getMaxHarvestCount());
                    return tree;
                    
                case "Rock":
                    Rock rock = new Rock(id);
                    if (data.getHarvestCount() != null) rock.setHarvestCount(data.getHarvestCount());
                    if (data.getMaxHarvestCount() != null) rock.setMaxHarvestCount(data.getMaxHarvestCount());
                    return rock;
                    
                case "Bush":
                    Bush bush = new Bush(id);
                    if (data.getHarvestCount() != null) bush.setHarvestCount(data.getHarvestCount());
                    if (data.getMaxHarvestCount() != null) bush.setMaxHarvestCount(data.getMaxHarvestCount());
                    return bush;
                    
                case "Apple":
                    Apple apple = new Apple(id);
                    if (data.getEnergyValue() != null) apple.setEnergyValue(data.getEnergyValue());
                    return apple;
                    
                case "Berry":
                    Berry berry = new Berry(id);
                    if (data.getEnergyValue() != null) berry.setEnergyValue(data.getEnergyValue());
                    return berry;
                    
                case "Chicken Meat":
                    ChickenMeat chickenMeat = new ChickenMeat(id);
                    if (data.getEnergyValue() != null) chickenMeat.setEnergyValue(data.getEnergyValue());
                    return chickenMeat;
                    
                case "Bear Meat":
                    BearMeat bearMeat = new BearMeat(id);
                    if (data.getEnergyValue() != null) bearMeat.setEnergyValue(data.getEnergyValue());
                    return bearMeat;
                    
                case "Deer Meat":
                    DeerMeat deerMeat = new DeerMeat(id);
                    if (data.getEnergyValue() != null) deerMeat.setEnergyValue(data.getEnergyValue());
                    return deerMeat;
                    
                case "Wood":
                    Wood wood = new Wood(id);
                    if (data.getQuantity() != null) wood.setQuantity(data.getQuantity());
                    return wood;
                    
                case "Stone":
                    Stone stone = new Stone(id);
                    if (data.getQuantity() != null) stone.setQuantity(data.getQuantity());
                    return stone;
                    
                case "Deer":
                    long tickCreated = data.getTickCreated() != null ? data.getTickCreated() : 0L;
                    Deer deer = new Deer(id, tickCreated);
                    if (data.getEnergy() != null) deer.setEnergy(data.getEnergy());
                    if (data.getTargetEnergy() != null) deer.setTargetEnergy(data.getTargetEnergy());
                    if (data.getTickLastReproduced() != null) deer.setTickLastReproduced(data.getTickLastReproduced());
                    if (data.getMoveSpeed() != null) deer.setMoveSpeed(data.getMoveSpeed());
                    if (data.getFleeRange() != null) deer.setFleeRange(data.getFleeRange());
                    return deer;
                    
                case "Bear":
                    tickCreated = data.getTickCreated() != null ? data.getTickCreated() : 0L;
                    Bear bear = new Bear(id, tickCreated);
                    if (data.getEnergy() != null) bear.setEnergy(data.getEnergy());
                    if (data.getTargetEnergy() != null) bear.setTargetEnergy(data.getTargetEnergy());
                    if (data.getTickLastReproduced() != null) bear.setTickLastReproduced(data.getTickLastReproduced());
                    if (data.getMoveSpeed() != null) bear.setMoveSpeed(data.getMoveSpeed());
                    if (data.getAggressionRange() != null) bear.setAggressionRange(data.getAggressionRange());
                    if (data.getAggressive() != null) bear.setAggressive(data.getAggressive());
                    return bear;
                    
                case "Chicken":
                    tickCreated = data.getTickCreated() != null ? data.getTickCreated() : 0L;
                    Chicken chicken = new Chicken(id, tickCreated);
                    if (data.getEnergy() != null) chicken.setEnergy(data.getEnergy());
                    if (data.getTargetEnergy() != null) chicken.setTargetEnergy(data.getTargetEnergy());
                    if (data.getTickLastReproduced() != null) chicken.setTickLastReproduced(data.getTickLastReproduced());
                    if (data.getMoveSpeed() != null) chicken.setMoveSpeed(data.getMoveSpeed());
                    if (data.getFleeRange() != null) chicken.setFleeRange(data.getFleeRange());
                    return chicken;
                    
                default:
                    logger.warn("Unknown entity type: {}. Entity will not be loaded.", entityType);
                    return null;
            }
        } catch (Exception e) {
            logger.error("Error recreating entity of type {}: {}", entityType, e.getMessage());
            return null;
        }
    }
    
    private Player convertToPlayer(PlayerEntityData playerEntity) {
        Player player = new Player(playerEntity.getTickCreated());
        player.setEnergy(playerEntity.getEnergy());
        player.setTargetEnergy(playerEntity.getTargetEnergy());
        player.setDirection(playerEntity.getDirection());
        player.setGathering(playerEntity.isGathering());
        player.setPlacing(playerEntity.isPlacing());
        player.setCrouching(playerEntity.isCrouching());
        player.setTickLastMoved(playerEntity.getTickLastMoved());
        player.setTickLastGathered(playerEntity.getTickLastGathered());
        player.setTickLastPlaced(playerEntity.getTickLastPlaced());
        player.setMovementSpeed(playerEntity.getMovementSpeed());
        player.setGatherSpeed(playerEntity.getGatherSpeed());
        player.setPlaceSpeed(playerEntity.getPlaceSpeed());
        player.setRoomX(playerEntity.getRoomX());
        player.setRoomY(playerEntity.getRoomY());
        player.setTileX(playerEntity.getTileX());
        player.setTileY(playerEntity.getTileY());
        
        // Load inventory
        Inventory inventory = new Inventory();
        List<InventorySlotEntity> slotEntities = playerEntity.getInventorySlots();
        for (InventorySlotEntity slotEntity : slotEntities) {
            if (slotEntity.getItemName() != null && slotEntity.getNumItems() > 0) {
                // Place items in their original slot positions
                int slotIndex = slotEntity.getSlotIndex();
                for (int j = 0; j < slotEntity.getNumItems(); j++) {
                    if (!inventory.placeIntoSlot(slotIndex, slotEntity.getItemName())) {
                        // Fallback to first available slot if original slot can't accommodate
                        inventory.placeIntoFirstAvailableInventorySlot(slotEntity.getItemName());
                    }
                }
            }
        }
        inventory.setSelectedInventorySlotIndex(playerEntity.getSelectedInventorySlotIndex());
        player.setInventory(inventory);
        
        return player;
    }
    
    private void copyPlayerData(Player source, Player target) {
        target.setEnergy(source.getEnergy());
        target.setTargetEnergy(source.getTargetEnergy());
        target.setDirection(source.getDirection());
        target.setGathering(source.isGathering());
        target.setPlacing(source.isPlacing());
        target.setCrouching(source.isCrouching());
        target.setTickLastMoved(source.getTickLastMoved());
        target.setTickLastGathered(source.getTickLastGathered());
        target.setTickLastPlaced(source.getTickLastPlaced());
        target.setMovementSpeed(source.getMovementSpeed());
        target.setGatherSpeed(source.getGatherSpeed());
        target.setPlaceSpeed(source.getPlaceSpeed());
        target.setRoomX(source.getRoomX());
        target.setRoomY(source.getRoomY());
        target.setTileX(source.getTileX());
        target.setTileY(source.getTileY());
        target.setInventory(source.getInventory());
    }
}
