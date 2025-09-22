import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging


class RoamAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Roam REST API"""
    
    def __init__(self, world_screen, player, *args, **kwargs):
        self.world_screen = world_screen
        self.player = player
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path_parts = parsed_path.path.strip('/').split('/')
            
            if not path_parts or path_parts[0] == '':
                self._send_response(200, {"message": "Roam REST API", "version": "1.0.0"})
                return
            
            if path_parts[0] == 'world':
                self._handle_world_request(path_parts[1:])
            elif path_parts[0] == 'player':
                self._handle_player_request(path_parts[1:])
            else:
                self._send_error(404, "Endpoint not found")
                
        except Exception as e:
            logging.error(f"Error handling GET request: {e}")
            self._send_error(500, "Internal server error")
    
    def _handle_world_request(self, path_parts):
        """Handle world-related API requests"""
        if not path_parts:
            # Get general world info
            world_data = self._get_world_data()
            self._send_response(200, world_data)
        elif path_parts[0] == 'rooms':
            # Get rooms data
            rooms_data = self._get_rooms_data()
            self._send_response(200, rooms_data)
        elif path_parts[0] == 'room' and len(path_parts) >= 3:
            # Get specific room data
            try:
                x = int(path_parts[1])
                y = int(path_parts[2])
                room_data = self._get_room_data(x, y)
                if room_data:
                    self._send_response(200, room_data)
                else:
                    self._send_error(404, "Room not found")
            except ValueError:
                self._send_error(400, "Invalid room coordinates")
        else:
            self._send_error(404, "World endpoint not found")
    
    def _handle_player_request(self, path_parts):
        """Handle player-related API requests"""
        if not path_parts:
            # Get general player info
            player_data = self._get_player_data()
            self._send_response(200, player_data)
        elif path_parts[0] == 'inventory':
            # Get player inventory
            inventory_data = self._get_player_inventory()
            self._send_response(200, inventory_data)
        elif path_parts[0] == 'stats':
            # Get player stats
            stats_data = self._get_player_stats()
            self._send_response(200, stats_data)
        else:
            self._send_error(404, "Player endpoint not found")
    
    def _get_world_data(self):
        """Get general world information"""
        try:
            current_room = self.world_screen.getCurrentRoom()
            return {
                "current_room": {
                    "x": current_room.getX() if current_room else None,
                    "y": current_room.getY() if current_room else None,
                    "name": current_room.getName() if current_room else None
                },
                "loaded_rooms_count": len(self.world_screen.getMap().getRooms()) if hasattr(self.world_screen, 'getMap') else 0,
                "tick_count": self.world_screen.getTickCounter().getTick() if hasattr(self.world_screen, 'getTickCounter') else 0
            }
        except Exception as e:
            logging.error(f"Error getting world data: {e}")
            return {"error": "Could not retrieve world data"}
    
    def _get_rooms_data(self):
        """Get information about all loaded rooms"""
        try:
            rooms = []
            if hasattr(self.world_screen, 'getMap'):
                for room in self.world_screen.getMap().getRooms():
                    rooms.append({
                        "x": room.getX(),
                        "y": room.getY(),
                        "name": room.getName(),
                        "entity_count": len(room.getGrid().getLocations()) if hasattr(room, 'getGrid') else 0,
                        "living_entities_count": len(room.getLivingEntities()) if hasattr(room, 'getLivingEntities') else 0
                    })
            return {"rooms": rooms}
        except Exception as e:
            logging.error(f"Error getting rooms data: {e}")
            return {"error": "Could not retrieve rooms data"}
    
    def _get_room_data(self, x, y):
        """Get detailed information about a specific room"""
        try:
            if not hasattr(self.world_screen, 'getMap'):
                return None
            
            room = self.world_screen.getMap().getRoom(x, y)
            if room == -1:
                return None
            
            # Get entities in the room
            entities = []
            if hasattr(room, 'getGrid'):
                grid = room.getGrid()
                for location_id in grid.getLocations():
                    location = grid.getLocation(location_id)
                    if location.getNumEntities() > 0:
                        for entity_id, entity in location.getEntities().items():
                            entities.append({
                                "id": entity.getID(),
                                "name": entity.getName(),
                                "x": location.getX(),
                                "y": location.getY(),
                                "is_solid": entity.isSolid() if hasattr(entity, 'isSolid') else False
                            })
            
            # Get living entities
            living_entities = []
            if hasattr(room, 'getLivingEntities'):
                for entity_id, entity in room.getLivingEntities().items():
                    living_entities.append({
                        "id": entity.getID(),
                        "name": entity.getName(),
                        "energy": entity.getEnergy() if hasattr(entity, 'getEnergy') else None,
                        "location_id": entity.getLocationID() if hasattr(entity, 'getLocationID') else None
                    })
            
            return {
                "x": room.getX(),
                "y": room.getY(),
                "name": room.getName(),
                "entities": entities,
                "living_entities": living_entities
            }
        except Exception as e:
            logging.error(f"Error getting room data: {e}")
            return None
    
    def _get_player_data(self):
        """Get general player information"""
        try:
            return {
                "name": self.player.getName(),
                "energy": self.player.getEnergy() if hasattr(self.player, 'getEnergy') else None,
                "location_id": self.player.getLocationID() if hasattr(self.player, 'getLocationID') else None,
                "direction": self.player.getDirection() if hasattr(self.player, 'getDirection') else None,
                "is_moving": self.player.isMoving() if hasattr(self.player, 'isMoving') else False,
                "is_gathering": self.player.isGathering() if hasattr(self.player, 'isGathering') else False,
                "is_placing": self.player.isPlacing() if hasattr(self.player, 'isPlacing') else False
            }
        except Exception as e:
            logging.error(f"Error getting player data: {e}")
            return {"error": "Could not retrieve player data"}
    
    def _get_player_inventory(self):
        """Get player inventory information"""
        try:
            inventory = self.player.getInventory()
            items = []
            if hasattr(inventory, 'getItems'):
                for item in inventory.getItems():
                    items.append({
                        "name": item.getName() if hasattr(item, 'getName') else str(item),
                        "quantity": inventory.getQuantityOfItem(item) if hasattr(inventory, 'getQuantityOfItem') else 1
                    })
            
            return {
                "items": items,
                "total_items": len(items)
            }
        except Exception as e:
            logging.error(f"Error getting player inventory: {e}")
            return {"error": "Could not retrieve player inventory"}
    
    def _get_player_stats(self):
        """Get player statistics"""
        try:
            # This would need to be implemented based on the actual stats system
            return {
                "movement_speed": self.player.getMovementSpeed() if hasattr(self.player, 'getMovementSpeed') else None,
                "gather_speed": self.player.getGatherSpeed() if hasattr(self.player, 'getGatherSpeed') else None,
                "place_speed": self.player.getPlaceSpeed() if hasattr(self.player, 'getPlaceSpeed') else None,
                "is_crouching": self.player.isCrouching() if hasattr(self.player, 'isCrouching') else False
            }
        except Exception as e:
            logging.error(f"Error getting player stats: {e}")
            return {"error": "Could not retrieve player stats"}
    
    def _send_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS
        self.end_headers()
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error(self, status_code, message):
        """Send error response"""
        self._send_response(status_code, {"error": message})
    
    def log_message(self, format, *args):
        """Override to use logging instead of stderr"""
        logging.info(f"API Request: {format % args}")


class RoamAPIServer:
    """REST API server for Roam game data"""
    
    def __init__(self, world_screen, player, host='localhost', port=8080):
        self.world_screen = world_screen
        self.player = player
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the API server"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def start(self):
        """Start the API server in a separate thread"""
        try:
            # Create a handler class with bound parameters
            class BoundHandler(RoamAPIHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(world_screen, player, *args, **kwargs)
            
            world_screen = self.world_screen
            player = self.player
            
            self.server = HTTPServer((self.host, self.port), BoundHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            logging.info(f"Roam API server started on {self.host}:{self.port}")
            print(f"REST API server running on http://{self.host}:{self.port}")
            print("Available endpoints:")
            print("  GET /world - General world information")
            print("  GET /world/rooms - List of loaded rooms")
            print("  GET /world/room/{x}/{y} - Specific room data")
            print("  GET /player - General player information")
            print("  GET /player/inventory - Player inventory")
            print("  GET /player/stats - Player statistics")
            
            return True
        except Exception as e:
            logging.error(f"Failed to start API server: {e}")
            return False
    
    def stop(self):
        """Stop the API server"""
        if self.server:
            self.server.shutdown()
            self.server_thread.join()
            logging.info("Roam API server stopped")
    
    def is_running(self):
        """Check if the server is running"""
        return self.server is not None and self.server_thread and self.server_thread.is_alive()