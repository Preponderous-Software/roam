package com.preponderous.roam.config;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Configuration for rate limiting using Bucket4j.
 * Provides per-user rate limiting for player actions and WebSocket messages.
 * 
 * @author Daniel McCoy Stephenson
 */
@Configuration
public class RateLimitConfig {
    
    /**
     * Bean for storing per-user rate limit buckets for player actions.
     * Limits users to 10 actions per second.
     */
    @Bean
    public Map<String, Bucket> playerActionBuckets() {
        return new ConcurrentHashMap<>();
    }
    
    /**
     * Bean for storing per-user rate limit buckets for WebSocket messages.
     * Limits users to 100 messages per second.
     */
    @Bean
    public Map<String, Bucket> webSocketMessageBuckets() {
        return new ConcurrentHashMap<>();
    }
    
    /**
     * Create a new bucket for player actions with a limit of 10 actions per second.
     */
    public static Bucket createPlayerActionBucket() {
        Bandwidth limit = Bandwidth.classic(10, Refill.intervally(10, Duration.ofSeconds(1)));
        return Bucket.builder()
                .addLimit(limit)
                .build();
    }
    
    /**
     * Create a new bucket for WebSocket messages with a limit of 100 messages per second.
     */
    public static Bucket createWebSocketMessageBucket() {
        Bandwidth limit = Bandwidth.classic(100, Refill.intervally(100, Duration.ofSeconds(1)));
        return Bucket.builder()
                .addLimit(limit)
                .build();
    }
}
