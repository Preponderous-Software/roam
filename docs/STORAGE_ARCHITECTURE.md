# Storage Architecture

This document describes the storage abstraction layer for the Roam game server.

## Overview

The Roam server uses an interface-based storage architecture that allows different storage backends to be used interchangeably without modifying game logic. This design enables flexibility in choosing storage solutions based on deployment requirements, performance needs, or development convenience.

## Architecture

### GameStateStorage Interface

The `GameStateStorage` interface defines the contract for all storage implementations:

```java
public interface GameStateStorage {
    void saveGameState(GameState gameState);
    Optional<GameState> loadGameState(String sessionId);
    void deleteGameState(String sessionId);
    boolean sessionExists(String sessionId);
    List<String> listAllSessionIds();
}
```

### Current Implementation

#### JPA/Hibernate Persistence (PersistenceService)

The default implementation uses JPA/Hibernate with support for:
- **PostgreSQL** (production)
- **H2** (development and testing)

**Features:**
- Full ACID transactions
- Automatic schema migrations with Flyway
- Connection pooling with HikariCP
- Complete entity persistence with ID preservation
- Automatic save/load integration

**Class:** `com.preponderous.roam.persistence.service.PersistenceService`

## Future Storage Implementations

The interface design allows for additional storage backends:

### JSON File Storage (Future)

A potential JSON-based file storage implementation would:
- Store each game session as a JSON file
- Use simple file I/O operations
- Provide fast local development without database setup
- Support easy backup/restore through file copying

**Example structure:**
```
data/
  sessions/
    {session-id-1}.json
    {session-id-2}.json
```

**Benefits:**
- No database required
- Human-readable storage format
- Easy debugging and inspection
- Simple backup/restore (copy files)
- Lightweight for development

**Implementation guidance:**
```java
@Service
@Profile("json-storage")
public class JsonFileStorageService implements GameStateStorage {
    @Override
    public void saveGameState(GameState gameState) {
        // Serialize gameState to JSON
        // Write to file: data/sessions/{sessionId}.json
    }
    
    @Override
    public Optional<GameState> loadGameState(String sessionId) {
        // Read from file: data/sessions/{sessionId}.json
        // Deserialize JSON to GameState
    }
    
    // ... other methods
}
```

### Cloud Storage (Future)

Other possible implementations:
- **AWS S3 / Azure Blob Storage:** For cloud-native deployments
- **Redis:** For high-performance caching and fast access
- **MongoDB:** For document-based storage with flexible schemas
- **Distributed databases:** For scaling across multiple servers

## Usage in Code

### Service Layer

The `GameService` class uses the `GameStateStorage` interface:

```java
@Service
public class GameService {
    @Autowired
    private GameStateStorage gameStateStorage;  // Interface, not concrete class
    
    public void saveSession(String sessionId) {
        GameState gameState = getSession(sessionId);
        if (gameState != null) {
            gameStateStorage.saveGameState(gameState);  // Works with any implementation
        }
    }
}
```

### Switching Storage Implementations

To switch storage backends:

1. **Using Spring Profiles:**
   ```bash
   # Use JPA/Hibernate (default)
   mvn spring-boot:run
   
   # Use JSON storage (when implemented)
   mvn spring-boot:run -Dspring.profiles.active=json-storage
   ```

2. **Using Configuration:**
   ```yaml
   # application.yml
   roam:
     storage:
       type: jpa  # or 'json', 'redis', etc.
   ```

3. **Programmatic Configuration:**
   ```java
   @Configuration
   public class StorageConfiguration {
       @Bean
       @ConditionalOnProperty(name = "roam.storage.type", havingValue = "jpa")
       public GameStateStorage jpaStorage() {
           return new PersistenceService();
       }
       
       @Bean
       @ConditionalOnProperty(name = "roam.storage.type", havingValue = "json")
       public GameStateStorage jsonStorage() {
           return new JsonFileStorageService();
       }
   }
   ```

## Benefits of This Architecture

### 1. **Flexibility**
- Switch storage backends without changing game logic
- Use different storage for different environments (dev vs. prod)
- Test with in-memory storage, deploy with database

### 2. **Testability**
- Mock the interface for unit tests
- Use lightweight storage for integration tests
- Test business logic independently of storage

### 3. **Maintainability**
- Clear separation of concerns
- Storage implementation details isolated
- Easy to add new storage types

### 4. **Future-Proofing**
- Support new storage technologies as they emerge
- Adapt to changing requirements without major refactoring
- Experiment with different storage solutions

## Implementation Guidelines

When implementing a new `GameStateStorage`:

1. **Implement all interface methods** - Ensure complete functionality
2. **Handle errors gracefully** - Throw `StorageException` for storage failures
3. **Maintain consistency** - Ensure save/load operations are idempotent
4. **Test thoroughly** - Write integration tests for the new implementation
5. **Document limitations** - Note any storage-specific constraints
6. **Consider performance** - Optimize for your storage backend
7. **Handle concurrency** - Ensure thread-safe operations if needed

## Error Handling

All storage implementations should throw `GameStateStorage.StorageException` for failures:

```java
try {
    // Storage operation
} catch (Exception e) {
    throw new GameStateStorage.StorageException(
        "Failed to save game state: " + sessionId, e
    );
}
```

## See Also

- [DATABASE.md](DATABASE.md) - JPA/Hibernate implementation details
- [DATABASE_IMPLEMENTATION_SUMMARY.md](DATABASE_IMPLEMENTATION_SUMMARY.md) - Database persistence architecture
- `GameStateStorage` interface JavaDoc
- `PersistenceService` class documentation
