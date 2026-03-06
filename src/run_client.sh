#!/bin/bash
# Script to run the Roam client application

echo "========================================="
echo "Roam Client - Server-Backed Application"
echo "========================================="
echo ""

# Check if server URL is provided
SERVER_URL="${1:-http://localhost:8080}"

echo "Server URL: $SERVER_URL"
echo ""
echo "Make sure the Spring Boot server is running!"
echo "Start server with: cd ../server && mvn spring-boot:run"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================="
echo ""

# Run the client
python3 roam.py "$SERVER_URL"
