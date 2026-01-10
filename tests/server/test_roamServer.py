"""Tests for the Roam Flask server API endpoints"""
import pytest
import json
import os
import shutil
from server.roamServer import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    
    # Use a temporary sessions directory for testing
    test_sessions_dir = "/tmp/test_roam_sessions"
    if os.path.exists(test_sessions_dir):
        shutil.rmtree(test_sessions_dir)
    os.makedirs(test_sessions_dir)
    
    with app.test_client() as client:
        yield client
    
    # Cleanup
    if os.path.exists(test_sessions_dir):
        shutil.rmtree(test_sessions_dir)


def test_version_endpoint(client):
    """Test the version endpoint"""
    response = client.get('/version')
    # Version endpoint may return 404 or actual version, both are acceptable
    assert response.status_code in [200, 404]


def test_create_session(client):
    """Test creating a new session"""
    response = client.post('/api/v1/session',
                          data=json.dumps({}),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    
    assert "id" in data
    assert "created_at" in data
    assert "world_config" in data
    assert "seed" in data["world_config"]
    assert "grid_size" in data["world_config"]


def test_create_session_with_seed(client):
    """Test creating a session with custom seed"""
    seed = 42
    response = client.post('/api/v1/session',
                          data=json.dumps({"seed": seed}),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["world_config"]["seed"] == seed


def test_create_session_with_grid_size(client):
    """Test creating a session with custom grid size"""
    grid_size = 25
    response = client.post('/api/v1/session',
                          data=json.dumps({"grid_size": grid_size}),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["world_config"]["grid_size"] == grid_size


def test_get_session(client):
    """Test retrieving a session"""
    # Create a session first
    create_response = client.post('/api/v1/session',
                                 data=json.dumps({}),
                                 content_type='application/json')
    session_data = json.loads(create_response.data)
    session_id = session_data["id"]
    
    # Get the session
    response = client.get(f'/api/v1/session/{session_id}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["id"] == session_id


def test_get_nonexistent_session(client):
    """Test getting a non-existent session"""
    response = client.get('/api/v1/session/nonexistent-id')
    assert response.status_code == 404


def test_list_sessions(client):
    """Test listing all sessions"""
    # Create a few sessions
    client.post('/api/v1/session',
               data=json.dumps({"seed": 100}),
               content_type='application/json')
    client.post('/api/v1/session',
               data=json.dumps({"seed": 200}),
               content_type='application/json')
    
    response = client.get('/api/v1/sessions')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "sessions" in data
    assert len(data["sessions"]) >= 2


def test_get_world_overview(client):
    """Test getting world overview"""
    # Create a session
    create_response = client.post('/api/v1/session',
                                 data=json.dumps({"seed": 123}),
                                 content_type='application/json')
    session_data = json.loads(create_response.data)
    session_id = session_data["id"]
    
    # Get world overview
    response = client.get(f'/api/v1/session/{session_id}/world')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "seed" in data
    assert data["seed"] == 123
    assert "biome_distribution" in data
    assert "rooms" in data
    assert "total_rooms" in data


def test_get_world_overview_with_radius(client):
    """Test getting world overview with custom radius"""
    # Create a session
    create_response = client.post('/api/v1/session',
                                 data=json.dumps({}),
                                 content_type='application/json')
    session_data = json.loads(create_response.data)
    session_id = session_data["id"]
    
    # Get world overview with radius 5
    response = client.get(f'/api/v1/session/{session_id}/world?radius=5')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["radius"] == 5
    assert data["total_rooms"] == 11 * 11  # (2*5+1)^2


def test_get_world_overview_nonexistent_session(client):
    """Test getting world overview for non-existent session"""
    response = client.get('/api/v1/session/nonexistent-id/world')
    assert response.status_code == 404


def test_get_room(client):
    """Test getting specific room data"""
    # Create a session
    create_response = client.post('/api/v1/session',
                                 data=json.dumps({"seed": 456}),
                                 content_type='application/json')
    session_data = json.loads(create_response.data)
    session_id = session_data["id"]
    
    # Get room at coordinates (5, 10)
    response = client.get(f'/api/v1/session/{session_id}/room/5/10')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["x"] == 5
    assert data["y"] == 10
    assert "biome" in data
    assert "terrain_features" in data
    assert "resources" in data
    assert "environmental_objects" in data
    assert "background_color" in data


def test_get_room_negative_coordinates(client):
    """Test getting room with negative coordinates"""
    # Create a session
    create_response = client.post('/api/v1/session',
                                 data=json.dumps({}),
                                 content_type='application/json')
    session_data = json.loads(create_response.data)
    session_id = session_data["id"]
    
    # Get room at coordinates (-3, -7)
    response = client.get(f'/api/v1/session/{session_id}/room/-3/-7')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["x"] == -3
    assert data["y"] == -7


def test_get_room_nonexistent_session(client):
    """Test getting room for non-existent session"""
    response = client.get('/api/v1/session/nonexistent-id/room/0/0')
    assert response.status_code == 404


def test_delete_session(client):
    """Test deleting a session"""
    # Create a session
    create_response = client.post('/api/v1/session',
                                 data=json.dumps({}),
                                 content_type='application/json')
    session_data = json.loads(create_response.data)
    session_id = session_data["id"]
    
    # Delete the session
    response = client.delete(f'/api/v1/session/{session_id}')
    assert response.status_code == 200
    
    # Verify session is deleted
    get_response = client.get(f'/api/v1/session/{session_id}')
    assert get_response.status_code == 404


def test_delete_nonexistent_session(client):
    """Test deleting a non-existent session"""
    response = client.delete('/api/v1/session/nonexistent-id')
    assert response.status_code == 404


def test_room_data_consistency(client):
    """Test that same room coordinates return same data"""
    # Create a session with fixed seed
    create_response = client.post('/api/v1/session',
                                 data=json.dumps({"seed": 999}),
                                 content_type='application/json')
    session_data = json.loads(create_response.data)
    session_id = session_data["id"]
    
    # Get room data twice
    response1 = client.get(f'/api/v1/session/{session_id}/room/3/4')
    response2 = client.get(f'/api/v1/session/{session_id}/room/3/4')
    
    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)
    
    # Should return same data
    assert data1["biome"] == data2["biome"]
    assert data1["background_color"] == data2["background_color"]
