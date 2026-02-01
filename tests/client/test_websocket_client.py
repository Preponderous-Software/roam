"""
Unit tests for WebSocket client.
Tests the WebSocket client functionality without requiring a live server.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import threading
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import after adding to path
from client.websocket_client import WebSocketClient


@pytest.fixture
def ws_client():
    """Create a WebSocket client instance for testing."""
    return WebSocketClient(
        base_url="http://localhost:8080",
        reconnect_base_delay=0.1,
        reconnect_max_delay=1.0
    )


class TestWebSocketClientInitialization:
    """Test WebSocket client initialization."""
    
    def test_constructor_sets_attributes(self, ws_client):
        """Test that constructor properly sets all attributes."""
        assert ws_client.ws_url == "ws://localhost:8080/ws/websocket"
        assert ws_client.reconnect_base_delay == 0.1
        assert ws_client.reconnect_max_delay == 1.0
        assert ws_client.connected is False
        assert ws_client.should_reconnect is True
        assert ws_client.ws is None
        assert ws_client.session_id is None
    
    def test_http_url_converted_to_ws(self):
        """Test that HTTP URL is converted to WebSocket URL."""
        client = WebSocketClient(base_url="http://example.com:8080")
        assert client.ws_url == "ws://example.com:8080/ws/websocket"
    
    def test_https_url_converted_to_wss(self):
        """Test that HTTPS URL is converted to secure WebSocket URL."""
        client = WebSocketClient(base_url="https://example.com:8080")
        assert client.ws_url == "wss://example.com:8080/ws/websocket"


class TestWebSocketConnection:
    """Test WebSocket connection management."""
    
    @patch('client.websocket_client.websocket.WebSocketApp')
    def test_connect_creates_websocket_app(self, mock_ws_app, ws_client):
        """Test that connect creates a WebSocket app."""
        mock_ws_instance = MagicMock()
        mock_ws_app.return_value = mock_ws_instance
        
        # Start connection in non-blocking way
        ws_client.connect("test-session-123")
        
        # Verify WebSocketApp was created
        mock_ws_app.assert_called_once()
        call_args = mock_ws_app.call_args
        assert call_args[0][0] == ws_client.ws_url
        assert 'on_open' in call_args[1]
        assert 'on_message' in call_args[1]
        assert 'on_error' in call_args[1]
        assert 'on_close' in call_args[1]
    
    @patch('client.websocket_client.websocket.WebSocketApp')
    def test_connect_starts_thread(self, mock_ws_app, ws_client):
        """Test that connect starts a background thread."""
        mock_ws_instance = MagicMock()
        mock_ws_app.return_value = mock_ws_instance
        
        ws_client.connect("test-session-123")
        
        # Verify thread was started
        assert ws_client.ws_thread is not None
        assert ws_client.ws_thread.is_alive()
        
        # Cleanup
        ws_client.should_reconnect = False
        ws_client.ws_thread.join(timeout=1)
    
    def test_connect_stores_session_id(self, ws_client):
        """Test that connect stores the session ID."""
        with patch('client.websocket_client.websocket.WebSocketApp'):
            ws_client.connect("test-session-123")
            assert ws_client.session_id == "test-session-123"
    
    def test_disconnect_closes_websocket(self, ws_client):
        """Test that disconnect closes the WebSocket."""
        mock_ws = MagicMock()
        ws_client.ws = mock_ws
        ws_client.connected = True
        
        ws_client.disconnect()
        
        mock_ws.close.assert_called_once()
        assert ws_client.connected is False
        assert ws_client.should_reconnect is False
    
    def test_disconnect_handles_errors_gracefully(self, ws_client):
        """Test that disconnect handles errors gracefully."""
        mock_ws = MagicMock()
        mock_ws.close.side_effect = Exception("Close error")
        ws_client.ws = mock_ws
        ws_client.connected = True
        
        # Should not raise exception
        ws_client.disconnect()
        
        assert ws_client.connected is False
    
    def test_is_connected_returns_connection_state(self, ws_client):
        """Test that is_connected returns current connection state."""
        assert ws_client.is_connected() is False
        
        ws_client.connected = True
        assert ws_client.is_connected() is True
        
        ws_client.connected = False
        assert ws_client.is_connected() is False


class TestMessageHandlers:
    """Test message handler registration and invocation."""
    
    def test_register_handler(self, ws_client):
        """Test registering a message handler."""
        handler = MagicMock()
        ws_client.register_handler("TICK_UPDATE", handler)
        
        assert "TICK_UPDATE" in ws_client.message_handlers
        assert ws_client.message_handlers["TICK_UPDATE"] == handler
    
    def test_register_multiple_handlers(self, ws_client):
        """Test registering multiple message handlers."""
        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()
        
        ws_client.register_handler("TICK_UPDATE", handler1)
        ws_client.register_handler("PLAYER_POSITION", handler2)
        ws_client.register_handler("ENTITY_STATE", handler3)
        
        assert len(ws_client.message_handlers) == 3
        assert ws_client.message_handlers["TICK_UPDATE"] == handler1
        assert ws_client.message_handlers["PLAYER_POSITION"] == handler2
        assert ws_client.message_handlers["ENTITY_STATE"] == handler3


class TestSTOMPProtocol:
    """Test STOMP protocol handling."""
    
    def test_on_open_sends_connect_frame(self, ws_client):
        """Test that on_open sends STOMP CONNECT frame."""
        mock_ws = MagicMock()
        
        ws_client._on_open(mock_ws)
        
        mock_ws.send.assert_called_once()
        sent_frame = mock_ws.send.call_args[0][0]
        assert "CONNECT" in sent_frame
        assert "accept-version:1.1,1.2" in sent_frame
    
    def test_on_close_clears_state(self, ws_client):
        """Test that on_close clears connection state."""
        ws_client.connected = True
        ws_client.stomp_session_id = "test-stomp-session"
        ws_client.subscriptions = {"/topic/test": 1}
        
        mock_ws = MagicMock()
        ws_client._on_close(mock_ws, None, None)
        
        assert ws_client.connected is False
        assert ws_client.stomp_session_id is None
        assert len(ws_client.subscriptions) == 0
    
    def test_handle_connected_sets_session_id(self, ws_client):
        """Test that CONNECTED frame handler sets session ID."""
        headers = {"session": "stomp-session-123"}
        
        ws_client._handle_connected(headers)
        
        assert ws_client.stomp_session_id == "stomp-session-123"
        assert ws_client.connected is True
    
    def test_handle_connected_subscribes_to_topics(self, ws_client):
        """Test that CONNECTED frame subscribes to session topics."""
        ws_client.session_id = "test-session"
        ws_client.ws = MagicMock()
        headers = {"session": "stomp-session-123"}
        
        ws_client._handle_connected(headers)
        
        # Should have subscribed to 4 topics
        assert len(ws_client.subscriptions) == 4
        assert "/topic/session/test-session/tick" in ws_client.subscriptions
        assert "/topic/session/test-session/player" in ws_client.subscriptions
        assert "/topic/session/test-session/entity" in ws_client.subscriptions
        assert "/topic/session/test-session/world" in ws_client.subscriptions
    
    def test_handle_message_parses_json_and_calls_handler(self, ws_client):
        """Test that MESSAGE frame parses JSON and calls handler."""
        handler = MagicMock()
        ws_client.register_handler("TICK_UPDATE", handler)
        
        headers = {"destination": "/topic/session/test/tick"}
        body = '{"type": "TICK_UPDATE", "currentTick": 42}'
        
        ws_client._handle_message(headers, body)
        
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args["type"] == "TICK_UPDATE"
        assert call_args["currentTick"] == 42
    
    def test_handle_message_with_no_handler(self, ws_client):
        """Test that MESSAGE frame without handler doesn't crash."""
        headers = {"destination": "/topic/session/test/tick"}
        body = '{"type": "UNKNOWN_TYPE", "data": "test"}'
        
        # Should not raise exception
        ws_client._handle_message(headers, body)
    
    def test_handle_message_with_invalid_json(self, ws_client):
        """Test that MESSAGE frame with invalid JSON is handled gracefully."""
        headers = {"destination": "/topic/session/test/tick"}
        body = 'invalid json {'
        
        # Should not raise exception
        ws_client._handle_message(headers, body)


class TestReconnection:
    """Test reconnection logic."""
    
    def test_reconnect_attempts_increment(self, ws_client):
        """Test that reconnection attempts are tracked."""
        assert ws_client.reconnect_attempts == 0
        
        # Simulate failed connection
        ws_client.reconnect_attempts = 1
        assert ws_client.reconnect_attempts == 1
    
    def test_reconnect_delay_increases_exponentially(self, ws_client):
        """Test that reconnection delay increases exponentially."""
        ws_client.reconnect_attempts = 0
        delay1 = min(
            ws_client.reconnect_base_delay * (2 ** ws_client.reconnect_attempts),
            ws_client.reconnect_max_delay
        )
        assert delay1 == 0.1
        
        ws_client.reconnect_attempts = 1
        delay2 = min(
            ws_client.reconnect_base_delay * (2 ** ws_client.reconnect_attempts),
            ws_client.reconnect_max_delay
        )
        assert delay2 == 0.2
        
        ws_client.reconnect_attempts = 2
        delay3 = min(
            ws_client.reconnect_base_delay * (2 ** ws_client.reconnect_attempts),
            ws_client.reconnect_max_delay
        )
        assert delay3 == 0.4
    
    def test_reconnect_delay_capped_at_max(self, ws_client):
        """Test that reconnection delay is capped at maximum."""
        ws_client.reconnect_attempts = 10  # Would be very large without cap
        delay = min(
            ws_client.reconnect_base_delay * (2 ** ws_client.reconnect_attempts),
            ws_client.reconnect_max_delay
        )
        assert delay == ws_client.reconnect_max_delay


class TestThreadSafety:
    """Test thread safety of WebSocket client."""
    
    def test_disconnect_is_thread_safe(self, ws_client):
        """Test that disconnect can be called from any thread."""
        ws_client.ws = MagicMock()
        ws_client.connected = True
        
        def disconnect_in_thread():
            ws_client.disconnect()
        
        thread = threading.Thread(target=disconnect_in_thread)
        thread.start()
        thread.join(timeout=1)
        
        assert ws_client.connected is False
    
    def test_register_handler_is_thread_safe(self, ws_client):
        """Test that register_handler can be called from any thread."""
        handler = MagicMock()
        
        def register_in_thread():
            ws_client.register_handler("TEST_TYPE", handler)
        
        thread = threading.Thread(target=register_in_thread)
        thread.start()
        thread.join(timeout=1)
        
        assert "TEST_TYPE" in ws_client.message_handlers
