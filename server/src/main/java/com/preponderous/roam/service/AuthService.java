package com.preponderous.roam.service;

import com.preponderous.roam.dto.AuthResponse;
import com.preponderous.roam.dto.LoginRequest;
import com.preponderous.roam.dto.RefreshTokenRequest;
import com.preponderous.roam.dto.RegisterRequest;
import com.preponderous.roam.model.RefreshToken;
import com.preponderous.roam.model.TokenBlacklist;
import com.preponderous.roam.model.User;
import com.preponderous.roam.persistence.repository.RefreshTokenRepository;
import com.preponderous.roam.persistence.repository.TokenBlacklistRepository;
import com.preponderous.roam.persistence.repository.UserRepository;
import com.preponderous.roam.security.JwtUtils;
import com.preponderous.roam.exception.UserAlreadyExistsException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;

/**
 * Service for authentication operations.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class AuthService {
    
    @Autowired
    private AuthenticationManager authenticationManager;
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private RefreshTokenRepository refreshTokenRepository;
    
    @Autowired
    private TokenBlacklistRepository tokenBlacklistRepository;
    
    @Autowired
    private PasswordEncoder passwordEncoder;
    
    @Autowired
    private JwtUtils jwtUtils;
    
    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new UserAlreadyExistsException("Username is already taken");
        }
        
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new UserAlreadyExistsException("Email is already in use");
        }
        
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        
        Set<String> roles = new HashSet<>();
        roles.add("ROLE_USER");
        user.setRoles(roles);
        
        userRepository.save(user);
        
        // Auto-login after registration
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
        );
        
        SecurityContextHolder.getContext().setAuthentication(authentication);
        
        return generateAuthResponse(authentication, user);
    }
    
    @Transactional
    public AuthResponse login(LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getUsername(), request.getPassword())
        );
        
        SecurityContextHolder.getContext().setAuthentication(authentication);
        
        User user = userRepository.findByUsername(request.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));
        
        return generateAuthResponse(authentication, user);
    }
    
    @Transactional
    public AuthResponse refreshToken(RefreshTokenRequest request) {
        String requestRefreshToken = request.getRefreshToken();
        
        if (!jwtUtils.validateToken(requestRefreshToken)) {
            throw new RuntimeException("Invalid refresh token");
        }
        
        RefreshToken refreshToken = refreshTokenRepository.findByToken(requestRefreshToken)
                .orElseThrow(() -> new RuntimeException("Refresh token not found"));
        
        if (refreshToken.isRevoked()) {
            throw new RuntimeException("Refresh token has been revoked");
        }
        
        if (refreshToken.isExpired()) {
            throw new RuntimeException("Refresh token is expired");
        }
        
        User user = refreshToken.getUser();
        UserDetails userDetails = org.springframework.security.core.userdetails.User.builder()
                .username(user.getUsername())
                .password(user.getPassword())
                .authorities(user.getRoles().toArray(new String[0]))
                .build();
        
        Authentication authentication = new UsernamePasswordAuthenticationToken(
                userDetails, null, userDetails.getAuthorities()
        );
        
        String newAccessToken = jwtUtils.generateAccessToken(authentication);
        
        return new AuthResponse(
                newAccessToken,
                requestRefreshToken,
                jwtUtils.getAccessExpirationMs() / 1000,
                user.getUsername(),
                user.getRoles()
        );
    }
    
    @Transactional
    public void logout(String token) {
        if (token != null && jwtUtils.validateToken(token)) {
            Date expiration = jwtUtils.getExpirationFromToken(token);
            TokenBlacklist blacklistedToken = new TokenBlacklist(token, expiration.toInstant());
            tokenBlacklistRepository.save(blacklistedToken);
            
            String username = jwtUtils.getUsernameFromToken(token);
            User user = userRepository.findByUsername(username).orElse(null);
            if (user != null) {
                refreshTokenRepository.deleteByUser(user);
            }
        }
        
        SecurityContextHolder.clearContext();
    }
    
    private AuthResponse generateAuthResponse(Authentication authentication, User user) {
        String accessToken = jwtUtils.generateAccessToken(authentication);
        String refreshTokenStr = jwtUtils.generateRefreshToken(user.getUsername());
        
        Instant refreshTokenExpiry = Instant.now().plusMillis(jwtUtils.getRefreshExpirationMs());
        RefreshToken refreshToken = new RefreshToken(user, refreshTokenStr, refreshTokenExpiry);
        refreshTokenRepository.save(refreshToken);
        
        return new AuthResponse(
                accessToken,
                refreshTokenStr,
                jwtUtils.getAccessExpirationMs() / 1000,
                user.getUsername(),
                user.getRoles()
        );
    }
    
    @Transactional
    public void cleanupExpiredTokens() {
        Instant now = Instant.now();
        refreshTokenRepository.deleteByExpiresAtBefore(now);
        tokenBlacklistRepository.deleteByExpiresAtBefore(now);
    }
}
