# Python Client Authentication

The Roam Python client now supports JWT-based authentication with the server.

## Quick Start

### Command-Line Demo

```bash
# Ensure server is running
cd server
mvn spring-boot:run

# In another terminal
cd ..
python3 demo_api.py
```

This demo script shows:
1. User registration with JWT tokens
2. Authenticated API calls (session, player, inventory operations)
3. Automatic token management
4. Logout and token revocation

### Programmatic Usage

```python
from client.api_client import RoamAPIClient

# Create client
client = RoamAPIClient("http://localhost:8080")

# Register or login
client.register("username", "password", "email@example.com")
# OR
client.login("username", "password")

# Make authenticated calls - tokens handled automatically
session = client.init_session()
player = client.get_player()

# Logout
client.logout()
```

### GUI Client

The graphical Roam game client includes an interactive login screen:

1. Launch the client: `python3 src/roam.py`
2. Login screen appears on startup
3. **First time users**: Press 'R' to switch to Registration mode
4. Fill in the form:
   - TAB to switch fields
   - Type your credentials
   - ENTER to submit
5. Once logged in, proceed to the game

## Features

- ✅ **Automatic Token Management**: Client stores and injects JWT tokens
- ✅ **Token Refresh**: Automatically refreshes expired tokens
- ✅ **Secure**: All API calls authenticated after login
- ✅ **Easy Integration**: Simple register/login/logout API
- ✅ **GUI Support**: Interactive login screen for game client

## API Client Methods

### Authentication

- `register(username, password, email)` - Register new user
- `login(username, password)` - Login existing user  
- `logout()` - Logout and revoke tokens
- `is_authenticated()` - Check if logged in

### Game Operations

All existing methods work the same way, but now require authentication:

- `init_session()` - Create game session
- `get_player()` - Get player state
- `perform_player_action(...)` - Move, gather, etc.
- `get_inventory()` - Get inventory
- `add_item_to_inventory(item_name)` - Add item
- And more...

## Documentation

See [docs/AUTHENTICATION.md](../docs/AUTHENTICATION.md) for complete authentication documentation including:
- REST API endpoints
- Token configuration
- Security considerations
- Troubleshooting

## Example Output

```
============================================================
Roam Client-Server Architecture Demo
============================================================

1. Initializing API client...
   ✓ Client initialized

2. Authenticating with server...
   • Registering new user: demo_user_1768246394
   ✓ Registration successful!
   ✓ Username: demo_user_1768246394
   ✓ Roles: ROLE_USER
   ✓ Access token expires in: 3600 seconds

3. Creating new game session...
   ✓ Session created: 8ec6abdd-c4b2-4c3e-9efb-5c32c2741256
   ✓ Current tick: 0
   ✓ Player ID: 7f13f566-6673-4382-a2be-080b4c74d9d7
   ✓ Player energy: 100.0

...
```
