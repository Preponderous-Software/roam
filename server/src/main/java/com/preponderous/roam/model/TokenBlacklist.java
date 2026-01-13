package com.preponderous.roam.model;

import jakarta.persistence.*;
import java.time.Instant;

/**
 * Token blacklist entity for tracking revoked JWT tokens.
 * 
 * @author Daniel McCoy Stephenson
 */
@jakarta.persistence.Entity
@Table(name = "token_blacklist")
public class TokenBlacklist {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, unique = true, length = 500)
    private String token;
    
    @Column(name = "expires_at", nullable = false)
    private Instant expiresAt;
    
    @Column(name = "blacklisted_at", nullable = false, updatable = false)
    private Instant blacklistedAt;
    
    @PrePersist
    protected void onCreate() {
        blacklistedAt = Instant.now();
    }
    
    public TokenBlacklist() {
    }
    
    public TokenBlacklist(String token, Instant expiresAt) {
        this.token = token;
        this.expiresAt = expiresAt;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public Instant getExpiresAt() {
        return expiresAt;
    }

    public void setExpiresAt(Instant expiresAt) {
        this.expiresAt = expiresAt;
    }

    public Instant getBlacklistedAt() {
        return blacklistedAt;
    }

    public void setBlacklistedAt(Instant blacklistedAt) {
        this.blacklistedAt = blacklistedAt;
    }
}
