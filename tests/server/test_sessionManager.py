"""Tests for the session manager service"""
import pytest
import os
import shutil
from server.services.sessionManager import SessionManager


@pytest.fixture
def temp_sessions_dir(tmp_path):
    """Create a temporary directory for sessions"""
    sessions_dir = tmp_path / "test_sessions"
    sessions_dir.mkdir()
    yield str(sessions_dir)
    # Cleanup after test
    if sessions_dir.exists():
        shutil.rmtree(sessions_dir)


def test_session_manager_initialization(temp_sessions_dir):
    """Test session manager initializes correctly"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    assert os.path.exists(temp_sessions_dir)
    assert len(manager.sessions) == 0


def test_create_session(temp_sessions_dir):
    """Test session creation"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session = manager.create_session()
    
    assert "id" in session
    assert "created_at" in session
    assert "last_accessed" in session
    assert "world_config" in session
    assert "generated_rooms" in session
    
    # Check world config
    assert "seed" in session["world_config"]
    assert "grid_size" in session["world_config"]
    assert session["world_config"]["grid_size"] == 17


def test_create_session_with_seed(temp_sessions_dir):
    """Test session creation with custom seed"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    seed = 12345
    session = manager.create_session(seed=seed)
    
    assert session["world_config"]["seed"] == seed


def test_create_session_with_grid_size(temp_sessions_dir):
    """Test session creation with custom grid size"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    grid_size = 25
    session = manager.create_session(grid_size=grid_size)
    
    assert session["world_config"]["grid_size"] == grid_size


def test_get_session(temp_sessions_dir):
    """Test retrieving a session"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    created_session = manager.create_session()
    session_id = created_session["id"]
    
    retrieved_session = manager.get_session(session_id)
    assert retrieved_session is not None
    assert retrieved_session["id"] == session_id


def test_get_nonexistent_session(temp_sessions_dir):
    """Test retrieving a non-existent session"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session = manager.get_session("nonexistent-id")
    
    assert session is None


def test_session_persistence(temp_sessions_dir):
    """Test that sessions are saved to disk"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session = manager.create_session(seed=999)
    session_id = session["id"]
    
    # Create a new manager instance (simulates restart)
    manager2 = SessionManager(sessions_dir=temp_sessions_dir)
    retrieved_session = manager2.get_session(session_id)
    
    assert retrieved_session is not None
    assert retrieved_session["id"] == session_id
    assert retrieved_session["world_config"]["seed"] == 999


def test_list_sessions(temp_sessions_dir):
    """Test listing all sessions"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    
    # Create multiple sessions
    session1 = manager.create_session(seed=100)
    session2 = manager.create_session(seed=200)
    session3 = manager.create_session(seed=300)
    
    sessions = manager.list_sessions()
    assert len(sessions) == 3
    
    # Check that all sessions are in the list
    session_ids = [s["id"] for s in sessions]
    assert session1["id"] in session_ids
    assert session2["id"] in session_ids
    assert session3["id"] in session_ids


def test_delete_session(temp_sessions_dir):
    """Test deleting a session"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session = manager.create_session()
    session_id = session["id"]
    
    # Verify session exists
    assert manager.get_session(session_id) is not None
    
    # Delete session
    result = manager.delete_session(session_id)
    assert result is True
    
    # Verify session is gone
    assert manager.get_session(session_id) is None
    
    # Verify file is deleted
    session_file = os.path.join(temp_sessions_dir, f"{session_id}.json")
    assert not os.path.exists(session_file)


def test_delete_nonexistent_session(temp_sessions_dir):
    """Test deleting a non-existent session"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    result = manager.delete_session("nonexistent-id")
    assert result is False


def test_get_world_generator(temp_sessions_dir):
    """Test getting world generator for a session"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session = manager.create_session(seed=777)
    session_id = session["id"]
    
    world_gen = manager.get_world_generator(session_id)
    assert world_gen is not None
    assert world_gen.seed == 777


def test_get_world_generator_nonexistent_session(temp_sessions_dir):
    """Test getting world generator for non-existent session"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    world_gen = manager.get_world_generator("nonexistent-id")
    assert world_gen is None


def test_mark_room_generated(temp_sessions_dir):
    """Test marking a room as generated"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session = manager.create_session()
    session_id = session["id"]
    
    # Mark room as generated
    manager.mark_room_generated(session_id, 5, 10)
    
    # Retrieve session and verify
    session = manager.get_session(session_id)
    assert "5,10" in session["generated_rooms"]
    assert session["generated_rooms"]["5,10"]["x"] == 5
    assert session["generated_rooms"]["5,10"]["y"] == 10


def test_multiple_rooms_generated(temp_sessions_dir):
    """Test marking multiple rooms as generated"""
    manager = SessionManager(sessions_dir=temp_sessions_dir)
    session = manager.create_session()
    session_id = session["id"]
    
    # Mark multiple rooms
    manager.mark_room_generated(session_id, 0, 0)
    manager.mark_room_generated(session_id, 1, 0)
    manager.mark_room_generated(session_id, 0, 1)
    
    session = manager.get_session(session_id)
    assert len(session["generated_rooms"]) == 3
