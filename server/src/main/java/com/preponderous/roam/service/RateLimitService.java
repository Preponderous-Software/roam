package com.preponderous.roam.service;

import com.preponderous.roam.config.RateLimitConfig;
import com.preponderous.roam.exception.RateLimitExceededException;
import io.github.bucket4j.Bucket;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * Service for managing rate limiting using Bucket4j.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class RateLimitService {
    
    @Autowired
    private Map<String, Bucket> playerActionBuckets;
    
    @Autowired
    private Map<String, Bucket> webSocketMessageBuckets;
    
    /**
     * Check if a player action is allowed under rate limiting.
     * If not allowed, throws RateLimitExceededException.
     * 
     * @param username the username of the player
     * @throws RateLimitExceededException if rate limit is exceeded
     */
    public void checkPlayerActionLimit(String username) {
        Bucket bucket = playerActionBuckets.computeIfAbsent(
                username, 
                k -> RateLimitConfig.createPlayerActionBucket()
        );
        
        if (!bucket.tryConsume(1)) {
            throw new RateLimitExceededException(
                    "Rate limit exceeded for player actions. Maximum 10 actions per second."
            );
        }
    }
    
    /**
     * Check if a WebSocket message is allowed under rate limiting.
     * If not allowed, throws RateLimitExceededException.
     * 
     * @param username the username of the player
     * @throws RateLimitExceededException if rate limit is exceeded
     */
    public void checkWebSocketMessageLimit(String username) {
        Bucket bucket = webSocketMessageBuckets.computeIfAbsent(
                username, 
                k -> RateLimitConfig.createWebSocketMessageBucket()
        );
        
        if (!bucket.tryConsume(1)) {
            throw new RateLimitExceededException(
                    "Rate limit exceeded for WebSocket messages. Maximum 100 messages per second."
            );
        }
    }
}
