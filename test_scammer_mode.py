"""
Test script for scammer mode - verify player replaces AI scammer
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_separator():
    print("\n" + "="*80 + "\n")

def test_scammer_mode():
    """Test that player acts as scammer, not AI"""
    
    print("Testing Scammer Mode - Player should replace AI scammer")
    print_separator()
    
    # Step 1: Start game in scammer mode
    print("Step 1: Starting game in scammer mode...")
    start_response = requests.post(
        f"{BASE_URL}/api/rpgv2/game/start",
        json={
            "mode": "scammer",
            "scam_type": "fake_bank",
            "victim_persona": "average"
        }
    )
    
    if start_response.status_code != 200:
        print(f"ERROR: Failed to start game - {start_response.status_code}")
        print(start_response.text)
        return
    
    data = start_response.json()
    session_id = data["session_id"]
    print(f"SUCCESS: Game started - Session ID: {session_id}")
    print(f"Mode: {data['mode']}")
    print(f"Opening messages count: {len(data['opening_messages'])}")
    
    # Check opening messages
    print("\nOpening messages:")
    for msg in data['opening_messages']:
        print(f"  - {msg['role']}: {msg['content'][:50]}...")
    
    if len(data['opening_messages']) > 0:
        print("\nWARNING: Scammer mode should have NO opening messages!")
        print("Player should start the conversation as scammer.")
    else:
        print("\nGOOD: No opening messages - player will start as scammer")
    
    print_separator()
    
    # Step 2: Player sends message as scammer
    print("Step 2: Player (as scammer) sends first message...")
    player_message = "Hello, I am calling from HSBC Bank. We detected suspicious activity on your account."
    
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
        return
    
    action_data = action_response.json()
    print(f"SUCCESS: Action processed")
    print(f"\nPlayer (scammer) said: {player_message}")
    
    # Check AI responses
    print("\nAI Responses:")
    ai_responses = action_data['ai_responses']
    
    has_ai_scammer = False
    has_victim = False
    has_expert = False
    
    for response in ai_responses:
        role = response['role']
        content = response['content']
        print(f"\n  {role.upper()}: {content[:100]}...")
        
        if role == "scammer":
            has_ai_scammer = True
            print("    ^^^ ERROR: AI scammer should NOT speak when player is scammer!")
        elif role == "victim":
            has_victim = True
            print("    ^^^ GOOD: AI victim responds to player (scammer)")
        elif role == "expert":
            has_expert = True
            print("    ^^^ GOOD: AI expert provides advice to victim")
    
    print_separator()
    
    # Step 3: Verify conversation history
    print("Step 3: Checking conversation history...")
    state_response = requests.get(f"{BASE_URL}/api/rpgv2/game/state/{session_id}")
    
    if state_response.status_code != 200:
        print(f"ERROR: Failed to get state - {state_response.status_code}")
        return
    
    state_data = state_response.json()
    history = state_data.get('conversation_history', [])
    
    print(f"\nConversation history ({len(history)} messages):")
    for i, msg in enumerate(history):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        print(f"  {i+1}. {role}: {content[:60]}...")
    
    # Check for player message role
    player_msg_in_history = None
    for msg in history:
        if msg.get('content') == player_message:
            player_msg_in_history = msg
            break
    
    if player_msg_in_history:
        recorded_role = player_msg_in_history.get('role')
        print(f"\nPlayer message recorded as role: '{recorded_role}'")
        if recorded_role == "scammer":
            print("GOOD: Player message correctly recorded as 'scammer'")
        else:
            print(f"ERROR: Player message should be 'scammer', not '{recorded_role}'")
    
    print_separator()
    
    # Summary
    print("SUMMARY:")
    print(f"  - AI Scammer spoke: {'YES (ERROR!)' if has_ai_scammer else 'NO (GOOD)'}")
    print(f"  - AI Victim spoke: {'YES (GOOD)' if has_victim else 'NO (ERROR!)'}")
    print(f"  - AI Expert spoke: {'YES (GOOD)' if has_expert else 'NO (ERROR!)'}")
    
    if not has_ai_scammer and has_victim and has_expert:
        print("\nRESULT: PASS - Scammer mode working correctly!")
    else:
        print("\nRESULT: FAIL - Issues detected in scammer mode")
    
    print_separator()

if __name__ == "__main__":
    try:
        test_scammer_mode()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend at http://localhost:8000")
        print("Please make sure the backend is running.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
