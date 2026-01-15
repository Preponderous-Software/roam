package com.preponderous.roam.config;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * Configuration for rate limiting using Bucket4j.
 * Provides per-user rate limiting for player actions and WebSocket messages.
 * Uses Caffeine cache with automatic eviction to prevent memory leaks.
 * 
 * @author Daniel McCoy Stephenson
 */
@Configuration
public class RateLimitConfig {
    
    /**
     * Bean for storing per-user rate limit buckets for player actions.
     * Limits users to 10 actions per second.
     * Buckets are automatically evicted after 1 hour of inactivity.
     */
    @Bean
    public Cache<String, Bucket> playerActionBuckets() {
        return Caffeine.newBuilder()
                .expireAfterAccess(Duration.ofHours(1))
                .maximumSize(10000)
                .build();
    }
    
    /**
     * Bean for storing per-user rate limit buckets for WebSocket messages.
     * Limits users to 100 messages per second.
     * Buckets are automatically evicted after 1 hour of inactivity.
     */
    @Bean
    public Cache<String, Bucket> webSocketMessageBuckets() {
        return Caffeine.newBuilder()
                .expireAfterAccess(Duration.ofHours(1))
                .maximumSize(10000)
                .build();
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
