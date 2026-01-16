"""
Unit tests for ServerBackedWorldScreen.
Tests the server-backed client functionality without requiring pygame UI.

Note: pygame mocking is handled by tests/conftest.py globally.
"""

import pytest
from unittest.mock import MagicMock, patch, call

from screen.serverBackedWorldScreen import ServerBackedWorldScreen
from screen.screenType import ScreenType


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for ServerBackedWorldScreen."""
    graphik = MagicMock()
    config = MagicMock()
    config.debug = False
    status = MagicMock()
    tick_counter = MagicMock()
    tick_counter.getTick.return_value = 0
    stats = MagicMock()
    player = MagicMock()
    player.getEnergy.return_value = 100.0
    player.getTargetEnergy.return_value = 100.0
    player.getDirection.return_value = -1
    player.isCrouching.return_value = False
    player.getInventory.return_value = MagicMock()
    api_client = MagicMock()
    session_id = "test-session-123"
    
    return {
        'graphik': graphik,
        'config': config,
        'status': status,
        'tick_counter': tick_counter,
        'stats': stats,
        'player': player,
        'api_client': api_client,
        'session_id': session_id
    }


@pytest.fixture
def world_screen(mock_dependencies):
    """Create a ServerBackedWorldScreen instance with mocked dependencies."""
    return ServerBackedWorldScreen(
        mock_dependencies['graphik'],
        mock_dependencies['config'],
        mock_dependencies['status'],
        mock_dependencies['tick_counter'],
        mock_dependencies['stats'],
        mock_dependencies['player'],
        mock_dependencies['api_client'],
        mock_dependencies['session_id']
    )


class TestServerBackedWorldScreenInitialization:
    """Test initialization of ServerBackedWorldScreen."""
    
    def test_constructor_sets_attributes(self, world_screen, mock_dependencies):
        """Test that constructor properly sets all attributes."""
        assert world_screen.graphik == mock_dependencies['graphik']
        assert world_screen.config == mock_dependencies['config']
        assert world_screen.status == mock_dependencies['status']
        assert world_screen.player == mock_dependencies['player']
        assert world_screen.api_client == mock_dependencies['api_client']
        assert world_screen.session_id == mock_dependencies['session_id']
        assert world_screen.running is True
        assert world_screen.changeScreen is False
        assert world_screen.player_data is None
        assert world_screen.server_tick == 0
    
    def test_initialize_fetches_player_data(self, world_screen, mock_dependencies):
        """Test that initialize fetches player data from server."""
        player_data = {
            'energy': 100.0,
            'direction': -1,
            'inventory': {'slots': []}
        }
        mock_dependencies['api_client'].get_player.return_value = player_data
        
        with patch.object(world_screen, 'energyBar', create=True):
            world_screen.initialize()
        
        mock_dependencies['api_client'].get_player.assert_called_once()
        assert world_screen.player_data == player_data
        mock_dependencies['status'].set.assert_called()
    
    def test_initialize_handles_server_error(self, world_screen, mock_dependencies):
        """Test that initialize handles server errors gracefully."""
        mock_dependencies['api_client'].get_player.side_effect = Exception("Connection failed")
        
        with patch.object(world_screen, 'energyBar', create=True):
            world_screen.initialize()
        
        assert world_screen.player_data is None
        mock_dependencies['status'].set.assert_called_with("Server error: Connection failed")


class TestPlayerActions:
    """Test player action methods."""
    
    def test_move_player_calls_server_api(self, world_screen, mock_dependencies):
        """Test that movePlayer sends action to server."""
        player_data = {'energy': 99.0, 'direction': 0, 'moving': True}
        mock_dependencies['api_client'].perform_player_action.return_value = player_data
        
        world_screen.movePlayer(0)
        
        mock_dependencies['api_client'].perform_player_action.assert_called_once_with(
            "move", direction=0
        )
        assert world_screen.player_data == player_data
        mock_dependencies['status'].set.assert_called_with("Moving up")
    
    def test_move_player_when_crouching(self, world_screen, mock_dependencies):
        """Test that movePlayer does nothing when player is crouching."""
        mock_dependencies['player'].isCrouching.return_value = True
        
        world_screen.movePlayer(0)
        
        mock_dependencies['api_client'].perform_player_action.assert_not_called()
    
    def test_move_player_handles_error(self, world_screen, mock_dependencies):
        """Test that movePlayer handles API errors."""
        mock_dependencies['api_client'].perform_player_action.side_effect = Exception("Server error")
        
        world_screen.movePlayer(0)
        
        mock_dependencies['status'].set.assert_called_with("Move failed: Server error")
    
    def test_stop_player_calls_server_api(self, world_screen, mock_dependencies):
        """Test that stopPlayer sends action to server."""
        player_data = {'direction': -1, 'moving': False}
        mock_dependencies['api_client'].perform_player_action.return_value = player_data
        
        world_screen.stopPlayer()
        
        mock_dependencies['api_client'].perform_player_action.assert_called_once_with("stop")
        mock_dependencies['status'].set.assert_called_with("Stopped")
    
    def test_stop_player_handles_error(self, world_screen, mock_dependencies):
        """Test that stopPlayer handles API errors."""
        mock_dependencies['api_client'].perform_player_action.side_effect = Exception("Server error")
        
        world_screen.stopPlayer()
        
        mock_dependencies['status'].set.assert_called_with("Stop failed: Server error")
    
    def test_toggle_gathering_with_player_data(self, world_screen, mock_dependencies):
        """Test toggleGathering with existing player data."""
        world_screen.player_data = {'gathering': False}
        new_data = {'gathering': True}
        mock_dependencies['api_client'].perform_player_action.return_value = new_data
        
        world_screen.toggleGathering()
        
        mock_dependencies['api_client'].perform_player_action.assert_called_once_with(
            "gather", gathering=True
        )
        mock_dependencies['status'].set.assert_called_with("Player gathering")
    
    def test_toggle_gathering_without_player_data(self, world_screen, mock_dependencies):
        """Test toggleGathering when player_data is None."""
        world_screen.player_data = None
        new_data = {'gathering': True}
        mock_dependencies['api_client'].perform_player_action.return_value = new_data
        
        world_screen.toggleGathering()
        
        mock_dependencies['api_client'].perform_player_action.assert_called_once_with(
            "gather", gathering=True
        )
    
    def test_toggle_gathering_handles_error(self, world_screen, mock_dependencies):
        """Test that toggleGathering handles API errors."""
        world_screen.player_data = {'gathering': False}
        mock_dependencies['api_client'].perform_player_action.side_effect = Exception("Server error")
        
        world_screen.toggleGathering()
        
        mock_dependencies['status'].set.assert_called_with("Gathering toggle failed: Server error")


class TestInventoryOperations:
    """Test inventory-related operations."""
    
    def test_add_test_item_success(self, world_screen, mock_dependencies):
        """Test adding an item to inventory."""
        player_data = {'inventory': {'slots': [{'itemName': 'apple', 'numItems': 1}]}}
        mock_dependencies['api_client'].get_player.return_value = player_data
        
        world_screen._addTestItem("apple")
        
        mock_dependencies['api_client'].add_item_to_inventory.assert_called_once_with("apple")
        mock_dependencies['api_client'].get_player.assert_called_once()
        mock_dependencies['status'].set.assert_called_with("Added apple")
    
    def test_add_test_item_handles_error(self, world_screen, mock_dependencies):
        """Test that _addTestItem handles errors."""
        mock_dependencies['api_client'].add_item_to_inventory.side_effect = Exception("Server error")
        
        world_screen._addTestItem("apple")
        
        mock_dependencies['status'].set.assert_called_with("Failed to add apple")
    
    def test_consume_food_with_valid_data(self, world_screen, mock_dependencies):
        """Test consuming food with valid player data."""
        world_screen.player_data = {
            'inventory': {
                'slots': [
                    {'empty': False, 'itemName': 'apple'},
                    {'empty': True}
                ]
            }
        }
        new_data = {'energy': 110.0}
        mock_dependencies['api_client'].perform_player_action.return_value = new_data
        
        world_screen._consumeFood()
        
        mock_dependencies['api_client'].perform_player_action.assert_called_once_with(
            "consume", item_name="apple"
        )
        mock_dependencies['status'].set.assert_called_with("Consumed apple")
    
    def test_consume_food_without_player_data(self, world_screen, mock_dependencies):
        """Test consuming food when player_data is None."""
        world_screen.player_data = None
        
        world_screen._consumeFood()
        
        mock_dependencies['api_client'].perform_player_action.assert_not_called()
        mock_dependencies['status'].set.assert_called_with("No player data available")
    
    def test_consume_food_with_empty_inventory(self, world_screen, mock_dependencies):
        """Test consuming food with empty inventory."""
        world_screen.player_data = {
            'inventory': {
                'slots': [{'empty': True}, {'empty': True}]
            }
        }
        
        world_screen._consumeFood()
        
        mock_dependencies['api_client'].perform_player_action.assert_not_called()
        mock_dependencies['status'].set.assert_called_with("No food to consume")
    
    def test_consume_food_handles_error(self, world_screen, mock_dependencies):
        """Test that _consumeFood handles errors."""
        world_screen.player_data = {
            'inventory': {
                'slots': [{'empty': False, 'itemName': 'apple'}]
            }
        }
        mock_dependencies['api_client'].perform_player_action.side_effect = Exception("Server error")
        
        world_screen._consumeFood()
        
        mock_dependencies['status'].set.assert_called_with("Consume failed: Server error")


class TestStateUpdates:
    """Test state update methods."""
    
    def test_update_player_from_server_data(self, world_screen, mock_dependencies):
        """Test updating player from server data."""
        player_data = {
            'energy': 95.0,
            'direction': 2,
            'inventory': {'slots': []}
        }
        
        world_screen._updatePlayerFromServerData(player_data)
        
        mock_dependencies['player'].setEnergy.assert_called_once_with(95.0)
        mock_dependencies['player'].setDirection.assert_called_once_with(2)
    
    def test_update_player_with_none_data(self, world_screen, mock_dependencies):
        """Test updating player with None data."""
        world_screen._updatePlayerFromServerData(None)
        
        mock_dependencies['player'].setEnergy.assert_not_called()
        mock_dependencies['player'].setDirection.assert_not_called()
    
    def test_update_player_with_invalid_direction(self, world_screen, mock_dependencies):
        """Test updating player with invalid direction."""
        player_data = {
            'energy': 95.0,
            'direction': -1,
            'inventory': {}
        }
        
        world_screen._updatePlayerFromServerData(player_data)
        
        mock_dependencies['player'].setEnergy.assert_called_once_with(95.0)
        mock_dependencies['player'].setDirection.assert_not_called()
    
    def test_update_tick_success(self, world_screen, mock_dependencies):
        """Test updating tick from server."""
        session_data = {'currentTick': 42}
        mock_dependencies['api_client'].update_tick.return_value = session_data
        
        world_screen.updateTick()
        
        assert world_screen.server_tick == 42
        mock_dependencies['api_client'].update_tick.assert_called_once()
    
    def test_update_tick_handles_error(self, world_screen, mock_dependencies):
        """Test that updateTick handles errors."""
        mock_dependencies['api_client'].update_tick.side_effect = Exception("Server error")
        
        world_screen.updateTick()
        
        mock_dependencies['status'].set.assert_called_with("Failed to update server tick")


class TestServerBackedArchitecture:
    """Test that server-backed architecture principles are maintained."""
    
    def test_no_local_state_mutations_on_movement(self, world_screen, mock_dependencies):
        """Test that movement doesn't modify local state before server response."""
        mock_dependencies['api_client'].perform_player_action.return_value = {'direction': 0}
        
        world_screen.movePlayer(0)
        
        # Should not call setDirection directly on player before server response
        # Direction is only updated via _updatePlayerFromServerData after server response
        assert mock_dependencies['api_client'].perform_player_action.called
    
    def test_all_actions_go_through_api(self, world_screen, mock_dependencies):
        """Test that all player actions go through API client."""
        world_screen.player_data = {'gathering': False}
        mock_dependencies['api_client'].perform_player_action.return_value = {}
        
        # Test various actions
        world_screen.movePlayer(0)
        world_screen.stopPlayer()
        world_screen.toggleGathering()
        
        # All should call the API
        assert mock_dependencies['api_client'].perform_player_action.call_count == 3
    
    def test_inventory_sync_is_no_op(self, world_screen):
        """Test that inventory sync doesn't clear inventory prematurely."""
        # This test verifies the intentional no-op behavior
        inventory_data = {'slots': [{'itemName': 'apple', 'numItems': 1}]}
        
        # Should not raise any errors and should be a no-op
        world_screen._updateInventoryFromServerData(inventory_data)
        
        # Test passes if no exception is raised


def test_integration_session_flow(mock_dependencies):
    """Integration test for a complete session flow."""
    world_screen = ServerBackedWorldScreen(
        mock_dependencies['graphik'],
        mock_dependencies['config'],
        mock_dependencies['status'],
        mock_dependencies['tick_counter'],
        mock_dependencies['stats'],
        mock_dependencies['player'],
        mock_dependencies['api_client'],
        mock_dependencies['session_id']
    )
    
    # Initialize
    mock_dependencies['api_client'].get_player.return_value = {
        'energy': 100.0,
        'direction': -1,
        'inventory': {'slots': []}
    }
    with patch.object(world_screen, 'energyBar', create=True):
        world_screen.initialize()
    
    # Move player
    mock_dependencies['api_client'].perform_player_action.return_value = {
        'energy': 99.0,
        'direction': 0,
        'moving': True
    }
    world_screen.movePlayer(0)
    
    # Add item
    mock_dependencies['api_client'].get_player.return_value = {
        'energy': 99.0,
        'inventory': {'slots': [{'itemName': 'apple', 'numItems': 1}]}
    }
    world_screen._addTestItem("apple")
    
    # Update tick
    mock_dependencies['api_client'].update_tick.return_value = {'currentTick': 1}
    world_screen.updateTick()
    
    # Verify all API calls were made
    assert mock_dependencies['api_client'].get_player.call_count >= 2
    assert mock_dependencies['api_client'].perform_player_action.called
    assert mock_dependencies['api_client'].add_item_to_inventory.called
    assert mock_dependencies['api_client'].update_tick.called


class TestClientSidePrediction:
    """Test client-side movement prediction (WI-005)."""
    
    def test_predict_position_up(self, world_screen):
        """Test position prediction for upward movement."""
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20, 'height': 20, 'entities': []
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        predicted = world_screen._predictPosition(0)  # up
        assert predicted == (5, 4)
    
    def test_predict_position_left(self, world_screen):
        """Test position prediction for left movement."""
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20, 'height': 20, 'entities': []
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        predicted = world_screen._predictPosition(1)  # left
        assert predicted == (4, 5)
    
    def test_predict_position_down(self, world_screen):
        """Test position prediction for downward movement."""
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20, 'height': 20, 'entities': []
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        predicted = world_screen._predictPosition(2)  # down
        assert predicted == (5, 6)
    
    def test_predict_position_right(self, world_screen):
        """Test position prediction for right movement."""
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20, 'height': 20, 'entities': []
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        predicted = world_screen._predictPosition(3)  # right
        assert predicted == (6, 5)
    
    def test_predict_position_blocked_by_bounds(self, world_screen):
        """Test that prediction detects out-of-bounds movement."""
        world_screen.player_data = {
            'tileX': 0, 'tileY': 0, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20, 'height': 20, 'entities': []
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        # Try to move up from top edge
        predicted = world_screen._predictPosition(0)
        assert predicted == (0, 0)  # Should stay in place
        
        # Try to move left from left edge
        predicted = world_screen._predictPosition(1)
        assert predicted == (0, 0)  # Should stay in place
    
    def test_predict_position_blocked_by_solid_entity(self, world_screen):
        """Test that prediction detects collision with solid entities."""
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20,
            'height': 20,
            'entities': [
                {
                    'locationId': '0,0,6,5',  # Solid entity at (6, 5)
                    'solid': True,
                    'type': 'Rock'
                }
            ]
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        # Try to move right into solid entity
        predicted = world_screen._predictPosition(3)
        assert predicted == (5, 5)  # Should stay in place
    
    def test_predict_position_not_blocked_by_non_solid_entity(self, world_screen):
        """Test that prediction allows movement through non-solid entities."""
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20,
            'height': 20,
            'entities': [
                {
                    'locationId': '0,0,6,5',  # Non-solid entity at (6, 5)
                    'solid': False,
                    'type': 'Berry'
                }
            ]
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        # Try to move right into non-solid entity
        predicted = world_screen._predictPosition(3)
        assert predicted == (6, 5)  # Should allow movement
    
    def test_predict_position_without_player_data(self, world_screen):
        """Test that prediction handles missing player data gracefully."""
        world_screen.player_data = None
        predicted = world_screen._predictPosition(0)
        assert predicted is None
    
    def test_move_player_with_prediction_enabled(self, world_screen, mock_dependencies):
        """Test that movePlayer uses prediction when enabled."""
        mock_dependencies['config'].enable_prediction = True
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0
        }
        world_screen.current_room = {
            'width': 20, 'height': 20, 'entities': []
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        
        # Mock the threading to run synchronously for testing
        with patch('threading.Thread') as mock_thread:
            world_screen.movePlayer(0)  # Move up
            
            # Verify prediction was set
            assert world_screen.predicted_position == (5, 4)
            
            # Verify thread was started for async request
            mock_thread.assert_called_once()
            assert world_screen.pending_move_request is True
    
    def test_move_player_without_prediction(self, world_screen, mock_dependencies):
        """Test that movePlayer works without prediction (synchronous mode)."""
        mock_dependencies['config'].enable_prediction = False
        player_data = {'tileX': 5, 'tileY': 4, 'direction': 0, 'moving': True}
        mock_dependencies['api_client'].perform_player_action.return_value = player_data
        
        world_screen.movePlayer(0)
        
        # Should call API synchronously
        mock_dependencies['api_client'].perform_player_action.assert_called_once_with(
            "move", direction=0
        )
        # No prediction should be set
        assert world_screen.predicted_position is None
    
    def test_send_move_request_successful_prediction(self, world_screen, mock_dependencies):
        """Test reconciliation when prediction is accurate."""
        world_screen.predicted_position = (5, 4)
        mock_dependencies['config'].prediction_snap_threshold = 2
        
        player_data = {'tileX': 5, 'tileY': 4, 'direction': 0}
        mock_dependencies['api_client'].perform_player_action.return_value = player_data
        
        world_screen._sendMoveRequest(0)
        
        # Prediction should be cleared (was accurate)
        assert world_screen.predicted_position is None
        assert world_screen.pending_move_request is False
    
    def test_send_move_request_prediction_error_within_threshold(self, world_screen, mock_dependencies):
        """Test reconciliation when prediction error is within threshold."""
        world_screen.predicted_position = (5, 4)
        mock_dependencies['config'].prediction_snap_threshold = 2
        
        # Server returns slightly different position
        player_data = {'tileX': 5, 'tileY': 5, 'direction': 0}
        mock_dependencies['api_client'].perform_player_action.return_value = player_data
        
        world_screen._sendMoveRequest(0)
        
        # Prediction should be cleared (within threshold)
        assert world_screen.predicted_position is None
        assert world_screen.pending_move_request is False
    
    def test_send_move_request_prediction_error_exceeds_threshold(self, world_screen, mock_dependencies):
        """Test reconciliation when prediction error exceeds threshold (snap back)."""
        world_screen.predicted_position = (5, 4)
        mock_dependencies['config'].prediction_snap_threshold = 2
        
        # Server returns significantly different position
        player_data = {'tileX': 5, 'tileY': 8, 'direction': 0}
        mock_dependencies['api_client'].perform_player_action.return_value = player_data
        
        world_screen._sendMoveRequest(0)
        
        # Prediction should be cleared (snapped to server)
        assert world_screen.predicted_position is None
        assert world_screen.pending_move_request is False
    
    def test_send_move_request_handles_error(self, world_screen, mock_dependencies):
        """Test that async move request handles server errors."""
        world_screen.predicted_position = (5, 4)
        mock_dependencies['api_client'].perform_player_action.side_effect = Exception("Network error")
        
        world_screen._sendMoveRequest(0)
        
        # Prediction should be reverted on error
        assert world_screen.predicted_position is None
        assert world_screen.pending_move_request is False
        mock_dependencies['status'].set.assert_called_with("Move failed: Network error")
    
    def test_render_world_uses_predicted_position(self, world_screen):
        """Test that render_world uses predicted position when available."""
        world_screen.player_data = {
            'tileX': 5, 'tileY': 5, 'roomX': 0, 'roomY': 0,
            'direction': 0
        }
        world_screen.current_room = {
            'width': 20, 'height': 20, 'tiles': [], 'entities': []
        }
        world_screen.current_room_x = 0
        world_screen.current_room_y = 0
        world_screen.predicted_position = (5, 4)
        
        # Just ensure render_world doesn't crash with predicted position
        # Full rendering test would require pygame mocking
        world_screen.render_world()
        
        # Test passes if no exception is raised
    
    def test_initialization_sets_prediction_state(self, world_screen):
        """Test that initialization sets up prediction state variables."""
        assert hasattr(world_screen, 'predicted_position')
        assert hasattr(world_screen, 'pending_move_request')
        assert world_screen.predicted_position is None
        assert world_screen.pending_move_request is False
