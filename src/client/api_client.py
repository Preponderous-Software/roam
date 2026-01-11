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
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        
        if response.status_code == 204:  # No content
            return {}
        
        return response.json()
    
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
