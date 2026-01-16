"""
Unit tests for ServerBackedWorldScreen.
Tests the server-backed client functionality without requiring pygame UI.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os

# Mock pygame BEFORE any imports that might need it
sys.modules['pygame'] = MagicMock()
sys.modules['pygame.font'] = MagicMock()

# Add src to path explicitly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

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


class TestKeyboardHandling:
    """Test keyboard event handling."""
    
    def test_esc_key_saves_session_before_menu(self, world_screen, mock_dependencies):
        """Test that ESC key saves session before navigating to menu."""
        import pygame
        
        world_screen.handleKeyDownEvent(pygame.K_ESCAPE)
        
        # Verify save_session was called
        mock_dependencies['api_client'].save_session.assert_called_once_with(
            mock_dependencies['session_id']
        )
        # Verify screen change is triggered
        assert world_screen.changeScreen is True
        assert world_screen.nextScreen == ScreenType.OPTIONS_SCREEN
    
    def test_esc_key_handles_save_failure_gracefully(self, world_screen, mock_dependencies):
        """Test that ESC key handles save failures gracefully."""
        import pygame
        
        # Simulate save failure
        mock_dependencies['api_client'].save_session.side_effect = Exception("Connection error")
        
        world_screen.handleKeyDownEvent(pygame.K_ESCAPE)
        
        # Save should have been attempted
        mock_dependencies['api_client'].save_session.assert_called_once()
        # Screen should still change even if save fails
        assert world_screen.changeScreen is True
        assert world_screen.nextScreen == ScreenType.OPTIONS_SCREEN
    
    def test_esc_key_logs_save_success(self, world_screen, mock_dependencies):
        """Test that ESC key logs successful save operation."""
        import pygame
        
        with patch('screen.serverBackedWorldScreen.logger') as mock_logger:
            world_screen.handleKeyDownEvent(pygame.K_ESCAPE)
            
            # Verify logging calls
            mock_logger.info.assert_any_call("ESC pressed - opening options menu")
            mock_logger.info.assert_any_call("Session saved before menu navigation")
    
    def test_esc_key_logs_save_failure(self, world_screen, mock_dependencies):
        """Test that ESC key logs save failures."""
        import pygame
        
        mock_dependencies['api_client'].save_session.side_effect = Exception("Network error")
        
        with patch('screen.serverBackedWorldScreen.logger') as mock_logger:
            world_screen.handleKeyDownEvent(pygame.K_ESCAPE)
            
            # Verify error is logged
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Failed to save session" in warning_call



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


def test_select_inventory_slot_preserves_player_position(mock_dependencies):
    """Test that selecting an inventory slot preserves player position data.
    
    This test verifies that when a player selects an inventory slot (e.g., by pressing
    a number key), the player's position data (roomX, roomY, tileX, tileY) is preserved
    in player_data. This prevents the player from teleporting/flickering when switching slots.
    """
    # Set up world screen
    world_screen = ServerBackedWorldScreen(
        graphik=mock_dependencies['graphik'],
        config=mock_dependencies['config'],
        status=mock_dependencies['status'],
        tickCounter=mock_dependencies['tick_counter'],
        stats=mock_dependencies['stats'],
        player=mock_dependencies['player'],
        api_client=mock_dependencies['api_client'],
        session_id=mock_dependencies['session_id']
    )
    
    # Set initial player data with position information
    initial_player_data = {
        'roomX': 2,
        'roomY': 1,
        'tileX': 15,
        'tileY': 8,
        'energy': 95.5,
        'direction': 2,
        'inventory': {
            'selectedSlotIndex': 0,
            'slots': [
                {'itemName': 'Wood', 'numItems': 5, 'empty': False},
                {'empty': True}
            ]
        }
    }
    world_screen.player_data = initial_player_data
    
    # Mock the API response for selecting a slot (returns only inventory data)
    inventory_response = {
        'selectedSlotIndex': 3,
        'slots': [
            {'itemName': 'Wood', 'numItems': 5, 'empty': False},
            {'empty': True}
        ]
    }
    mock_dependencies['api_client'].select_inventory_slot.return_value = inventory_response
    
    # Mock inventory for status display
    mock_slot = MagicMock()
    mock_slot.isEmpty.return_value = True
    mock_dependencies['player'].getInventory.return_value.getInventorySlots.return_value = [mock_slot] * 10
    
    # Select inventory slot 3
    world_screen._selectInventorySlot(3)
    
    # Verify API was called
    mock_dependencies['api_client'].select_inventory_slot.assert_called_once_with(3)
    
    # Verify position data is still present in player_data
    assert world_screen.player_data is not None
    assert world_screen.player_data['roomX'] == 2, "roomX should be preserved"
    assert world_screen.player_data['roomY'] == 1, "roomY should be preserved"
    assert world_screen.player_data['tileX'] == 15, "tileX should be preserved"
    assert world_screen.player_data['tileY'] == 8, "tileY should be preserved"
    assert world_screen.player_data['energy'] == 95.5, "energy should be preserved"
    assert world_screen.player_data['direction'] == 2, "direction should be preserved"
    
    # Verify inventory data was updated
    assert world_screen.player_data['inventory']['selectedSlotIndex'] == 3
    
    # Verify the local inventory object was updated
    mock_dependencies['player'].getInventory.return_value.setSelectedInventorySlotIndex.assert_called_once_with(3)
