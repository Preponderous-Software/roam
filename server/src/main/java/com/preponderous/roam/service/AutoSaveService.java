package com.preponderous.roam.service;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.persistence.service.PersistenceService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Service responsible for automatic saving of game sessions.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class AutoSaveService {
    
    private static final Logger logger = LoggerFactory.getLogger(AutoSaveService.class);
    
    @Autowired
    private GameService gameService;
    
    @Autowired
    private PersistenceService persistenceService;
    
    @Value("${roam.persistence.auto-save:false}")
    private boolean autoSaveEnabled;
    
    /**
     * Auto-save all active sessions periodically.
     * Rate is controlled by roam.persistence.auto-save-interval property (default 30 seconds).
     */
    @Scheduled(fixedRateString = "${roam.persistence.auto-save-interval:30000}")
    public void autoSaveAllSessions() {
        if (!autoSaveEnabled) {
            return;
        }
        
        Map<String, GameState> activeSessions = gameService.getActiveSessions();
        
        if (activeSessions.isEmpty()) {
            logger.debug("No active sessions to auto-save");
            return;
        }
        
        logger.info("Starting auto-save for {} active session(s)", activeSessions.size());
        
        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger failureCount = new AtomicInteger(0);
        
        activeSessions.values().forEach(session -> {
            try {
                persistenceService.saveGameState(session);
                successCount.incrementAndGet();
                logger.debug("Auto-saved session: {}", session.getSessionId());
            } catch (Exception e) {
                failureCount.incrementAndGet();
                logger.error("Auto-save failed for session {}: {}", 
                    session.getSessionId(), e.getMessage());
                
                // Retry once on failure
                try {
                    Thread.sleep(1000); // Wait 1 second before retry
                    persistenceService.saveGameState(session);
                    successCount.incrementAndGet();
                    failureCount.decrementAndGet();
                    logger.info("Auto-save retry succeeded for session: {}", session.getSessionId());
                } catch (Exception retryException) {
                    logger.error("Auto-save retry failed for session {}: {}", 
                        session.getSessionId(), retryException.getMessage());
                }
            }
        });
        
        if (failureCount.get() > 0) {
            logger.warn("Auto-save completed: {} succeeded, {} failed", 
                successCount.get(), failureCount.get());
        } else {
            logger.info("Auto-save completed successfully for {} session(s)", 
                successCount.get());
        }
    }
    
    /**
     * Save all active sessions immediately.
     * Used for graceful shutdown.
     * 
     * @return Number of sessions successfully saved
     */
    public int saveAllSessionsNow() {
        Map<String, GameState> activeSessions = gameService.getActiveSessions();
        
        if (activeSessions.isEmpty()) {
            logger.info("No active sessions to save during shutdown");
            return 0;
        }
        
        logger.info("Saving {} active session(s) during shutdown", activeSessions.size());
        
        AtomicInteger successCount = new AtomicInteger(0);
        
        activeSessions.values().forEach(session -> {
            try {
                persistenceService.saveGameState(session);
                successCount.incrementAndGet();
                logger.info("Saved session during shutdown: {}", session.getSessionId());
            } catch (Exception e) {
                logger.error("Failed to save session {} during shutdown: {}", 
                    session.getSessionId(), e.getMessage(), e);
            }
        });
        
        logger.info("Shutdown save completed: {} of {} session(s) saved successfully", 
            successCount.get(), activeSessions.size());
        
        return successCount.get();
    }
}
