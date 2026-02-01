# Docker Deployment Guide

This guide explains how to run Roam using Docker containers.

## Overview

Roam can be containerized using Docker for easy deployment:

- **Server**: Spring Boot backend runs in a Docker container
- **Client**: Python pygame client (optional, requires display access)

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+

## Quick Start

### Option 1: Server Only (Recommended)

Run the server in Docker and the client natively on your host:

```bash
# Start the server
docker compose up -d roam-server

# Check server status
docker compose logs -f roam-server

# Run client on host (in another terminal)
cd src
python3 roam.py
```

### Option 2: Server + Client (Linux with X11 only)

Run both server and client in Docker containers:

```bash
# Allow Docker to access X11 display
xhost +local:docker

# Uncomment roam-client service in compose.yml
# Then start both services
docker compose up -d

# Check logs
docker compose logs -f
```

## Files

### Dockerfile

Multi-stage Dockerfile for the Spring Boot server:

- **Stage 1 (builder)**: Uses Maven to build the application
- **Stage 2 (runtime)**: Minimal JRE image with the built JAR

**Features**:
- Multi-stage build for smaller image size
- Maven dependency caching for faster rebuilds
- Health check endpoint
- Configurable JVM options
- CORS environment variable support

### compose.yml

Docker Compose configuration defining services:

- **roam-server**: Spring Boot backend
  - Port: 8080
  - Health checks enabled
  - Auto-restart policy
  - Configurable via environment variables

- **roam-client** (commented out): Python pygame client
  - Requires X11 display
  - Only works on Linux hosts
  - Network access to server

### Dockerfile.client

Optional Dockerfile for the Python client:

- Based on Python 3.11
- Installs build tools (gcc, g++, make) for compiling pygame
- Installs pygame and SDL dependencies
- Requires X11 display forwarding
- Connects to server via environment variable

**Note**: The client image is larger (~500MB) due to build dependencies required for pygame compilation.

## Commands

### Build and Start

```bash
# Build and start server
docker compose up -d roam-server

# Build without cache (force rebuild)
docker compose build --no-cache roam-server

# Start in foreground (see logs)
docker compose up roam-server
```

### Stop and Remove

```bash
# Stop services
docker compose stop

# Stop and remove containers
docker compose down

# Remove containers, networks, and volumes
docker compose down -v
```

### Logs and Monitoring

```bash
# View logs
docker compose logs roam-server

# Follow logs (real-time)
docker compose logs -f roam-server

# Check status
docker compose ps

# Check health
docker compose exec roam-server wget -qO- http://localhost:8080/actuator/health
```

### Shell Access

```bash
# Access server container shell
docker compose exec roam-server sh

# Run commands in container
docker compose exec roam-server java -version
```

## Configuration

### Environment Variables

Configure the server via environment variables in `compose.yml`:

```yaml
environment:
  # CORS origins (comma-separated)
  ALLOWED_ORIGINS: "http://localhost:3000,http://localhost:5000"
  
  # JVM memory settings
  JAVA_OPTS: "-Xmx512m -Xms256m"
```

### Port Mapping

Change the exposed port by editing `compose.yml`:

```yaml
ports:
  - "9090:8080"  # Expose on port 9090
```

Then connect client to `http://localhost:9090`.

### Volume Mounting (Optional)

To persist data or enable hot-reload during development:

```yaml
services:
  roam-server:
    volumes:
      - ./server/src:/app/src:ro  # Mount source (read-only)
      - roam-data:/app/data        # Persist data

volumes:
  roam-data:
```

## Running the Client in Docker

### Requirements

The Python client requires display access, which is complex in Docker:

- **Linux**: X11 display forwarding (works)
- **macOS**: XQuartz required (experimental)
- **Windows**: WSL2 with X11 server (complex)

### Linux Setup

1. Allow Docker to access X11:
```bash
xhost +local:docker
```

2. Uncomment the `roam-client` service in `compose.yml`

3. Start the client:
```bash
docker compose up -d roam-client
```

4. View client logs:
```bash
docker compose logs -f roam-client
```

5. Clean up after use:
```bash
xhost -local:docker
```

### macOS Setup (Experimental)

1. Install and start XQuartz:
```bash
brew install --cask xquartz
open -a XQuartz
```

2. In XQuartz preferences, enable "Allow connections from network clients"

3. Allow connections:
```bash
xhost +localhost
```

4. Update `compose.yml`:
```yaml
roam-client:
  environment:
    - DISPLAY=host.docker.internal:0
```

5. Start client:
```bash
docker compose up -d roam-client
```

### Windows Setup

Not recommended. Use WSL2 with X11 server or run client natively on Windows.

## Production Deployment

### Best Practices

1. **Use specific image tags**:
```yaml
roam-server:
  image: roam-server:1.0.0
```

2. **Set resource limits**:
```yaml
roam-server:
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 1G
      reservations:
        memory: 512M
```

3. **Use secrets for sensitive data**:
```yaml
roam-server:
  secrets:
    - db_password
```

4. **Enable logging driver**:
```yaml
roam-server:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

5. **Use a reverse proxy** (nginx, traefik) for HTTPS and load balancing

### Scaling

Scale server instances:

```bash
docker compose up -d --scale roam-server=3
```

Note: Requires load balancer and session management.

## Troubleshooting

### Server won't start

Check logs:
```bash
docker compose logs roam-server
```

Common issues:
- Port 8080 already in use: Change port mapping
- Build failed: Check Maven dependencies
- Health check failing: Wait longer or check application logs

### Client can't connect to server

1. Check server is running:
```bash
curl http://localhost:8080/api/v1/session/init -X POST -H "Content-Type: application/json" -d '{}'
```

2. Verify CORS settings in `compose.yml`

3. Use `host.docker.internal` instead of `localhost` from within client container

### Client display issues

1. Check X11 forwarding:
```bash
echo $DISPLAY
xhost
```

2. Verify X11 socket is mounted:
```bash
docker compose exec roam-client ls -la /tmp/.X11-unix
```

3. Check pygame errors:
```bash
docker compose logs roam-client
```

### Permission denied errors

Run xhost command:
```bash
xhost +local:docker
```

Or use specific user:
```yaml
roam-client:
  user: "${UID}:${GID}"
```

## Architecture

```
┌─────────────────────────────────────┐
│ Docker Host                          │
│                                      │
│  ┌────────────────────────────────┐ │
│  │ roam-server (Container)        │ │
│  │                                 │ │
│  │  - Spring Boot App (Java 17)   │ │
│  │  - Port 8080                    │ │
│  │  - REST API                     │ │
│  │  - In-memory sessions           │ │
│  └────────────────────────────────┘ │
│           │                          │
│           │ REST API                 │
│           ▼                          │
│  ┌────────────────────────────────┐ │
│  │ roam-client (Container)        │ │
│  │ [Optional]                      │ │
│  │  - Python 3.11                  │ │
│  │  - pygame UI                    │ │
│  │  - X11 display                  │ │
│  └────────────────────────────────┘ │
│           │                          │
└───────────┼──────────────────────────┘
            │ X11
            ▼
    ┌──────────────┐
    │ Host Display │
    └──────────────┘
```

## Alternative: Native Client

**Recommended approach**: Run server in Docker, client natively:

```bash
# Terminal 1: Start server
docker compose up -d roam-server

# Terminal 2: Run client natively
cd src
python3 roam.py http://localhost:8080
```

This avoids X11 complexity while still containerizing the server.

## Testing

Test the containerized setup:

```bash
# Start server
docker compose up -d roam-server

# Wait for health check
docker compose ps

# Run test script
cd src
python3 test_client.py
```

All tests should pass ✓

## Performance

Typical resource usage:

- **Server**: ~200-400 MB RAM, <5% CPU (idle)
- **Client**: ~100-150 MB RAM, 10-30% CPU (active rendering)

Adjust memory limits in `compose.yml` based on your needs.

## Security Notes

1. **CORS**: Configure `ALLOWED_ORIGINS` for production
2. **Ports**: Don't expose port 8080 publicly without authentication
3. **Secrets**: Never commit credentials to `compose.yml`
4. **Updates**: Regularly update base images
5. **Network**: Use internal networks for service communication

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Spring Boot Docker Guide](https://spring.io/guides/topicals/spring-boot-docker/)
- [X11 Docker Tutorial](https://wiki.ros.org/docker/Tutorials/GUI)

## Support

For issues related to Docker deployment:

1. Check logs: `docker compose logs`
2. Verify configuration: `docker compose config`
3. Test connectivity: `curl http://localhost:8080/api/v1/session/init`
4. Review this documentation
5. See main README.md for general application support
