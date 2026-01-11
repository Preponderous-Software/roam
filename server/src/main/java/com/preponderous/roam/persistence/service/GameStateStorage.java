package com.preponderous.roam.persistence.service;

import com.preponderous.roam.model.GameState;

import java.util.List;
import java.util.Optional;

/**
 * Interface for game state storage implementations.
 * 
 * <p>This interface defines the contract for persisting and loading game state,
 * allowing different storage backends (e.g., JPA/database, JSON files, etc.) 
 * to be used interchangeably without modifying game logic.</p>
 * 
 * <h3>Implementations:</h3>
 * <ul>
 *   <li>{@link PersistenceService} - Database persistence using JPA/Hibernate</li>
 *   <li>Future: JSON file storage, cloud storage, etc.</li>
 * </ul>
 * 
 * @author Daniel McCoy Stephenson
 */
public interface GameStateStorage {
    
    /**
     * Save a game state to storage.
     * 
     * @param gameState the game state to save
     * @throws StorageException if the save operation fails
     */
    void saveGameState(GameState gameState);
    
    /**
     * Load a game state from storage.
     * 
     * @param sessionId the session ID to load
     * @return an Optional containing the game state if found, empty otherwise
     * @throws StorageException if the load operation fails
     */
    Optional<GameState> loadGameState(String sessionId);
    
    /**
     * Delete a game state from storage.
     * 
     * @param sessionId the session ID to delete
     * @throws StorageException if the delete operation fails
     */
    void deleteGameState(String sessionId);
    
    /**
     * Check if a game session exists in storage.
     * 
     * @param sessionId the session ID to check
     * @return true if the session exists, false otherwise
     * @throws StorageException if the check operation fails
     */
    boolean sessionExists(String sessionId);
    
    /**
     * List all session IDs in storage.
     * 
     * @return list of session IDs
     * @throws StorageException if the list operation fails
     */
    List<String> listAllSessionIds();
    
    /**
     * Exception thrown when storage operations fail.
     */
    class StorageException extends RuntimeException {
        public StorageException(String message) {
            super(message);
        }
        
        public StorageException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
