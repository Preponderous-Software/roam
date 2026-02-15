# Roam Web Client

Browser-based client for playing Roam in your web browser.

## Features

- 🌐 **Browser-based**: Play directly in your web browser without installing any software
- 🎮 **Full game controls**: WASD movement, running, crouching, and gathering
- 🔐 **Authentication**: Secure login and registration
- 🔄 **Real-time updates**: WebSocket connection for live game state updates
- 📱 **Responsive design**: Clean, modern UI that works on different screen sizes
- 🎨 **Canvas rendering**: Hardware-accelerated 2D graphics using HTML5 Canvas

## Quick Start

### Using Docker Compose (Recommended)

1. Start all services:
```bash
docker compose up -d
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Register a new account or login with existing credentials

4. Start playing!

### Manual Setup

If you want to run the web client separately:

1. Make sure the Roam server is running on `http://localhost:8080`

2. Serve the web client using any HTTP server. For example with Python:
```bash
cd web-client
python3 -m http.server 8000
```

3. Open your browser to `http://localhost:8000`

## Architecture

The web client is a single-page application (SPA) built with vanilla JavaScript:

- **index.html**: Main HTML page with authentication and game UI
- **game.js**: Game client logic, API communication, and rendering
- **nginx.conf**: Nginx configuration for serving the client and proxying API requests
- **Dockerfile**: Container image for deployment

### Technology Stack

- HTML5 Canvas for rendering
- Vanilla JavaScript (ES6+)
- WebSocket for real-time communication
- REST API for game actions
- Nginx for serving static files and proxying

## Controls

| Key | Action |
|-----|--------|
| W | Move up |
| A | Move left |
| S | Move down |
| D | Move right |
| Shift | Run (hold) |
| Ctrl | Crouch (hold) |
| Space | Gather (hold) |

## Configuration

### API Endpoint

By default, the web client connects to the server at:
- `http://localhost:8080` when running locally
- Same hostname on port 8080 when deployed

To change the API endpoint, edit `game.js`:

```javascript
const API_BASE_URL = 'http://your-server:8080';
```

### CORS Configuration

The server must allow requests from the web client origin. Update `compose.yml`:

```yaml
environment:
  ALLOWED_ORIGINS: "http://localhost,http://your-domain.com"
```

## Development

### File Structure

```
web-client/
├── index.html      # Main HTML page
├── game.js         # Game client JavaScript
├── nginx.conf      # Nginx configuration
├── Dockerfile      # Container image definition
└── README.md       # This file
```

### Making Changes

1. Edit the files directly
2. Rebuild and restart the container:
```bash
docker compose up -d --build web-client
```

3. Refresh your browser to see changes

### Local Development

For faster iteration during development:

1. Run the server:
```bash
docker compose up -d roam-server
```

2. Serve the web client locally:
```bash
cd web-client
python3 -m http.server 8000
```

3. Edit `game.js` to point to the correct server:
```javascript
const API_BASE_URL = 'http://localhost:8080';
```

4. Make your changes and simply refresh the browser

## Troubleshooting

### Cannot connect to server

1. Check that the server is running:
```bash
docker compose ps
curl http://localhost:8080/actuator/health
```

2. Check CORS configuration in the server environment variables

3. Open browser DevTools (F12) and check the Console for errors

### WebSocket connection fails

1. Ensure the server is accessible
2. Check that port 8080 is not blocked by a firewall
3. Verify WebSocket endpoint is working: `ws://localhost:8080/ws`

### Game not rendering

1. Make sure you're logged in
2. Check browser console (F12) for JavaScript errors
3. Verify the session was initialized successfully

### Authentication issues

1. Check that the database is running and healthy
2. Verify user credentials are correct
3. Clear browser localStorage and try again:
   - Open DevTools (F12)
   - Application tab → Local Storage
   - Clear all items

## Browser Compatibility

The web client is tested and works on:
- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

WebSocket and Canvas support is required.

## Performance

The web client is optimized for performance:
- Connection pooling for HTTP requests
- Throttled input processing (5 moves/second max)
- Efficient Canvas rendering with requestAnimationFrame
- Minimal DOM manipulation
- Automatic WebSocket reconnection

Typical resource usage:
- ~5-10 MB memory
- ~1-5% CPU (depending on activity)
- ~10-50 KB/s network (with active gameplay)

## Security

The web client implements security best practices:
- JWT-based authentication
- Secure token storage (localStorage)
- Automatic token refresh
- HTTPS support (in production)
- XSS protection headers
- CORS validation

**Production recommendations:**
- Use HTTPS for all communication
- Set secure CORS origins (no wildcards)
- Implement rate limiting on the server
- Regular security updates

## Contributing

To contribute to the web client:

1. Make your changes
2. Test thoroughly in multiple browsers
3. Update documentation if needed
4. Submit a pull request

## License

This project is licensed under the Preponderous Non-Commercial License (Preponderous-NC).
See the main repository LICENSE file for details.

## Support

For issues or questions:
- Check the main [README](../README.md)
- Visit the [Discord server](https://discord.gg/49J4RHQxhy)
- Open an issue on GitHub

## Credits

- Original game by Daniel McCoy Stephenson
- Web client implementation: Browser-based adaptation of the Python client
