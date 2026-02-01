"""
WebSocket Client for Roam
Handles real-time communication with the Roam server using STOMP over WebSocket.

@author Daniel McCoy Stephenson
"""

import json
import logging
import threading
import time
from typing import Callable, Dict, Optional, Any
import websocket


logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    WebSocket client for receiving real-time game state updates from the server.
    Uses STOMP protocol over WebSocket for pub/sub messaging.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 60.0
    ):
        """
        Initialize the WebSocket client.
        
        Args:
            base_url: Base URL of the server (http://host:port)
            reconnect_base_delay: Initial delay between reconnection attempts (seconds)
            reconnect_max_delay: Maximum delay between reconnection attempts (seconds)
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ws_url = f"{ws_url}/ws/websocket"  # SockJS endpoint
        
        self.reconnect_base_delay = reconnect_base_delay
        self.reconnect_max_delay = reconnect_max_delay
        self.reconnect_attempts = 0
        
        # Connection state
        self.ws: Optional[websocket.WebSocketApp] = None
        self.connected = False
        self.should_reconnect = True
        self.session_id: Optional[str] = None
        
        # Threading
        self.ws_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Message handlers
        self.message_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        
        # STOMP protocol state
        self.stomp_session_id: Optional[str] = None
        self.subscription_id = 0
        self.subscriptions: Dict[str, int] = {}  # topic -> subscription_id
        
    def connect(self, session_id: str) -> bool:
        """
        Connect to the WebSocket server and subscribe to session topics.
        
        Args:
            session_id: Game session ID to subscribe to
            
        Returns:
            True if connection initiated successfully, False otherwise
        """
        with self.lock:
            if self.connected:
                logger.warning("WebSocket already connected")
                return True
            
            self.session_id = session_id
            self.should_reconnect = True
            self.reconnect_attempts = 0
            
            try:
                logger.info(f"Connecting to WebSocket at {self.ws_url}")
                
                # Create WebSocket app with callbacks
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                
                # Start WebSocket in a separate thread
                self.ws_thread = threading.Thread(
                    target=self._run_websocket,
                    daemon=True,
                    name="WebSocketThread"
                )
                self.ws_thread.start()
                
                # Wait a bit for connection to establish
                for _ in range(50):  # Wait up to 5 seconds
                    if self.connected:
                        return True
                    time.sleep(0.1)
                
                logger.warning("WebSocket connection timeout")
                return False
                
            except Exception as e:
                logger.error(f"Failed to connect to WebSocket: {e}", exc_info=True)
                return False
    
    def disconnect(self):
        """Disconnect from the WebSocket server."""
        with self.lock:
            logger.info("Disconnecting WebSocket")
            self.should_reconnect = False
            
            if self.ws:
                try:
                    # Send DISCONNECT frame
                    if self.connected:
                        disconnect_frame = "DISCONNECT\n\n\x00"
                        self.ws.send(disconnect_frame)
                except Exception as e:
                    logger.warning(f"Error sending disconnect frame: {e}")
                
                try:
                    self.ws.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
                
                self.ws = None
            
            self.connected = False
            self.stomp_session_id = None
            self.subscriptions.clear()
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.connected
    
    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message (TICK_UPDATE, PLAYER_POSITION, ENTITY_STATE, WORLD_EVENT)
            handler: Callback function that takes message data as argument
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    def _run_websocket(self):
        """Run the WebSocket connection (called in separate thread)."""
        while self.should_reconnect:
            try:
                logger.debug("Starting WebSocket run_forever")
                self.ws.run_forever()
                logger.debug("WebSocket run_forever exited")
            except Exception as e:
                logger.error(f"WebSocket error: {e}", exc_info=True)
            
            # Reconnection logic
            if self.should_reconnect and not self.connected:
                delay = min(
                    self.reconnect_base_delay * (2 ** self.reconnect_attempts),
                    self.reconnect_max_delay
                )
                self.reconnect_attempts += 1
                logger.info(f"Reconnecting in {delay:.1f} seconds (attempt {self.reconnect_attempts})")
                time.sleep(delay)
                
                # Recreate WebSocket app
                with self.lock:
                    if self.should_reconnect:
                        self.ws = websocket.WebSocketApp(
                            self.ws_url,
                            on_open=self._on_open,
                            on_message=self._on_message,
                            on_error=self._on_error,
                            on_close=self._on_close
                        )
    
    def _on_open(self, ws):
        """WebSocket on_open callback."""
        logger.info("WebSocket connection opened")
        
        # Send STOMP CONNECT frame
        connect_frame = (
            "CONNECT\n"
            "accept-version:1.1,1.2\n"
            "heart-beat:10000,10000\n"
            "\n"
            "\x00"
        )
        ws.send(connect_frame)
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket on_close callback."""
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        with self.lock:
            self.connected = False
            self.stomp_session_id = None
            self.subscriptions.clear()
    
    def _on_error(self, ws, error):
        """WebSocket on_error callback."""
        logger.error(f"WebSocket error: {error}")
    
    def _on_message(self, ws, message):
        """WebSocket on_message callback."""
        try:
            # Parse STOMP frame
            if not message:
                return
            
            # Handle heartbeat
            if message == "\n":
                return
            
            # Split frame into command and body
            parts = message.split("\n\n", 1)
            if len(parts) < 1:
                return
            
            header_part = parts[0]
            body = parts[1].rstrip("\x00") if len(parts) > 1 else ""
            
            # Parse command and headers
            lines = header_part.split("\n")
            if not lines:
                return
            
            command = lines[0]
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key] = value
            
            logger.debug(f"Received STOMP frame: {command}")
            
            # Handle different STOMP commands
            if command == "CONNECTED":
                self._handle_connected(headers)
            elif command == "MESSAGE":
                self._handle_message(headers, body)
            elif command == "ERROR":
                logger.error(f"STOMP error: {headers.get('message', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
    
    def _handle_connected(self, headers: Dict[str, str]):
        """Handle STOMP CONNECTED frame."""
        self.stomp_session_id = headers.get("session")
        logger.info(f"STOMP connected: session={self.stomp_session_id}")
        
        with self.lock:
            self.connected = True
            self.reconnect_attempts = 0
            
            # Subscribe to session topics
            if self.session_id:
                self._subscribe(f"/topic/session/{self.session_id}/tick")
                self._subscribe(f"/topic/session/{self.session_id}/player")
                self._subscribe(f"/topic/session/{self.session_id}/entity")
                self._subscribe(f"/topic/session/{self.session_id}/world")
    
    def _subscribe(self, topic: str):
        """
        Subscribe to a STOMP topic.
        
        Args:
            topic: Topic to subscribe to
        """
        if topic in self.subscriptions:
            logger.debug(f"Already subscribed to {topic}")
            return
        
        sub_id = self.subscription_id
        self.subscription_id += 1
        self.subscriptions[topic] = sub_id
        
        subscribe_frame = (
            f"SUBSCRIBE\n"
            f"id:{sub_id}\n"
            f"destination:{topic}\n"
            "\n"
            "\x00"
        )
        
        try:
            self.ws.send(subscribe_frame)
            logger.info(f"Subscribed to {topic} (id={sub_id})")
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
            del self.subscriptions[topic]
    
    def _handle_message(self, headers: Dict[str, str], body: str):
        """
        Handle STOMP MESSAGE frame.
        
        Args:
            headers: Message headers
            body: Message body (JSON)
        """
        try:
            if not body:
                return
            
            # Parse JSON message
            message_data = json.loads(body)
            message_type = message_data.get("type")
            
            if not message_type:
                logger.warning("Received message without type field")
                return
            
            logger.debug(f"Received message type: {message_type}")
            
            # Call registered handler
            handler = self.message_handlers.get(message_type)
            if handler:
                handler(message_data)
            else:
                logger.debug(f"No handler registered for message type: {message_type}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
