# Database Setup and Configuration

This document provides detailed information about setting up and using the database persistence layer for the Roam game server.

## Table of Contents

- [Overview](#overview)
- [Database Profiles](#database-profiles)
- [Quick Start with Docker Compose](#quick-start-with-docker-compose)
- [Local Development Setup](#local-development-setup)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Backup and Restore](#backup-and-restore)
- [Migrations](#migrations)
- [Testing](#testing)

## Overview

The Roam server uses JPA/Hibernate for database persistence with support for:

- **PostgreSQL** (production)
- **H2** (development and testing)
- **Flyway** for schema migrations
- **HikariCP** for connection pooling
- **Testcontainers** for integration testing

## Database Profiles

The application supports multiple profiles for different environments:

### H2 Profile (Default)

File-based H2 database for development:

```bash
# Start with H2 (default)
mvn spring-boot:run

# Or explicitly
mvn spring-boot:run -Dspring.profiles.active=h2
```

**Database location**: `./data/roam-db.mv.db`

**H2 Console**: http://localhost:8080/h2-console
- JDBC URL: `jdbc:h2:file:./data/roam-db`
- Username: `sa`
- Password: (empty)

### PostgreSQL Profile

For production use with PostgreSQL:

```bash
# Set environment variables (REQUIRED for security)
export DATABASE_URL=jdbc:postgresql://localhost:5432/roam
export DATABASE_USERNAME=roam
export DATABASE_PASSWORD=your_secure_password

# Run with PostgreSQL profile
mvn spring-boot:run -Dspring.profiles.active=postgresql
```

**Security Note**: Never use default passwords in production. Always set secure passwords via environment variables.

### Test Profile

In-memory H2 database for unit/integration tests:

```bash
mvn test
```

Tests automatically use the `test` profile with an in-memory database.

## Quick Start with Docker Compose

### Security Setup

**IMPORTANT**: Before running docker-compose, you must set a secure password:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set a secure POSTGRES_PASSWORD
nano .env  # or use your preferred editor

# Example .env content:
# POSTGRES_PASSWORD=MySecurePassword123!
```

The docker-compose configuration requires the `POSTGRES_PASSWORD` environment variable to be set. This prevents accidental deployment with insecure default passwords.

### Full Stack (Server + PostgreSQL)

```bash
# Start both server and database
docker-compose up

# Or in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

The server will be available at http://localhost:8080

### Database Only

For local development where you want to run the server locally but use PostgreSQL in Docker:

```bash
# Start only PostgreSQL
docker-compose -f compose-db-only.yml up -d

# Run server locally with PostgreSQL profile
cd server
mvn spring-boot:run -Dspring.profiles.active=postgresql
```

## Local Development Setup

### Prerequisites

- Java 17 or higher
- Maven 3.6 or higher
- PostgreSQL 12+ (if not using Docker)

### PostgreSQL Installation

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### macOS (Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16
```

### Create Database

```bash
# Login to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE roam;
CREATE USER roam WITH ENCRYPTED PASSWORD 'roam';
GRANT ALL PRIVILEGES ON DATABASE roam TO roam;
\q
```

### Configure Application

Edit `server/src/main/resources/application.yml` or set environment variables:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/roam
    username: roam
    password: roam
```

Or use environment variables:

```bash
export DATABASE_URL=jdbc:postgresql://localhost:5432/roam
export DATABASE_USERNAME=roam
export DATABASE_PASSWORD=roam
```

## Database Schema

The database consists of the following main tables:

### game_sessions

Stores game session metadata:

- `session_id` (PK): Unique session identifier
- `current_tick`: Current game tick
- `created_at`: Session creation timestamp
- `updated_at`: Last update timestamp
- `world_*`: World configuration parameters

### players

Stores player state:

- `id` (PK): Player identifier
- `session_id` (FK): Associated session
- Player stats (energy, position, speeds, etc.)
- Inventory state

### inventory_slots

Stores player inventory:

- `id` (PK): Auto-generated ID
- `player_id` (FK): Associated player
- `slot_index`: Inventory slot position
- `item_name`: Item type
- `num_items`: Quantity

### rooms

Stores world rooms:

- `id` (PK): Auto-generated ID
- `session_id` (FK): Associated session
- `room_x`, `room_y`: Room coordinates
- `width`, `height`: Room dimensions

### tiles

Stores tile data:

- `id` (PK): Auto-generated ID
- `room_id` (FK): Associated room
- `tile_x`, `tile_y`: Tile coordinates within room
- Biome, resources, and hazards

### game_entities

Stores game entities (trees, rocks, animals, etc.):

- `id` (PK): Entity identifier
- `room_id` (FK): Associated room
- `entity_type`: Entity class name
- Entity properties (energy, created tick, etc.)

## API Endpoints

### Save Game

```http
POST /api/v1/session/{sessionId}/save
```

Manually save the current game state to the database.

**Response:**
```json
{
  "message": "Session saved successfully",
  "sessionId": "abc-123"
}
```

### Load Game

```http
POST /api/v1/session/{sessionId}/load
```

Load a game state from the database into memory.

**Response:** Full session DTO with game state

### Auto-Save Configuration

Enable automatic saving every 100 ticks in `application.yml`:

```yaml
roam:
  persistence:
    auto-save: true
```

## Backup and Restore

### Security Note

Backup and restore scripts require the `DATABASE_PASSWORD` environment variable to be set for security:

```bash
# Set the database password before running backup/restore
export DATABASE_PASSWORD=your_secure_password
```

The scripts will refuse to run without this variable set to prevent using insecure default passwords.

### Backup Database

```bash
# Set password first
export DATABASE_PASSWORD=your_secure_password

# Backup to default location
./server/scripts/backup-db.sh

# Backup to specific file
./server/scripts/backup-db.sh /path/to/backup.sql
```

Backups are automatically compressed with gzip. The script keeps the last 10 backups.

### Restore Database

```bash
# Set password first
export DATABASE_PASSWORD=your_secure_password

# Restore from backup
./server/scripts/restore-db.sh ./server/scripts/backup/roam_backup_20260111_120000.sql.gz
```

**Warning:** This will drop the existing database and recreate it from the backup!

### Docker Backup

```bash
# Backup from Docker container
docker exec roam-postgres pg_dump -U roam roam | gzip > backup.sql.gz

# Restore to Docker container
gunzip < backup.sql.gz | docker exec -i roam-postgres psql -U roam roam
```

## Migrations

Database schema is managed using Flyway migrations located in:

```
server/src/main/resources/db/migration/
```

### Creating a New Migration

1. Create a new SQL file following the pattern:
   ```
   V<VERSION>__<description>.sql
   ```
   Example: `V2__add_player_achievements.sql`

2. Add SQL statements:
   ```sql
   CREATE TABLE achievements (
       id BIGSERIAL PRIMARY KEY,
       player_id VARCHAR(36) NOT NULL,
       achievement_name VARCHAR(100) NOT NULL,
       unlocked_at TIMESTAMP NOT NULL,
       FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
   );
   
   CREATE INDEX idx_achievements_player ON achievements(player_id);
   ```

3. Restart the application - Flyway will automatically apply the migration

### Migration History

View migration history:

```bash
# For H2
# Access H2 console at http://localhost:8080/h2-console
# Query: SELECT * FROM flyway_schema_history;

# For PostgreSQL
psql -U roam -d roam -c "SELECT * FROM flyway_schema_history;"
```

## Testing

### Unit Tests

Run all tests including persistence tests:

```bash
cd server
mvn test
```

### Integration Tests

Integration tests use H2 in-memory database by default. To test with PostgreSQL using Testcontainers, you would need to add a test configuration (requires Docker).

### Test Coverage

Persistence tests cover:

- Save and load game state
- Update existing game state
- Delete game state
- Session existence checks
- Player state persistence
- World configuration persistence

## Configuration Properties

### Complete Configuration Reference

```yaml
spring:
  datasource:
    url: ${DATABASE_URL:jdbc:h2:file:./data/roam-db}
    driver-class-name: org.h2.Driver  # or org.postgresql.Driver
    username: ${DATABASE_USERNAME:sa}
    password: ${DATABASE_PASSWORD:}
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000

  jpa:
    hibernate:
      ddl-auto: validate  # Never use 'create' or 'update' in production!
    show-sql: false
    properties:
      hibernate:
        format_sql: true
        use_sql_comments: true

  flyway:
    enabled: true
    baseline-on-migrate: true
    locations: classpath:db/migration

roam:
  persistence:
    auto-save: false  # Set to true for automatic saves every 100 ticks
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | JDBC connection URL | `jdbc:h2:file:./data/roam-db` |
| `DATABASE_USERNAME` | Database username | `sa` (H2) / `roam` (PostgreSQL) |
| `DATABASE_PASSWORD` | Database password | empty (H2) / `roam` (PostgreSQL) |
| `SPRING_PROFILES_ACTIVE` | Active Spring profile | `h2` |

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to database

**Solutions:**
- Check database is running: `docker-compose ps` or `systemctl status postgresql`
- Verify connection parameters in environment variables
- Check firewall settings
- Review logs: `docker-compose logs postgres` or `journalctl -u postgresql`

### Migration Failures

**Problem:** Flyway migration fails

**Solutions:**
- Check migration SQL syntax
- Ensure migrations are numbered sequentially
- Review Flyway history: `SELECT * FROM flyway_schema_history;`
- If needed, repair: set `spring.flyway.repair=true` temporarily

### Performance Issues

**Problem:** Slow database queries

**Solutions:**
- Check connection pool settings (HikariCP)
- Add database indexes for frequently queried columns
- Enable SQL logging to identify slow queries
- Monitor connection pool: Look for HikariCP warnings in logs

### Data Not Persisting

**Problem:** Game state not saved

**Solutions:**
- Verify auto-save is enabled if expecting automatic saves
- Manually call `/api/v1/session/{sessionId}/save` endpoint
- Check logs for persistence errors
- Verify database connectivity

## Performance Tuning

### Connection Pool Sizing

Adjust HikariCP settings based on your workload:

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20  # Max connections (default: 10)
      minimum-idle: 5        # Min idle connections (default: 10)
```

**Rule of thumb:** `maximum-pool-size` = (core_count * 2) + effective_spindle_count

### Query Optimization

- Indexes are already created for foreign keys and frequently queried columns
- Use `spring.jpa.show-sql=true` during development to monitor queries
- Consider implementing pagination for large data sets

## Security Considerations

### Production Checklist

- [ ] Use strong database passwords
- [ ] Never commit credentials to version control
- [ ] Use environment variables or secrets management
- [ ] Enable SSL/TLS for database connections
- [ ] Restrict database access by IP
- [ ] Regular backups with encryption
- [ ] Keep database software updated
- [ ] Monitor for unusual activity

### Password Security

```bash
# Generate secure password
openssl rand -base64 32

# Set in environment
export DATABASE_PASSWORD="<generated-password>"
```

## Additional Resources

- [Spring Data JPA Documentation](https://spring.io/projects/spring-data-jpa)
- [Hibernate Documentation](https://hibernate.org/orm/documentation/)
- [Flyway Documentation](https://flywaydb.org/documentation/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [H2 Database Documentation](http://www.h2database.com/html/main.html)
