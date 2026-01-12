"""
Unit tests for InventoryScreen.
Tests the inventory screen functionality with server-backed inventory.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock pygame BEFORE any imports that might need it
sys.modules['pygame'] = MagicMock()

# Add src to path explicitly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from screen.inventoryScreen import InventoryScreen
from screen.screenType import ScreenType


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for InventoryScreen."""
    graphik = MagicMock()
    graphik.getGameDisplay.return_value = MagicMock()
    graphik.getGameDisplay.return_value.get_width.return_value = 800
    graphik.getGameDisplay.return_value.get_height.return_value = 600
    
    config = MagicMock()
    status = MagicMock()
    inventory = MagicMock()
    inventory.getInventorySlots.return_value = [MagicMock() for _ in range(25)]
    api_client = MagicMock()
    session_id = "test-session-123"
    
    return {
        'graphik': graphik,
        'config': config,
        'status': status,
        'inventory': inventory,
        'api_client': api_client,
        'session_id': session_id
    }


@pytest.fixture
def inventory_screen(mock_dependencies):
    """Create an InventoryScreen instance with mocked dependencies."""
    return InventoryScreen(
        mock_dependencies['graphik'],
        mock_dependencies['config'],
        mock_dependencies['status'],
        mock_dependencies['inventory'],
        mock_dependencies['api_client'],
        mock_dependencies['session_id']
    )


class TestInventoryScreenInitialization:
    """Test initialization of InventoryScreen."""
    
    def test_constructor_sets_attributes(self, inventory_screen, mock_dependencies):
        """Test that constructor properly sets all attributes."""
        assert inventory_screen.graphik == mock_dependencies['graphik']
        assert inventory_screen.config == mock_dependencies['config']
        assert inventory_screen.status == mock_dependencies['status']
        assert inventory_screen.inventory == mock_dependencies['inventory']
        assert inventory_screen.api_client == mock_dependencies['api_client']
        assert inventory_screen.session_id == mock_dependencies['session_id']
        assert inventory_screen.changeScreen is False
        assert inventory_screen.nextScreen == ScreenType.WORLD_SCREEN
    
    def test_constructor_without_api_client(self, mock_dependencies):
        """Test that constructor works without API client (backward compatibility)."""
        screen = InventoryScreen(
            mock_dependencies['graphik'],
            mock_dependencies['config'],
            mock_dependencies['status'],
            mock_dependencies['inventory']
        )
        assert screen.api_client is None
        assert screen.session_id is None


class TestInventoryFetching:
    """Test inventory fetching from server."""
    
    def test_fetch_inventory_from_server_success(self, inventory_screen, mock_dependencies):
        """Test successful inventory fetch from server."""
        # Mock server response
        mock_player_data = {
            'inventory': {
                'slots': [
                    {'empty': False, 'itemName': 'Wood', 'numItems': 5},
                    {'empty': True, 'itemName': None, 'numItems': 0}
                ],
                'selectedSlotIndex': 0
            }
        }
        mock_dependencies['api_client'].get_player.return_value = mock_player_data
        
        # Fetch inventory
        inventory_screen.fetchInventoryFromServer()
        
        # Verify API call was made
        mock_dependencies['api_client'].get_player.assert_called_once_with(
            mock_dependencies['session_id']
        )
        
        # Verify inventory data was stored
        assert inventory_screen.server_inventory_data is not None
        assert len(inventory_screen.server_inventory_data['slots']) == 2
        assert inventory_screen.server_inventory_data['slots'][0]['itemName'] == 'Wood'
    
    def test_fetch_inventory_from_server_error(self, inventory_screen, mock_dependencies):
        """Test inventory fetch handles server errors."""
        # Mock server error
        mock_dependencies['api_client'].get_player.side_effect = Exception("Connection failed")
        
        # Fetch inventory
        inventory_screen.fetchInventoryFromServer()
        
        # Verify error was handled
        assert inventory_screen.server_inventory_data is None
    
    def test_fetch_inventory_without_api_client(self, mock_dependencies):
        """Test inventory fetch without API client."""
        screen = InventoryScreen(
            mock_dependencies['graphik'],
            mock_dependencies['config'],
            mock_dependencies['status'],
            mock_dependencies['inventory']
        )
        
        # Fetch inventory
        screen.fetchInventoryFromServer()
        
        # Verify no server call was made
        assert screen.server_inventory_data is None


class TestInventoryInteractions:
    """Test inventory interaction restrictions."""
    
    def test_swap_disabled_with_server_inventory(self, inventory_screen):
        """Test that swapping is disabled when using server inventory."""
        # Set server inventory data
        inventory_screen.server_inventory_data = {'slots': []}
        
        # Attempt swap
        inventory_screen.swapCursorSlotWithInventorySlotByIndex(0)
        
        # Verify status message was set
        inventory_screen.status.set.assert_called_with("Inventory interaction disabled (server mode)")
    
    def test_mouse_click_disabled_with_server_inventory(self, inventory_screen):
        """Test that mouse clicks are disabled when using server inventory."""
        # Set server inventory data
        inventory_screen.server_inventory_data = {'slots': []}
        
        # Attempt mouse click
        inventory_screen.handleMouseClickEvent((100, 100))
        
        # Verify status message was set
        inventory_screen.status.set.assert_called_with("Inventory interaction disabled (server mode)")


class TestInventoryDisplay:
    """Test inventory display functionality."""
    
    def test_uses_server_inventory_when_available(self, inventory_screen, mock_dependencies):
        """Test that drawPlayerInventory uses server data when available."""
        # Set server inventory data
        inventory_screen.server_inventory_data = {
            'slots': [
                {'empty': False, 'itemName': 'Wood', 'numItems': 5},
                {'empty': True, 'itemName': None, 'numItems': 0}
            ],
            'selectedSlotIndex': 0
        }
        
        # Draw inventory
        inventory_screen.drawPlayerInventory()
        
        # Verify drawing methods were called
        assert mock_dependencies['graphik'].drawRectangle.called
        assert mock_dependencies['graphik'].drawText.called
    
    def test_falls_back_to_local_inventory(self, inventory_screen, mock_dependencies):
        """Test that drawPlayerInventory falls back to local inventory."""
        # No server inventory data
        inventory_screen.server_inventory_data = None
        
        # Mock local inventory slots
        mock_slot = MagicMock()
        mock_slot.isEmpty.return_value = True
        mock_dependencies['inventory'].getInventorySlots.return_value = [mock_slot] * 25
        mock_dependencies['inventory'].getSelectedInventorySlotIndex.return_value = 0
        
        # Draw inventory
        inventory_screen.drawPlayerInventory()
        
        # Verify local inventory was accessed
        mock_dependencies['inventory'].getInventorySlots.assert_called()
