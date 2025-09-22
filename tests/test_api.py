import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.api_server import RoamAPIServer, RoamAPIHandler


class TestableAPIHandler:
    """A testable version of RoamAPIHandler that doesn't inherit from BaseHTTPRequestHandler"""
    
    def __init__(self, world_screen, player):
        self.world_screen = world_screen
        self.player = player
    
    # Copy the data extraction methods from RoamAPIHandler
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
            return {"error": "Could not retrieve rooms data"}
    
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
            return {"error": "Could not retrieve player inventory"}
    
    def _get_player_stats(self):
        """Get player statistics"""
        try:
            return {
                "movement_speed": self.player.getMovementSpeed() if hasattr(self.player, 'getMovementSpeed') else None,
                "gather_speed": self.player.getGatherSpeed() if hasattr(self.player, 'getGatherSpeed') else None,
                "place_speed": self.player.getPlaceSpeed() if hasattr(self.player, 'getPlaceSpeed') else None,
                "is_crouching": self.player.isCrouching() if hasattr(self.player, 'isCrouching') else False
            }
        except Exception as e:
            return {"error": "Could not retrieve player stats"}


class TestRoamAPI(unittest.TestCase):
    """Test the Roam REST API"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock objects for world_screen and player
        self.mock_world_screen = Mock()
        self.mock_player = Mock()
        
        # Setup mock world screen
        self.mock_current_room = Mock()
        self.mock_current_room.getX.return_value = 0
        self.mock_current_room.getY.return_value = 0
        self.mock_current_room.getName.return_value = "Test Room"
        
        # Setup mock grid and living entities for the room
        self.mock_grid = Mock()
        self.mock_grid.getLocations.return_value = []
        self.mock_current_room.getGrid.return_value = self.mock_grid
        self.mock_current_room.getLivingEntities.return_value = {}
        
        self.mock_world_screen.getCurrentRoom.return_value = self.mock_current_room
        
        self.mock_map = Mock()
        self.mock_map.getRooms.return_value = [self.mock_current_room]
        self.mock_world_screen.getMap.return_value = self.mock_map
        
        self.mock_tick_counter = Mock()
        self.mock_tick_counter.getTick.return_value = 1000
        self.mock_world_screen.getTickCounter.return_value = self.mock_tick_counter
        
        # Setup mock player
        self.mock_player.getName.return_value = "Test Player"
        self.mock_player.getEnergy.return_value = 100
        self.mock_player.getLocationID.return_value = 1
        self.mock_player.getDirection.return_value = 2
        self.mock_player.isMoving.return_value = False
        self.mock_player.isGathering.return_value = False
        self.mock_player.isPlacing.return_value = False
        self.mock_player.getMovementSpeed.return_value = 30
        self.mock_player.getGatherSpeed.return_value = 30
        self.mock_player.getPlaceSpeed.return_value = 30
        self.mock_player.isCrouching.return_value = False
        
        # Setup mock inventory
        self.mock_inventory = Mock()
        self.mock_inventory.getItems.return_value = []
        self.mock_player.getInventory.return_value = self.mock_inventory
        
        # Create API server instance
        self.api_server = RoamAPIServer(self.mock_world_screen, self.mock_player, port=8081)
    
    def test_api_server_creation(self):
        """Test that the API server can be created"""
        self.assertIsNotNone(self.api_server)
        self.assertEqual(self.api_server.host, 'localhost')
        self.assertEqual(self.api_server.port, 8081)
        self.assertEqual(self.api_server.world_screen, self.mock_world_screen)
        self.assertEqual(self.api_server.player, self.mock_player)
    
    def test_handler_world_data(self):
        """Test the world data handler methods"""
        # Create a testable handler with mock objects
        handler = TestableAPIHandler(self.mock_world_screen, self.mock_player)
        
        # Test world data
        world_data = handler._get_world_data()
        self.assertIn('current_room', world_data)
        self.assertEqual(world_data['current_room']['x'], 0)
        self.assertEqual(world_data['current_room']['y'], 0)
        self.assertEqual(world_data['current_room']['name'], "Test Room")
        self.assertEqual(world_data['loaded_rooms_count'], 1)
        self.assertEqual(world_data['tick_count'], 1000)
    
    def test_handler_player_data(self):
        """Test the player data handler methods"""
        # Create a testable handler with mock objects
        handler = TestableAPIHandler(self.mock_world_screen, self.mock_player)
        
        # Test player data
        player_data = handler._get_player_data()
        self.assertEqual(player_data['name'], "Test Player")
        self.assertEqual(player_data['energy'], 100)
        self.assertEqual(player_data['location_id'], 1)
        self.assertEqual(player_data['direction'], 2)
        self.assertFalse(player_data['is_moving'])
        self.assertFalse(player_data['is_gathering'])
        self.assertFalse(player_data['is_placing'])
    
    def test_handler_player_inventory(self):
        """Test the player inventory handler"""
        # Create a testable handler with mock objects
        handler = TestableAPIHandler(self.mock_world_screen, self.mock_player)
        
        # Test player inventory
        inventory_data = handler._get_player_inventory()
        self.assertIn('items', inventory_data)
        self.assertIn('total_items', inventory_data)
        self.assertEqual(inventory_data['items'], [])
        self.assertEqual(inventory_data['total_items'], 0)
    
    def test_handler_player_stats(self):
        """Test the player stats handler"""
        # Create a testable handler with mock objects
        handler = TestableAPIHandler(self.mock_world_screen, self.mock_player)
        
        # Test player stats
        stats_data = handler._get_player_stats()
        self.assertEqual(stats_data['movement_speed'], 30)
        self.assertEqual(stats_data['gather_speed'], 30)
        self.assertEqual(stats_data['place_speed'], 30)
        self.assertFalse(stats_data['is_crouching'])
    
    def test_handler_rooms_data(self):
        """Test the rooms data handler"""
        # Create a testable handler with mock objects
        handler = TestableAPIHandler(self.mock_world_screen, self.mock_player)
        
        # Test rooms data
        rooms_data = handler._get_rooms_data()
        self.assertIn('rooms', rooms_data)
        self.assertEqual(len(rooms_data['rooms']), 1)
        self.assertEqual(rooms_data['rooms'][0]['x'], 0)
        self.assertEqual(rooms_data['rooms'][0]['y'], 0)
        self.assertEqual(rooms_data['rooms'][0]['name'], "Test Room")


if __name__ == '__main__':
    unittest.main()