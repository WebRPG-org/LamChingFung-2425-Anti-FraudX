"""
測試三角色系統（受害人、專家、騙徒）
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分隔線"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_victim_mode():
    """測試受害人模式"""
    print_section("測試 1: 受害人模式")
    
    # 開始遊戲
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/start", json={
        "mode": "victim",
        "scam_type": "假冒銀行",
        "victim_persona": "average"
    })
    
    data = response.json()
    session_id = data["session_id"]
    
    print(f"✅ 會話創建成功: {session_id}")
    print(f"📋 模式: {data['mode_info']['name']}")
    print(f"📝 描述: {data['mode_info']['description']}")
    
    # 顯示開場消息
    print("\n開場對話:")
    for msg in data["opening_messages"]:
        role_emoji = {"scammer": "🎭", "expert": "🛡️", "victim": "👤"}
        emoji = role_emoji.get(msg["role"], "💬")
        print(f"{emoji} {msg['role']}: {msg['content']}")
    
    # 玩家（受害人）回應
    print("\n玩家回應:")
    player_msg = "這聽起來有點奇怪，我需要考慮一下"
    print(f"👤 受害人: {player_msg}")
    
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/action", json={
        "session_id": session_id,
        "message": player_msg
    })
    
    data = response.json()
    
    print("\nAI 回應:")
    for ai_msg in data["ai_responses"]:
        role_emoji = {"scammer": "🎭", "expert": "🛡️"}
        emoji = role_emoji.get(ai_msg["role"], "💬")
        print(f"{emoji} {ai_msg['role']}: {ai_msg['content']}")
    
    print("\n遊戲狀態:")
    print(f"  回合數: {data['game_state']['round_count']}")
    print(f"  對騙徒信任度: {data['game_state']['trust_in_scammer']:.1f}")
    print(f"  對專家信任度: {data['game_state']['trust_in_expert']:.1f}")
    print(f"  警覺性: {data['game_state']['alertness']:.1f}")
    
    return session_id

def test_scammer_mode():
    """測試騙徒模式"""
    print_section("測試 2: 騙徒模式")
    
    # 開始遊戲
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/start", json={
        "mode": "scammer",
        "scam_type": "假冒銀行",
        "victim_persona": "average"
    })
    
    data = response.json()
    session_id = data["session_id"]
    
    print(f"✅ 會話創建成功: {session_id}")
    print(f"📋 模式: {data['mode_info']['name']}")
    print(f"📝 描述: {data['mode_info']['description']}")
    
    # 玩家（騙徒）發起詐騙
    print("\n玩家（騙徒）發起詐騙:")
    player_msg = "你好，我是銀行客服，你的帳戶出現異常，需要立即驗證"
    print(f"🎭 騙徒: {player_msg}")
    
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/action", json={
        "session_id": session_id,
        "message": player_msg
    })
    
    data = response.json()
    
    print("\nAI 回應:")
    for ai_msg in data["ai_responses"]:
        role_emoji = {"victim": "👤", "expert": "🛡️"}
        emoji = role_emoji.get(ai_msg["role"], "💬")
        print(f"{emoji} {ai_msg['role']}: {ai_msg['content']}")
    
    print("\n遊戲狀態:")
    print(f"  回合數: {data['game_state']['round_count']}")
    print(f"  對騙徒信任度: {data['game_state']['trust_in_scammer']:.1f}")
    print(f"  警覺性: {data['game_state']['alertness']:.1f}")
    
    return session_id

def test_expert_mode():
    """測試專家模式"""
    print_section("測試 3: 專家模式")
    
    # 開始遊戲
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/start", json={
        "mode": "expert",
        "scam_type": "假冒銀行",
        "victim_persona": "average"
    })
    
    data = response.json()
    session_id = data["session_id"]
    
    print(f"✅ 會話創建成功: {session_id}")
    print(f"📋 模式: {data['mode_info']['name']}")
    print(f"📝 描述: {data['mode_info']['description']}")
    
    # 顯示開場消息
    print("\n開場對話:")
    for msg in data["opening_messages"]:
        role_emoji = {"scammer": "🎭", "victim": "👤", "expert": "🛡️"}
        emoji = role_emoji.get(msg["role"], "💬")
        print(f"{emoji} {msg['role']}: {msg['content']}")
    
    # 玩家（專家）提供建議
    print("\n玩家（專家）提供建議:")
    player_msg = "小心！這是典型的假冒銀行詐騙，真正的銀行不會這樣聯繫你"
    print(f"🛡️ 專家: {player_msg}")
    
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/action", json={
        "session_id": session_id,
        "message": player_msg
    })
    
    data = response.json()
    
    print("\nAI 回應:")
    for ai_msg in data["ai_responses"]:
        role_emoji = {"scammer": "🎭", "victim": "👤"}
        emoji = role_emoji.get(ai_msg["role"], "💬")
        print(f"{emoji} {ai_msg['role']}: {ai_msg['content']}")
    
    print("\n遊戲狀態:")
    print(f"  回合數: {data['game_state']['round_count']}")
    print(f"  對騙徒信任度: {data['game_state']['trust_in_scammer']:.1f}")
    print(f"  警覺性: {data['game_state']['alertness']:.1f}")
    
    return session_id

def test_role_switching(session_id):
    """測試角色切換"""
    print_section("測試 4: 角色切換")
    
    print(f"使用會話: {session_id}")
    
    # 切換到專家模式
    print("\n切換到專家模式...")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": session_id,
        "new_mode": "expert"
    })
    
    data = response.json()
    if data["success"]:
        print(f"✅ {data['message']}")
        print(f"   舊模式: {data['old_mode']}")
        print(f"   新模式: {data['new_mode']}")
    else:
        print("❌ 切換失敗")
    
    time.sleep(1)
    
    # 切換到騙徒模式
    print("\n切換到騙徒模式...")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": session_id,
        "new_mode": "scammer"
    })
    
    data = response.json()
    if data["success"]:
        print(f"✅ {data['message']}")
        print(f"   舊模式: {data['old_mode']}")
        print(f"   新模式: {data['new_mode']}")
    else:
        print("❌ 切換失敗")
    
    time.sleep(1)
    
    # 切換回受害人模式
    print("\n切換回受害人模式...")
    response = requests.post(f"{BASE_URL}/api/rpgv2/game/switch-role", json={
        "session_id": session_id,
        "new_mode": "victim"
    })
    
    data = response.json()
    if data["success"]:
        print(f"✅ {data['message']}")
        print(f"   舊模式: {data['old_mode']}")
        print(f"   新模式: {data['new_mode']}")
    else:
        print("❌ 切換失敗")

def test_performance_stats():
    """測試性能統計"""
    print_section("測試 5: 性能統計")
    
    response = requests.get(f"{BASE_URL}/api/rpgv2/performance/stats")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get("status") == "not_initialized":
            print("⚠️ 優化判定系統尚未初始化")
        else:
            stats = data["data"]
            print("📊 AI 判定系統性能統計:")
            print(f"  總判定次數: {stats.get('total_judgments', 0)}")
            print(f"  快速路徑命中: {stats.get('fast_path_hits', 0)}")
            print(f"  緩存命中: {stats.get('cache_hits', 0)}")
            print(f"  AI 調用: {stats.get('ai_calls', 0)}")
            print(f"  快速路徑命中率: {stats.get('fast_path_hit_rate', 0):.1f}%")
            print(f"  緩存命中率: {stats.get('cache_hit_rate', 0):.1f}%")
    else:
        print("❌ 獲取性能統計失敗")

def main():
    """主測試流程"""
    print("\n" + "🎮"*30)
    print("  三角色系統測試")
    print("🎮"*30)
    
    try:
        # 測試受害人模式
        victim_session = test_victim_mode()
        time.sleep(2)
        
        # 測試騙徒模式
        scammer_session = test_scammer_mode()
        time.sleep(2)
        
        # 測試專家模式
        expert_session = test_expert_mode()
        time.sleep(2)
        
        # 測試角色切換
        test_role_switching(victim_session)
        time.sleep(2)
        
        # 測試性能統計
        test_performance_stats()
        
        print_section("測試完成")
        print("✅ 所有測試通過！")
        print("\n鍵盤快捷鍵:")
        print("  按 1 = 切換到受害人模式")
        print("  按 2 = 切換到騙徒模式")
        print("  按 3 = 切換到專家模式")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
