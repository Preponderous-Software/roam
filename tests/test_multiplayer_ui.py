"""
Simple validation test for new multiplayer API methods.
Tests the basic structure and signature of the new methods without requiring a server.
"""

import sys
import os
from unittest.mock import MagicMock

# Mock pygame before importing screens
sys.modules['pygame'] = MagicMock()
sys.modules['pygame.font'] = MagicMock()
sys.modules['pygame.scrap'] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from client.api_client import RoamAPIClient


def test_api_client_has_multiplayer_methods():
    """Test that RoamAPIClient has the new multiplayer methods."""
    client = RoamAPIClient("http://localhost:8080")
    
    # Check that methods exist
    assert hasattr(client, 'join_session'), "RoamAPIClient should have join_session method"
    assert hasattr(client, 'leave_session'), "RoamAPIClient should have leave_session method"
    assert hasattr(client, 'get_players'), "RoamAPIClient should have get_players method"
    
    # Check that methods are callable
    assert callable(client.join_session), "join_session should be callable"
    assert callable(client.leave_session), "leave_session should be callable"
    assert callable(client.get_players), "get_players should be callable"
    
    print("✓ All multiplayer methods exist and are callable")


def test_screen_types_exist():
    """Test that new screen types are defined."""
    from screen.screenType import ScreenType
    
    assert hasattr(ScreenType, 'JOIN_SESSION_SCREEN'), "ScreenType should have JOIN_SESSION_SCREEN"
    assert hasattr(ScreenType, 'SESSION_INFO_SCREEN'), "ScreenType should have SESSION_INFO_SCREEN"
    
    assert ScreenType.JOIN_SESSION_SCREEN == "join_session_screen"
    assert ScreenType.SESSION_INFO_SCREEN == "session_info_screen"
    
    print("✓ All new screen types are defined")


def test_screens_can_be_imported():
    """Test that new screen modules can be imported."""
    try:
        from screen.sessionInfoScreen import SessionInfoScreen
        print("✓ SessionInfoScreen can be imported")
    except ImportError as e:
        print(f"✗ Failed to import SessionInfoScreen: {e}")
        raise
    
    try:
        from screen.joinSessionScreen import JoinSessionScreen
        print("✓ JoinSessionScreen can be imported")
    except ImportError as e:
        print(f"✗ Failed to import JoinSessionScreen: {e}")
        raise


if __name__ == "__main__":
    print("Running multiplayer UI validation tests...\n")
    
    test_api_client_has_multiplayer_methods()
    test_screen_types_exist()
    test_screens_can_be_imported()
    
    print("\n✓ All validation tests passed!")
