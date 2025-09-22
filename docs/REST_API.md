# Roam REST API

This REST API provides external access to the Roam game world data, allowing client applications to retrieve information about the world state, player status, and game statistics.

## Getting Started

The REST API server starts automatically when you enter the game world. By default, it runs on `http://localhost:8080`.

## Available Endpoints

### General Information

#### `GET /`
Returns basic API information.

**Response:**
```json
{
  "message": "Roam REST API",
  "version": "1.0.0"
}
```

### World Endpoints

#### `GET /world`
Returns general world information including current room and basic statistics.

**Response:**
```json
{
  "current_room": {
    "x": 0,
    "y": 0,
    "name": "plains_room"
  },
  "loaded_rooms_count": 3,
  "tick_count": 15420
}
```

#### `GET /world/rooms`
Returns information about all currently loaded rooms.

**Response:**
```json
{
  "rooms": [
    {
      "x": 0,
      "y": 0,
      "name": "plains_room",
      "entity_count": 100,
      "living_entities_count": 5
    },
    {
      "x": 1,
      "y": 0,
      "name": "forest_room",
      "entity_count": 100,
      "living_entities_count": 8
    }
  ]
}
```

#### `GET /world/room/{x}/{y}`
Returns detailed information about a specific room at coordinates (x, y).

**Parameters:**
- `x`: Room x-coordinate (integer)
- `y`: Room y-coordinate (integer)

**Response:**
```json
{
  "x": 0,
  "y": 0,
  "name": "plains_room",
  "entities": [
    {
      "id": 1,
      "name": "Stone",
      "x": 5,
      "y": 3,
      "is_solid": true
    },
    {
      "id": 2,
      "name": "Grass",
      "x": 6,
      "y": 3,
      "is_solid": false
    }
  ],
  "living_entities": [
    {
      "id": 10,
      "name": "Chicken",
      "energy": 50,
      "location_id": 25
    }
  ]
}
```

### Player Endpoints

#### `GET /player`
Returns general player information.

**Response:**
```json
{
  "name": "Player",
  "energy": 85,
  "location_id": 45,
  "direction": 2,
  "is_moving": false,
  "is_gathering": false,
  "is_placing": false
}
```

#### `GET /player/inventory`
Returns the player's inventory contents.

**Response:**
```json
{
  "items": [
    {
      "name": "OakWood",
      "quantity": 15
    },
    {
      "name": "Stone",
      "quantity": 8
    },
    {
      "name": "Apple",
      "quantity": 3
    }
  ],
  "total_items": 3
}
```

#### `GET /player/stats`
Returns player statistics and movement attributes.

**Response:**
```json
{
  "movement_speed": 30,
  "gather_speed": 30,
  "place_speed": 30,
  "is_crouching": false
}
```

## Error Responses

When an error occurs, the API returns an appropriate HTTP status code and an error message:

```json
{
  "error": "Room not found"
}
```

Common error codes:
- `400 Bad Request`: Invalid parameters (e.g., non-numeric room coordinates)
- `404 Not Found`: Resource not found (e.g., room doesn't exist)
- `500 Internal Server Error`: Unexpected server error

## CORS Support

The API includes CORS headers to allow cross-origin requests from web applications.

## Example Usage

### Fetching World Information with curl
```bash
curl http://localhost:8080/world
```

### Fetching Player Inventory with JavaScript
```javascript
fetch('http://localhost:8080/player/inventory')
  .then(response => response.json())
  .then(data => console.log('Player inventory:', data));
```

### Fetching Room Data with Python
```python
import requests

response = requests.get('http://localhost:8080/world/room/0/0')
room_data = response.json()
print(f"Room at (0,0): {room_data['name']}")
```

## Use Cases

This API enables various external applications:

1. **World Viewer Applications**: Display the game world state in a web browser or separate application
2. **Mapping Applications**: Create interactive maps showing room layouts and entity positions
3. **Statistics Dashboards**: Monitor game progress and player statistics
4. **Development Tools**: Debug and analyze game state during development
5. **Companion Apps**: Mobile or web apps that provide additional game information

## Technical Notes

- The API server runs in a separate thread and doesn't affect game performance
- Data is retrieved in real-time from the active game session
- The server automatically starts when the world screen is initialized
- The server stops when the game is closed

## Configuration

By default, the API server uses:
- Host: `localhost` 
- Port: `8080`

These settings can be modified in the `RoamAPIServer` initialization in `src/roam.py`.