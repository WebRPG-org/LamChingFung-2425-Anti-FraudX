"""
Complete test for all three role modes
Tests that player correctly replaces the corresponding AI agent
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def print_subheader(text):
    print(f"\n--- {text} ---\n")

def test_mode(mode_name, mode_key, player_role, expected_ai_roles, player_message):
    """
    Test a specific game mode
    
    Args:
        mode_name: Display name (e.g., "Scammer Mode")
        mode_key: API key (e.g., "scammer")
        player_role: Expected role for player (e.g., "scammer")
        expected_ai_roles: List of AI roles that should respond (e.g., ["victim", "expert"])
        player_message: Message player will send
    """
    print_header(f"Testing {mode_name}")
    
    # Start game
    print_subheader("Step 1: Starting game")
    start_response = requests.post(
        f"{BASE_URL}/api/rpgv2/game/start",
        json={
            "mode": mode_key,
            "scam_type": "fake_bank",
            "victim_persona": "average"
        }
    )
    
    if start_response.status_code != 200:
        print(f"ERROR: Failed to start game - {start_response.status_code}")
        print(start_response.text)
        return False
    
    data = start_response.json()
    session_id = data["session_id"]
    print(f"SUCCESS: Game started")
    print(f"  Session ID: {session_id}")
    print(f"  Mode: {data['mode']}")
    print(f"  Opening messages: {len(data['opening_messages'])}")
    
    # Check opening messages
    if data['opening_messages']:
        print("\n  Opening messages:")
        for msg in data['opening_messages']:
            print(f"    - {msg['role']}: {msg['content'][:60]}...")
    
    # Send player action
    print_subheader("Step 2: Player sends message")
    print(f"Player ({player_role}) says: {player_message}")
    
    action_response = requests.post(
        f"{BASE_URL}/api/rpgv2/game/action",
        json={
            "session_id": session_id,
            "message": player_message
        }
    )
    
    if action_response.status_code != 200:
        print(f"ERROR: Failed to send action - {action_response.status_code}")
        print(action_response.text)
        return False
    
    action_data = action_response.json()
    ai_responses = action_data['ai_responses']
    
    print(f"\nAI Responses ({len(ai_responses)} total):")
    
    # Check AI responses
    response_roles = []
    errors = []
    
    for response in ai_responses:
        role = response['role']
        content = response['content']
        response_roles.append(role)
        
        print(f"\n  {role.upper()}: {content[:80]}...")
        
        if role == player_role:
            errors.append(f"AI {role} should NOT speak (player is {player_role})")
            print(f"    ^^^ ERROR: AI {role} should NOT speak!")
        elif role in expected_ai_roles:
            print(f"    ^^^ GOOD: AI {role} correctly responds")
        else:
            errors.append(f"Unexpected AI role: {role}")
            print(f"    ^^^ WARNING: Unexpected AI role")
    
    # Check for missing AI roles
    for expected_role in expected_ai_roles:
        if expected_role not in response_roles:
            errors.append(f"Missing AI {expected_role} response")
            print(f"\n  ERROR: Missing AI {expected_role} response")
    
    # Check conversation history
    print_subheader("Step 3: Checking conversation history")
    state_response = requests.get(f"{BASE_URL}/api/rpgv2/game/state/{session_id}")
    
    if state_response.status_code != 200:
        print(f"ERROR: Failed to get state - {state_response.status_code}")
        return False
    
    state_data = state_response.json()
    history = state_data.get('conversation_history', [])
    
    print(f"Conversation history ({len(history)} messages):")
    
    player_msg_found = False
    player_msg_role = None
    
    for i, msg in enumerate(history):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        print(f"  {i+1}. {role}: {content[:60]}...")
        
        if content == player_message:
            player_msg_found = True
            player_msg_role = role
    
    if player_msg_found:
        print(f"\nPlayer message recorded as: '{player_msg_role}'")
        if player_msg_role == player_role:
            print(f"  ^^^ GOOD: Correctly recorded as '{player_role}'")
        else:
            errors.append(f"Player message recorded as '{player_msg_role}' instead of '{player_role}'")
            print(f"  ^^^ ERROR: Should be '{player_role}', not '{player_msg_role}'")
    else:
        errors.append("Player message not found in history")
        print("  ^^^ ERROR: Player message not found in history")
    
    # Summary
    print_subheader("Summary")
    
    if errors:
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        print(f"\nRESULT: FAIL")
        return False
    else:
        print("All checks passed!")
        print(f"RESULT: PASS")
        return True

def main():
    print_header("RPGv2 Role Mode Testing Suite")
    print("Testing that player correctly replaces AI in each mode")
    
    results = {}
    
    # Test 1: Scammer Mode
    results['scammer'] = test_mode(
        mode_name="Scammer Mode (Player = Scammer)",
        mode_key="scammer",
        player_role="scammer",
        expected_ai_roles=["victim", "expert"],
        player_message="Hello, I am calling from HSBC Bank. We detected suspicious activity on your account."
    )
    
    # Test 2: Victim Mode
    results['victim'] = test_mode(
        mode_name="Victim Mode (Player = Victim)",
        mode_key="victim",
        player_role="victim",
        expected_ai_roles=["scammer", "expert"],
        player_message="What kind of suspicious activity? I'm worried."
    )
    
    # Test 3: Expert Mode
    results['expert'] = test_mode(
        mode_name="Expert Mode (Player = Expert)",
        mode_key="expert",
        player_role="expert",
        expected_ai_roles=["scammer", "victim"],
        player_message="This is a scam! Do not provide any personal information to this caller."
    )
    
    # Final Summary
    print_header("FINAL RESULTS")
    
    for mode, passed in results.items():
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"  {symbol} {mode.upper()} Mode: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("  ALL TESTS PASSED!")
    else:
        print("  SOME TESTS FAILED - Please review errors above")
    print("="*80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend at http://localhost:8000")
        print("Please make sure the backend is running.")
        exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
