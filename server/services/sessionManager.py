"""
Session Manager
Manages game sessions and world state persistence.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Optional
from server.services.worldGenerator import WorldGenerator


class SessionManager:
    """Manages game sessions and their associated world states"""
    
    def __init__(self, sessions_dir: str = "server/sessions"):
        """
        Initialize the session manager.
        
        Args:
            sessions_dir: Directory to store session data
        """
        self.sessions_dir = sessions_dir
        self.sessions: Dict[str, Dict] = {}
        self._ensure_sessions_dir()
        self._load_existing_sessions()
    
    def _ensure_sessions_dir(self):
        """Ensure the sessions directory exists"""
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def _get_session_file_path(self, session_id: str) -> str:
        """Get the file path for a session"""
        return os.path.join(self.sessions_dir, f"{session_id}.json")
    
    def _load_existing_sessions(self):
        """Load existing sessions from disk"""
        if not os.path.exists(self.sessions_dir):
            return
        
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(self.sessions_dir, filename), 'r') as f:
                        session_data = json.load(f)
                        self.sessions[session_id] = session_data
                except Exception as e:
                    print(f"Error loading session {session_id}: {e}")
    
    def create_session(self, seed: Optional[int] = None, grid_size: int = 17) -> Dict:
        """
        Create a new game session.
        
        Args:
            seed: Random seed for world generation
            grid_size: Size of the grid for each room
            
        Returns:
            Session data dictionary
        """
        session_id = str(uuid.uuid4())
        world_generator = WorldGenerator(seed=seed, grid_size=grid_size)
        world_config = world_generator.generate_world_config()
        
        session_data = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "world_config": world_config,
            "generated_rooms": {}  # Store generated room coordinates
        }
        
        self.sessions[session_id] = session_data
        self._save_session(session_id)
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            # Update last accessed time
            session["last_accessed"] = datetime.now().isoformat()
            self._save_session(session_id)
        return session
    
    def get_world_generator(self, session_id: str) -> Optional[WorldGenerator]:
        """
        Get world generator for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            WorldGenerator instance or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        world_config = session["world_config"]
        return WorldGenerator(
            seed=world_config["seed"],
            grid_size=world_config["grid_size"]
        )
    
    def mark_room_generated(self, session_id: str, x: int, y: int):
        """
        Mark a room as generated in the session.
        
        Args:
            session_id: Session identifier
            x: X coordinate
            y: Y coordinate
        """
        session = self.sessions.get(session_id)
        if session:
            coord_key = f"{x},{y}"
            session["generated_rooms"][coord_key] = {
                "x": x,
                "y": y,
                "generated_at": datetime.now().isoformat()
            }
            self._save_session(session_id)
    
    def list_sessions(self) -> list:
        """
        List all active sessions.
        
        Returns:
            List of session summaries
        """
        return [
            {
                "id": session_id,
                "created_at": session_data["created_at"],
                "last_accessed": session_data["last_accessed"],
                "seed": session_data["world_config"]["seed"]
            }
            for session_id, session_data in self.sessions.items()
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        if session_id not in self.sessions:
            return False
        
        # Remove from memory
        del self.sessions[session_id]
        
        # Remove from disk
        session_file = self._get_session_file_path(session_id)
        if os.path.exists(session_file):
            os.remove(session_file)
        
        return True
    
    def _save_session(self, session_id: str):
        """Save session data to disk"""
        session_data = self.sessions.get(session_id)
        if not session_data:
            return
        
        session_file = self._get_session_file_path(session_id)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
