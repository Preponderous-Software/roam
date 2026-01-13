#!/usr/bin/env python3
"""
Demo script showing the Roam API client in action.
This demonstrates the client-server architecture where the Python client
communicates with the Java Spring Boot server via REST API.

@author Daniel McCoy Stephenson
"""

import sys
import os

# Add src directory to path to import the API client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from client.api_client import RoamAPIClient


def main():
    print("=" * 60)
    print("Roam Client-Server Architecture Demo")
    print("=" * 60)
    print()
    
    # Initialize API client
    print("1. Initializing API client...")
    client = RoamAPIClient("http://localhost:8080")
    print("   ✓ Client initialized")
    print()
    
    # Register or login
    print("2. Authenticating with server...")
    import time
    username = f"demo_user_{int(time.time())}"
    password = "demo_password_123"
    email = f"demo_{int(time.time())}@example.com"
    
    try:
        # Try to register a new user
        print(f"   • Registering new user: {username}")
        auth_response = client.register(username, password, email)
        print(f"   ✓ Registration successful!")
        print(f"   ✓ Username: {auth_response['username']}")
        print(f"   ✓ Roles: {', '.join(auth_response['roles'])}")
        print(f"   ✓ Access token expires in: {auth_response['expiresIn']} seconds")
    except Exception as e:
        print(f"   ✗ Registration failed: {e}")
        print(f"   • Trying to login instead...")
        try:
            # If registration fails, try to login
            auth_response = client.login(username, password)
            print(f"   ✓ Login successful!")
            print(f"   ✓ Username: {auth_response['username']}")
        except Exception as login_error:
            print(f"   ✗ Login also failed: {login_error}")
            print("   Please ensure the server is running and accessible")
            return
    print()
    
    # Create a new game session
    print("3. Creating new game session...")
    try:
        session = client.init_session()
        print(f"   ✓ Session created: {session['sessionId']}")
        print(f"   ✓ Current tick: {session['currentTick']}")
        print(f"   ✓ Player ID: {session['player']['id']}")
        print(f"   ✓ Player energy: {session['player']['energy']}")
    except Exception as e:
        print(f"   ✗ Failed to create session: {e}")
        return
    print()
    
    # Get player state
    print("4. Fetching player state...")
    try:
        player = client.get_player()
        print(f"   ✓ Player name: {player['name']}")
        print(f"   ✓ Energy: {player['energy']}/{player['targetEnergy']}")
        print(f"   ✓ Direction: {player['direction']}")
        print(f"   ✓ Moving: {player['moving']}")
    except Exception as e:
        print(f"   ✗ Failed to get player: {e}")
        return
    print()
    
    # Add items to inventory
    print("5. Adding items to inventory...")
    try:
        # Add apple
        inv = client.add_item_to_inventory("apple")
        print(f"   ✓ Added apple - Inventory has {inv['numItems']} items")
        
        # Add banana
        inv = client.add_item_to_inventory("banana")
        print(f"   ✓ Added banana - Inventory has {inv['numItems']} items")
        
        # Add stone
        inv = client.add_item_to_inventory("stone")
        print(f"   ✓ Added stone - Inventory has {inv['numItems']} items")
        
        # Show inventory summary
        print(f"   ✓ Free slots: {inv['numFreeSlots']}/{inv['numFreeSlots'] + inv['numTakenSlots']}")
    except Exception as e:
        print(f"   ✗ Failed to add items: {e}")
        return
    print()
    
    # Perform player actions
    print("6. Performing player actions...")
    try:
        # Move up
        player = client.perform_player_action("move", direction=0)
        print(f"   ✓ Moved up - Direction: {player['direction']}, Moving: {player['moving']}")
        
        # Start gathering
        player = client.perform_player_action("gather", gathering=True)
        print(f"   ✓ Started gathering - Gathering: {player['gathering']}")
        
        # Stop gathering
        player = client.perform_player_action("gather", gathering=False)
        print(f"   ✓ Stopped gathering - Gathering: {player['gathering']}")
        
        # Stop moving
        player = client.perform_player_action("stop")
        print(f"   ✓ Stopped moving - Direction: {player['direction']}, Moving: {player['moving']}")
    except Exception as e:
        print(f"   ✗ Failed to perform actions: {e}")
        return
    print()
    
    # Update energy
    print("7. Managing player energy...")
    try:
        # Remove energy
        player = client.update_player_energy(10, "remove")
        print(f"   ✓ Removed 10 energy - Energy: {player['energy']}")
        
        # Add energy back
        player = client.update_player_energy(5, "add")
        print(f"   ✓ Added 5 energy - Energy: {player['energy']}")
    except Exception as e:
        print(f"   ✗ Failed to update energy: {e}")
        return
    print()
    
    # Get inventory
    print("8. Viewing inventory...")
    try:
        inventory = client.get_inventory()
        print(f"   ✓ Total items: {inventory['numItems']}")
        print(f"   ✓ Taken slots: {inventory['numTakenSlots']}")
        print(f"   ✓ Free slots: {inventory['numFreeSlots']}")
        print("   ✓ Items:")
        for slot in inventory['slots']:
            if not slot['empty']:
                print(f"      - {slot['itemName']} x{slot['numItems']}")
    except Exception as e:
        print(f"   ✗ Failed to get inventory: {e}")
        return
    print()
    
    # Update tick
    print("9. Advancing game tick...")
    try:
        session = client.update_tick()
        print(f"   ✓ Tick advanced to: {session['currentTick']}")
    except Exception as e:
        print(f"   ✗ Failed to update tick: {e}")
        return
    print()
    
    # Get session state
    print("10. Fetching complete session state...")
    try:
        session = client.get_session()
        print(f"   ✓ Session ID: {session['sessionId']}")
        print(f"   ✓ Current tick: {session['currentTick']}")
        print(f"   ✓ Player energy: {session['player']['energy']}")
        print(f"   ✓ Player inventory items: {session['player']['inventory']['numItems']}")
    except Exception as e:
        print(f"   ✗ Failed to get session: {e}")
        return
    print()
    
    # Logout
    print("11. Logging out...")
    try:
        client.logout()
        print("   ✓ Logged out successfully")
        print("   ✓ Tokens revoked")
    except Exception as e:
        print(f"   ✗ Failed to logout: {e}")
    print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    print()
    print("Summary:")
    print("- User authentication with JWT tokens")
    print("- Spring Boot server manages all game state")
    print("- Python client communicates via REST API")
    print("- All business logic is server-side")
    print("- Client only handles presentation and API calls")
    print()


if __name__ == "__main__":
    main()
