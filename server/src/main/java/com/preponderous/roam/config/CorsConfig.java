package com.preponderous.roam.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * CORS configuration for allowing Python client to access REST API.
 * 
 * @author Daniel McCoy Stephenson
 */
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        // Note: For production, configure allowed origins via environment variables
        // and restrict to specific domains for security
        String allowedOrigins = System.getenv("ALLOWED_ORIGINS");
        if (allowedOrigins == null || allowedOrigins.isEmpty()) {
            // Development default: use specific ports for client applications only
            // Port 8080 (server's own port) is excluded to prevent self-XSS attacks
            allowedOrigins = "http://localhost:3000,http://localhost:5000";
        }
        
        // Support comma-separated list of origins
        String[] allowedOriginArray = allowedOrigins.split("\\s*,\\s*");
        
        registry.addMapping("/api/**")
                .allowedOrigins(allowedOriginArray)
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .exposedHeaders("Authorization")
                .allowCredentials(false)
                .maxAge(3600);
    }
}
