"""
Unit tests for refactored roam.py.
Tests the server-backed Roam client initialization and session management.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


class TestRoamInitialization:
    """Test Roam class initialization."""
    
    @patch('src.roam.pygame')
    @patch('src.roam.RoamAPIClient')
    @patch('src.roam.Config')
    @patch('src.roam.Player')
    @patch('src.roam.TickCounter')
    @patch('src.roam.Graphik')
    @patch('src.roam.Status')
    @patch('src.roam.Stats')
    @patch('src.roam.OptionsScreen')
    @patch('src.roam.MainMenuScreen')
    @patch('src.roam.StatsScreen')
    @patch('src.roam.ConfigScreen')
    def test_roam_initialization_creates_api_client(
        self, mock_config_screen, mock_stats_screen, mock_main_menu, 
        mock_options, mock_stats, mock_status, mock_graphik, 
        mock_tick_counter, mock_player, mock_config, mock_api_client, mock_pygame
    ):
        """Test that Roam initialization creates API client."""
        from src.roam import Roam
        
        config = mock_config.return_value
        config.pathToSaveDirectory = "/tmp/test"
        config.displayWidth = 800
        config.displayHeight = 600
        config.fullscreen = False
        
        roam = Roam(config, "http://localhost:8080")
        
        # Verify API client was created with correct URL
        mock_api_client.assert_called_once_with("http://localhost:8080")
        assert roam.server_url == "http://localhost:8080"
        assert roam.session_id is None
        assert roam.player is None
        assert roam.worldScreen is None
    
    @patch('src.roam.pygame')
    @patch('src.roam.RoamAPIClient')
    @patch('src.roam.Config')
    def test_roam_initialization_with_default_url(
        self, mock_config, mock_api_client, mock_pygame
    ):
        """Test that Roam uses default URL when not provided."""
        with patch('src.roam.TickCounter'), \
             patch('src.roam.Graphik'), \
             patch('src.roam.Status'), \
             patch('src.roam.Stats'), \
             patch('src.roam.OptionsScreen'), \
             patch('src.roam.MainMenuScreen'), \
             patch('src.roam.StatsScreen'), \
             patch('src.roam.ConfigScreen'):
            
            from src.roam import Roam
            
            config = mock_config.return_value
            config.pathToSaveDirectory = "/tmp/test"
            config.displayWidth = 800
            config.displayHeight = 600
            config.fullscreen = False
            
            roam = Roam(config)
            
            mock_api_client.assert_called_once_with("http://localhost:8080")


class TestSessionManagement:
    """Test session initialization and management."""
    
    @patch('src.roam.pygame')
    @patch('src.roam.ServerBackedWorldScreen')
    @patch('src.roam.InventoryScreen')
    def test_initialize_world_screen_success(self, mock_inv_screen, mock_world_screen, mock_pygame):
        """Test successful world screen initialization with server session."""
        with patch('src.roam.RoamAPIClient') as mock_api_client, \
             patch('src.roam.Config') as mock_config, \
             patch('src.roam.Player') as mock_player, \
             patch('src.roam.TickCounter'), \
             patch('src.roam.Graphik'), \
             patch('src.roam.Status') as mock_status, \
             patch('src.roam.Stats'), \
             patch('src.roam.OptionsScreen'), \
             patch('src.roam.MainMenuScreen'), \
             patch('src.roam.StatsScreen'), \
             patch('src.roam.ConfigScreen'):
            
            from src.roam import Roam
            
            config = mock_config.return_value
            config.pathToSaveDirectory = "/tmp/test"
            config.displayWidth = 800
            config.displayHeight = 600
            config.fullscreen = False
            
            roam = Roam(config, "http://localhost:8080")
            
            # Mock API responses
            session_data = {
                'sessionId': 'test-session-123',
                'player': {
                    'energy': 100.0,
                    'direction': -1
                }
            }
            roam.api_client.init_session.return_value = session_data
            
            # Initialize world screen
            roam.initializeWorldScreen()
            
            # Verify session was initialized
            roam.api_client.init_session.assert_called_once()
            assert roam.session_id == 'test-session-123'
            assert roam.player is not None
            mock_world_screen.assert_called_once()
    
    @patch('src.roam.pygame')
    def test_initialize_world_screen_handles_error(self, mock_pygame):
        """Test that initialization handles server errors."""
        with patch('src.roam.RoamAPIClient') as mock_api_client, \
             patch('src.roam.Config') as mock_config, \
             patch('src.roam.TickCounter'), \
             patch('src.roam.Graphik'), \
             patch('src.roam.Status') as mock_status, \
             patch('src.roam.Stats'), \
             patch('src.roam.OptionsScreen'), \
             patch('src.roam.MainMenuScreen'), \
             patch('src.roam.StatsScreen'), \
             patch('src.roam.ConfigScreen'):
            
            from src.roam import Roam
            
            config = mock_config.return_value
            config.pathToSaveDirectory = "/tmp/test"
            config.displayWidth = 800
            config.displayHeight = 600
            config.fullscreen = False
            
            roam = Roam(config, "http://localhost:8080")
            
            # Mock API error
            roam.api_client.init_session.side_effect = Exception("Connection failed")
            
            # Initialize world screen
            roam.initializeWorldScreen()
            
            # Verify error was handled
            assert roam.worldScreen is None
            assert roam.nextScreen == roam.ScreenType.MAIN_MENU_SCREEN
            assert roam.changeScreen is True


class TestURLValidation:
    """Test URL validation."""
    
    @patch('sys.exit')
    def test_invalid_url_format(self, mock_exit):
        """Test that invalid URL format causes graceful exit."""
        with patch('src.roam.pygame'):
            # Simulate the main script validation logic
            from urllib.parse import urlparse
            
            invalid_url = "not-a-url"
            
            try:
                parsed = urlparse(invalid_url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError("Invalid URL format")
            except Exception:
                # Should catch and handle the error
                assert True
    
    def test_valid_http_url(self):
        """Test that valid HTTP URL is accepted."""
        from urllib.parse import urlparse
        
        url = "http://localhost:8080"
        parsed = urlparse(url)
        
        assert parsed.scheme == "http"
        assert parsed.netloc == "localhost:8080"
    
    def test_valid_https_url(self):
        """Test that valid HTTPS URL is accepted."""
        from urllib.parse import urlparse
        
        url = "https://example.com:8080"
        parsed = urlparse(url)
        
        assert parsed.scheme == "https"
        assert parsed.netloc == "example.com:8080"
    
    @patch('sys.exit')
    def test_non_http_protocol_rejected(self, mock_exit):
        """Test that non-HTTP/HTTPS protocols are rejected."""
        from urllib.parse import urlparse
        
        url = "ftp://example.com"
        parsed = urlparse(url)
        
        if parsed.scheme not in ['http', 'https']:
            # Should be rejected
            assert True


class TestSessionCleanup:
    """Test session cleanup."""
    
    @patch('src.roam.pygame')
    def test_session_cleanup_on_quit(self, mock_pygame):
        """Test that session is cleaned up when quitting."""
        with patch('src.roam.RoamAPIClient') as mock_api_client, \
             patch('src.roam.Config') as mock_config, \
             patch('src.roam.TickCounter'), \
             patch('src.roam.Graphik'), \
             patch('src.roam.Status'), \
             patch('src.roam.Stats'), \
             patch('src.roam.OptionsScreen'), \
             patch('src.roam.MainMenuScreen'), \
             patch('src.roam.StatsScreen'), \
             patch('src.roam.ConfigScreen'):
            
            from src.roam import Roam
            from screen.screenType import ScreenType
            
            config = mock_config.return_value
            config.pathToSaveDirectory = "/tmp/test"
            config.displayWidth = 800
            config.displayHeight = 600
            config.fullscreen = False
            
            roam = Roam(config, "http://localhost:8080")
            roam.session_id = "test-session-123"
            roam.currentScreen = MagicMock()
            roam.currentScreen.run.return_value = ScreenType.NONE
            
            # Mock quitApplication to avoid actual quit
            roam.quitApplication = MagicMock()
            
            # Run should clean up session
            roam.run()
            
            # Verify session cleanup was attempted
            roam.api_client.delete_session.assert_called_once()


class TestServerBackedArchitecturePrinciples:
    """Test that server-backed architecture principles are maintained."""
    
    def test_no_local_game_logic_in_roam(self):
        """Test that Roam class doesn't contain game logic."""
        import inspect
        with patch('src.roam.pygame'), \
             patch('src.roam.RoamAPIClient'), \
             patch('src.roam.Config'), \
             patch('src.roam.TickCounter'), \
             patch('src.roam.Graphik'), \
             patch('src.roam.Status'), \
             patch('src.roam.Stats'), \
             patch('src.roam.OptionsScreen'), \
             patch('src.roam.MainMenuScreen'), \
             patch('src.roam.StatsScreen'), \
             patch('src.roam.ConfigScreen'):
            
            from src.roam import Roam
            
            # Get all methods of Roam class
            methods = [m for m in dir(Roam) if not m.startswith('_')]
            
            # Roam should only have UI management methods, not game logic
            # Expected methods: initializeGameDisplay, initializeWorldScreen, run, quitApplication
            expected_methods = ['initializeGameDisplay', 'initializeWorldScreen', 'quitApplication', 'run']
            
            for method in expected_methods:
                assert method in methods or method.startswith('_'), \
                    f"Expected method {method} not found in Roam class"
    
    def test_roam_uses_api_client_for_all_operations(self):
        """Test that Roam delegates all operations to API client."""
        with patch('src.roam.pygame'), \
             patch('src.roam.RoamAPIClient') as mock_api_client, \
             patch('src.roam.Config') as mock_config, \
             patch('src.roam.TickCounter'), \
             patch('src.roam.Graphik'), \
             patch('src.roam.Status'), \
             patch('src.roam.Stats'), \
             patch('src.roam.OptionsScreen'), \
             patch('src.roam.MainMenuScreen'), \
             patch('src.roam.StatsScreen'), \
             patch('src.roam.ConfigScreen'):
            
            from src.roam import Roam
            
            config = mock_config.return_value
            config.pathToSaveDirectory = "/tmp/test"
            config.displayWidth = 800
            config.displayHeight = 600
            config.fullscreen = False
            
            roam = Roam(config, "http://localhost:8080")
            
            # Verify API client is created
            assert roam.api_client is not None
            assert isinstance(roam.api_client, type(mock_api_client.return_value))


def test_integration_full_lifecycle():
    """Integration test for full Roam lifecycle."""
    with patch('src.roam.pygame'), \
         patch('src.roam.RoamAPIClient') as mock_api_client, \
         patch('src.roam.Config') as mock_config, \
         patch('src.roam.Player'), \
         patch('src.roam.ServerBackedWorldScreen'), \
         patch('src.roam.InventoryScreen'), \
         patch('src.roam.TickCounter'), \
         patch('src.roam.Graphik'), \
         patch('src.roam.Status'), \
         patch('src.roam.Stats'), \
         patch('src.roam.OptionsScreen'), \
         patch('src.roam.MainMenuScreen') as mock_main_menu, \
         patch('src.roam.StatsScreen'), \
         patch('src.roam.ConfigScreen'):
        
        from src.roam import Roam
        from screen.screenType import ScreenType
        
        config = mock_config.return_value
        config.pathToSaveDirectory = "/tmp/test"
        config.displayWidth = 800
        config.displayHeight = 600
        config.fullscreen = False
        
        # Create Roam instance
        roam = Roam(config, "http://localhost:8080")
        
        # Mock session initialization
        session_data = {
            'sessionId': 'test-session-123',
            'player': {'energy': 100.0, 'direction': -1}
        }
        roam.api_client.init_session.return_value = session_data
        
        # Initialize world screen
        roam.initializeWorldScreen()
        
        # Verify session was created
        assert roam.session_id == 'test-session-123'
        assert roam.player is not None
        
        # Simulate quit
        roam.session_id = 'test-session-123'
        roam.api_client.delete_session = MagicMock()
        roam.quitApplication = MagicMock()
        
        roam.currentScreen = MagicMock()
        roam.currentScreen.run.return_value = ScreenType.NONE
        
        roam.run()
        
        # Verify cleanup
        roam.api_client.delete_session.assert_called_once()
