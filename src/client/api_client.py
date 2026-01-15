"""
Roam API Client
Python client for communicating with the Roam server REST API.

@author Daniel McCoy Stephenson
"""

import requests
from typing import Dict, Any, Optional


class RoamAPIClient:
    """Client for interacting with Roam server REST API."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the Roam server
        """
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the server.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Add authentication header if we have an access token
        # and this is not an auth endpoint
        if self.access_token and not endpoint.startswith("/api/v1/auth"):
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {self.access_token}"
            kwargs["headers"] = headers
        
        response = requests.request(method, url, **kwargs)
        
        # If we get a 401 and have a refresh token, try to refresh
        if response.status_code == 401 and self.refresh_token and not endpoint.startswith("/api/v1/auth"):
            try:
                self._refresh_access_token()
                # Retry the request with new token
                headers = kwargs.get("headers", {})
                headers["Authorization"] = f"Bearer {self.access_token}"
                kwargs["headers"] = headers
                response = requests.request(method, url, **kwargs)
            except Exception:
                pass  # Let the original error be raised
        
        response.raise_for_status()
        
        if response.status_code == 204:  # No content
            return {}
        
        return response.json()
    
    # Authentication Management
    
    def register(self, username: str, password: str, email: str) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            username: Username for the new account (3-50 characters)
            password: Password for the new account (minimum 6 characters)
            email: Email address for the new account
            
        Returns:
            Authentication response with tokens and user info
            
        Raises:
            requests.exceptions.HTTPError: If registration fails
        """
        response = self._make_request(
            "POST",
            "/api/v1/auth/register",
            json={
                "username": username,
                "password": password,
                "email": email
            }
        )
        
        # Store tokens for future requests
        self.access_token = response.get("accessToken")
        self.refresh_token = response.get("refreshToken")
        
        return response
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with existing user credentials.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authentication response with tokens and user info
            
        Raises:
            requests.exceptions.HTTPError: If login fails
        """
        response = self._make_request(
            "POST",
            "/api/v1/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        
        # Store tokens for future requests
        self.access_token = response.get("accessToken")
        self.refresh_token = response.get("refreshToken")
        
        return response
    
    def _refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            Authentication response with new tokens
            
        Raises:
            requests.exceptions.HTTPError: If refresh fails
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        response = self._make_request(
            "POST",
            "/api/v1/auth/refresh",
            json={
                "refreshToken": self.refresh_token
            }
        )
        
        # Update tokens
        self.access_token = response.get("accessToken")
        self.refresh_token = response.get("refreshToken")
        
        return response
    
    def logout(self) -> None:
        """
        Logout and revoke the current access token.
        
        Raises:
            requests.exceptions.HTTPError: If logout fails
        """
        if self.access_token:
            try:
                self._make_request("POST", "/api/v1/auth/logout")
            finally:
                # Clear tokens even if logout fails
                self.access_token = None
                self.refresh_token = None
    
    def is_authenticated(self) -> bool:
        """
        Check if the client is currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.access_token is not None
    
    # Session Management
    
    def init_session(self) -> Dict[str, Any]:
        """
        Initialize a new game session.
        
        Returns:
            Session data including sessionId, currentTick, and player
        """
        data = self._make_request("POST", "/api/v1/session/init", json={})
        self.session_id = data.get("sessionId")
        return data
    
    def get_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current session state.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Session data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("GET", f"/api/v1/session/{sid}")
    
    def delete_session(self, session_id: Optional[str] = None) -> None:
        """
        Delete a session.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        self._make_request("DELETE", f"/api/v1/session/{sid}")
        if sid == self.session_id:
            self.session_id = None
    
    def update_tick(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Update game tick.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated session data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("POST", f"/api/v1/session/{sid}/tick")
    
    def save_session(self, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Save the current game session to the database.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Response with success message
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("POST", f"/api/v1/session/{sid}/save")
    
    def load_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a game session from the database.
        
        Args:
            session_id: Session ID to load (uses stored session_id if not provided)
            
        Returns:
            Session data
            
        Raises:
            requests.exceptions.HTTPError: If session doesn't exist (404)
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        # Store the session ID for future requests
        self.session_id = sid
        return self._make_request("POST", f"/api/v1/session/{sid}/load")
    
    # Player Management
    
    def get_player(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get player state.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Player data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("GET", f"/api/v1/session/{sid}/player")
    
    def perform_player_action(
        self,
        action: str,
        direction: Optional[int] = None,
        item_name: Optional[str] = None,
        gathering: Optional[bool] = None,
        placing: Optional[bool] = None,
        crouching: Optional[bool] = None,
        tile_x: Optional[int] = None,
        tile_y: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a player action.
        
        Args:
            action: Action type (move, stop, gather, place, crouch, consume)
            direction: Movement direction (0=up, 1=left, 2=down, 3=right)
            item_name: Name of item (for consume action)
            gathering: Gathering state
            placing: Placing state
            crouching: Crouching state
            tile_x: Target tile X coordinate (for targeted gather/place)
            tile_y: Target tile Y coordinate (for targeted gather/place)
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated player data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        payload = {"action": action}
        if direction is not None:
            payload["direction"] = direction
        if item_name is not None:
            payload["itemName"] = item_name
        if gathering is not None:
            payload["gathering"] = gathering
        if placing is not None:
            payload["placing"] = placing
        if crouching is not None:
            payload["crouching"] = crouching
        if tile_x is not None:
            payload["tileX"] = tile_x
        if tile_y is not None:
            payload["tileY"] = tile_y
        
        return self._make_request(
            "POST",
            f"/api/v1/session/{sid}/player/action",
            json=payload
        )
    
    def update_player_energy(
        self,
        amount: float,
        operation: str = "add",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update player energy.
        
        Args:
            amount: Amount of energy to add/remove
            operation: Operation type ("add" or "remove")
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated player data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request(
            "PUT",
            f"/api/v1/session/{sid}/player/energy",
            params={"amount": amount, "operation": operation}
        )
    
    # Inventory Management
    
    def get_inventory(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get player inventory.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Inventory data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("GET", f"/api/v1/session/{sid}/inventory")
    
    def add_item_to_inventory(
        self,
        item_name: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add item to inventory.
        
        Args:
            item_name: Name of the item to add
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated inventory data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request(
            "POST",
            f"/api/v1/session/{sid}/inventory/add",
            params={"itemName": item_name}
        )
    
    def remove_item_from_inventory(
        self,
        item_name: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove item from inventory.
        
        Args:
            item_name: Name of the item to remove
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated inventory data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request(
            "POST",
            f"/api/v1/session/{sid}/inventory/remove",
            params={"itemName": item_name}
        )
    
    def select_inventory_slot(
        self,
        slot_index: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select an inventory slot.
        
        Args:
            slot_index: Index of the slot to select
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated inventory data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request(
            "PUT",
            f"/api/v1/session/{sid}/inventory/select",
            params={"slotIndex": slot_index}
        )
    
    def clear_inventory(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear inventory.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated inventory data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("DELETE", f"/api/v1/session/{sid}/inventory")
    
    def swap_inventory_slots(
        self,
        from_slot: int,
        to_slot: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Swap two inventory slots.
        
        Args:
            from_slot: Index of the first slot
            to_slot: Index of the second slot
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Updated inventory data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request(
            "POST",
            f"/api/v1/session/{sid}/inventory/swap",
            params={"fromSlot": from_slot, "toSlot": to_slot}
        )
    
    # World Management
    
    def get_world(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get world data including all loaded rooms.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            World data with configuration and rooms
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("GET", f"/api/v1/session/{sid}/world")
    
    def get_room(
        self,
        room_x: int,
        room_y: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a specific room by coordinates.
        Generates the room if it doesn't exist yet.
        
        Args:
            room_x: Room X coordinate
            room_y: Room Y coordinate
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            Room data with tiles
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("GET", f"/api/v1/session/{sid}/room/{room_x}/{room_y}")
    
    def get_entities(self, session_id: Optional[str] = None) -> list:
        """
        Get all entities in the session across all loaded rooms.
        
        Args:
            session_id: Session ID (uses stored session_id if not provided)
            
        Returns:
            List of entity data
        """
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        return self._make_request("GET", f"/api/v1/session/{sid}/entities")
