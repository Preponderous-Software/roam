#!/bin/bash
# Quick start script for Roam using Docker

set -e

echo "=========================================="
echo "Roam - Docker Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    echo "Please install Docker Compose or update Docker to a newer version"
    exit 1
fi

echo "✓ Docker is installed"
echo ""

# Start the server
echo "Starting Roam server..."
docker compose up -d roam-server

echo ""
echo "Waiting for server to be healthy..."
for i in {1..30}; do
    if docker compose ps roam-server | grep -q "healthy"; then
        echo "✓ Server is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠ Server health check timeout. Check logs with: docker compose logs roam-server"
        break
    fi
    sleep 2
    echo -n "."
done

echo ""
echo "=========================================="
echo "✓ Server started successfully!"
echo "=========================================="
echo ""
echo "Server is running at: http://localhost:8080"
echo ""
echo "Next steps:"
echo "  1. Run the client:"
echo "     cd client && python3 roam_client.py"
echo ""
echo "  2. View server logs:"
echo "     docker compose logs -f roam-server"
echo ""
echo "  3. Stop the server:"
echo "     docker compose down"
echo ""
echo "See DOCKER.md for more information."
echo "=========================================="
