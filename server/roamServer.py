import os
from flask import Flask, jsonify, request
from server.services.sessionManager import SessionManager

app = Flask(__name__)

# Initialize session manager
session_manager = SessionManager()


# Expected input: none
# Expected output: version string or error json
@app.route('/version', methods=['GET'])
def version():
    if os.path.isfile("server/version.txt"):
        with open("server/version.txt", "r") as file:
            version = file.read()
            
            if version:
                return version
            else:
                return jsonify({"error": "Version file is empty"}), 500
    else:
        return jsonify({"error": "Version file not found"}), 404


# Create a new game session
# Expected input: JSON body with optional 'seed' and 'grid_size' fields
# Expected output: Session data including session ID and world config
@app.route('/api/v1/session', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    seed = data.get('seed')
    grid_size = data.get('grid_size', 17)
    
    try:
        session = session_manager.create_session(seed=seed, grid_size=grid_size)
        return jsonify(session), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get session information
# Expected input: session ID in URL path
# Expected output: Session data
@app.route('/api/v1/session/<session_id>', methods=['GET'])
def get_session(session_id):
    session = session_manager.get_session(session_id)
    if session:
        return jsonify(session), 200
    else:
        return jsonify({"error": "Session not found"}), 404


# List all sessions
# Expected input: none
# Expected output: List of session summaries
@app.route('/api/v1/sessions', methods=['GET'])
def list_sessions():
    sessions = session_manager.list_sessions()
    return jsonify({"sessions": sessions}), 200


# Get world overview for a session
# Expected input: session ID in URL path, optional 'radius' query parameter
# Expected output: World overview with biome distribution
@app.route('/api/v1/session/<session_id>/world', methods=['GET'])
def get_world_overview(session_id):
    radius = request.args.get('radius', default=10, type=int)
    
    world_generator = session_manager.get_world_generator(session_id)
    if not world_generator:
        return jsonify({"error": "Session not found"}), 404
    
    try:
        world_overview = world_generator.generate_world_overview(radius=radius)
        return jsonify(world_overview), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get specific room data
# Expected input: session ID, x, and y coordinates in URL path
# Expected output: Room data including biome, terrain, resources, and objects
@app.route('/api/v1/session/<session_id>/room/<int:x>/<int:y>', methods=['GET'])
def get_room(session_id, x, y):
    world_generator = session_manager.get_world_generator(session_id)
    if not world_generator:
        return jsonify({"error": "Session not found"}), 404
    
    try:
        room_data = world_generator.generate_room_data(x, y)
        # Mark room as generated in session
        session_manager.mark_room_generated(session_id, x, y)
        return jsonify(room_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete a session
# Expected input: session ID in URL path
# Expected output: Success message
@app.route('/api/v1/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session_manager.delete_session(session_id):
        return jsonify({"message": "Session deleted"}), 200
    else:
        return jsonify({"error": "Session not found"}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)