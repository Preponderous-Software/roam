package com.preponderous.roam;

import com.preponderous.roam.service.AutoSaveService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ApplicationContext;
import org.springframework.scheduling.annotation.EnableScheduling;

import javax.annotation.PreDestroy;

/**
 * Main Spring Boot application class for Roam server.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootApplication
@EnableScheduling
public class RoamServerApplication {
    
    private static final Logger logger = LoggerFactory.getLogger(RoamServerApplication.class);
    
    private static ApplicationContext applicationContext;

    public static void main(String[] args) {
        applicationContext = SpringApplication.run(RoamServerApplication.class, args);
        
        // Register shutdown hook to save all sessions on server stop
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("Shutdown hook triggered - saving all active sessions");
            try {
                AutoSaveService autoSaveService = applicationContext.getBean(AutoSaveService.class);
                int savedCount = autoSaveService.saveAllSessionsNow();
                logger.info("Shutdown complete - saved {} session(s)", savedCount);
            } catch (Exception e) {
                logger.error("Error during shutdown save: {}", e.getMessage(), e);
            }
        }));
        
        logger.info("Roam server started successfully with graceful shutdown enabled");
    }
}
