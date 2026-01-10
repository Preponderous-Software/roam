#!/usr/bin/env python3
"""
Test script for the Roam client (without pygame UI).
Tests the API communication logic.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from client.api_client import RoamAPIClient


def test_client_api():
    """Test the client API communication."""
    print("=" * 60)
    print("Testing Roam Client API Communication")
    print("=" * 60)
    print()
    
    # Initialize client
    print("1. Initializing API client...")
    client = RoamAPIClient("http://localhost:8080")
    print("   ✓ Client initialized")
    print()
    
    # Start session
    print("2. Starting session...")
    try:
        session = client.init_session()
        session_id = session['sessionId']
        print(f"   ✓ Session started: {session_id}")
        print(f"   ✓ Player energy: {session['player']['energy']}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    print()
    
    # Get player state
    print("3. Getting player state...")
    try:
        player = client.get_player()
        print(f"   ✓ Player name: {player['name']}")
        print(f"   ✓ Direction: {player['direction']}")
        print(f"   ✓ Moving: {player['moving']}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    print()
    
    # Move player
    print("4. Moving player...")
    try:
        player = client.perform_player_action("move", direction=0)
        print(f"   ✓ Direction after move: {player['direction']}")
        print(f"   ✓ Moving: {player['moving']}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    print()
    
    # Add items
    print("5. Adding items to inventory...")
    try:
        client.add_item_to_inventory("apple")
        client.add_item_to_inventory("banana")
        inventory = client.get_inventory()
        print(f"   ✓ Items in inventory: {inventory['numItems']}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    print()
    
    # Consume food
    print("6. Consuming food...")
    try:
        # Remove some energy first
        player = client.update_player_energy(20, "remove")
        energy_before = player['energy']
        print(f"   ✓ Energy before consumption: {energy_before}")
        
        # Consume apple
        player = client.perform_player_action("consume", item_name="apple")
        energy_after = player['energy']
        print(f"   ✓ Energy after consumption: {energy_after}")
        print(f"   ✓ Energy restored: {energy_after - energy_before}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    print()
    
    # Delete session
    print("7. Ending session...")
    try:
        client.delete_session()
        print(f"   ✓ Session deleted")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    print()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_client_api()
    sys.exit(0 if success else 1)
