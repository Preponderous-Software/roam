package com.preponderous.roam.persistence.service;

import com.preponderous.roam.model.*;
import com.preponderous.roam.persistence.entity.*;
import com.preponderous.roam.persistence.repository.GameSessionRepository;
import com.preponderous.roam.persistence.repository.PlayerRepository;
import com.preponderous.roam.persistence.repository.RoomRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Service for persisting and loading game state from the database.
 * Handles conversion between domain models and JPA entities.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class PersistenceService {
    
    private static final Logger logger = LoggerFactory.getLogger(PersistenceService.class);
    
    @Autowired
    private GameSessionRepository sessionRepository;
    
    @Autowired
    private PlayerRepository playerRepository;
    
    @Autowired
    private RoomRepository roomRepository;
    
    /**
     * Save a game state to the database.
     */
    @Transactional
    public void saveGameState(GameState gameState) {
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
    }
    
    /**
     * Load a game state from the database.
     */
    @Transactional(readOnly = true)
    public Optional<GameState> loadGameState(String sessionId) {
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
        GameState gameState = new GameState(sessionId, sessionEntity.getCurrentTick(), world);
        
        // Load player
        Optional<PlayerEntityData> playerEntityOpt = playerRepository.findBySessionId(sessionId);
        if (playerEntityOpt.isPresent()) {
            Player player = convertToPlayer(playerEntityOpt.get());
            // Replace the default player with loaded player
            copyPlayerData(player, gameState.getPlayer());
        }
        
        logger.info("Game state loaded successfully for session: {}", sessionId);
        return Optional.of(gameState);
    }
    
    /**
     * Delete a game state from the database.
     */
    @Transactional
    public void deleteGameState(String sessionId) {
        logger.info("Deleting game state for session: {}", sessionId);
        sessionRepository.deleteById(sessionId);
        logger.info("Game state deleted successfully for session: {}", sessionId);
    }
    
    /**
     * List all saved game sessions.
     */
    @Transactional(readOnly = true)
    public List<GameSessionEntity> listAllSessions() {
        return sessionRepository.findAllByOrderByUpdatedAtDesc();
    }
    
    /**
     * Check if a session exists in the database.
     */
    @Transactional(readOnly = true)
    public boolean sessionExists(String sessionId) {
        return sessionRepository.existsById(sessionId);
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
        roomEntity.getTiles().clear();
        
        Tile[][] tiles = room.getTiles();
        for (int y = 0; y < room.getHeight(); y++) {
            for (int x = 0; x < room.getWidth(); x++) {
                Tile tile = tiles[y][x];
                TileEntity tileEntity = new TileEntity(x, y, tile.getBiome().name());
                tileEntity.setResourceType(tile.getResourceType());
                tileEntity.setResourceAmount(tile.getResourceAmount());
                tileEntity.setHasHazard(tile.hasHazard());
                tileEntity.setHazardType(tile.getHazardType());
                roomEntity.addTile(tileEntity);
            }
        }
    }
    
    private void saveEntities(Room room, RoomEntity roomEntity) {
        roomEntity.getEntities().clear();
        
        for (Entity entity : room.getEntitiesList()) {
            GameEntityData entityData = new GameEntityData(
                entity.getId(),
                entity.getClass().getSimpleName(),
                entity.getName(),
                entity.getImagePath()
            );
            entityData.setLocationId(entity.getLocationId());
            entityData.setSolid(entity.isSolid());
            
            if (entity instanceof LivingEntity) {
                LivingEntity living = (LivingEntity) entity;
                entityData.setEnergy(living.getEnergy());
                entityData.setTargetEnergy(living.getTargetEnergy());
                entityData.setTickCreated(living.getTickCreated());
                entityData.setTickLastReproduced(living.getTickLastReproduced());
            }
            
            roomEntity.addEntity(entityData);
        }
    }
    
    private Room convertToRoom(RoomEntity roomEntity) {
        Room room = new Room(roomEntity.getRoomX(), roomEntity.getRoomY(), 
                           roomEntity.getWidth(), roomEntity.getHeight());
        
        // Load tiles
        for (TileEntity tileEntity : roomEntity.getTiles()) {
            Tile tile = new Tile(tileEntity.getTileX(), tileEntity.getTileY(), 
                               Biome.valueOf(tileEntity.getBiome()));
            tile.setResourceType(tileEntity.getResourceType());
            tile.setResourceAmount(tileEntity.getResourceAmount());
            tile.setHasHazard(tileEntity.isHasHazard());
            tile.setHazardType(tileEntity.getHazardType());
            room.setTile(tile.getX(), tile.getY(), tile);
        }
        
        // Load entities - would need entity factory to recreate proper types
        // For now, this is a simplified version
        // TODO: Implement entity recreation from stored data
        
        return room;
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
        for (int i = 0; i < slotEntities.size() && i < inventory.getNumInventorySlots(); i++) {
            InventorySlotEntity slotEntity = slotEntities.get(i);
            if (slotEntity.getItemName() != null && slotEntity.getNumItems() > 0) {
                for (int j = 0; j < slotEntity.getNumItems(); j++) {
                    inventory.placeIntoFirstAvailableInventorySlot(slotEntity.getItemName());
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
