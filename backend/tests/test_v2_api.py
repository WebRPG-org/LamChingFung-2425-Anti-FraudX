"""
V2 API 集成測試
"""

import sys
import requests
import json
import time

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE = "http://localhost:8000"

def test_health_check():
    """測試健康檢查"""
    print("\n" + "=" * 60)
    print("測試 1: V2 健康檢查")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/game/v2/health")
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["status"] == "ok", "狀態不正常"
        assert "version" in data, "缺少 version 字段"
        assert "features" in data, "缺少 features 字段"
        
        print(f"[OK] 健康檢查通過")
        print(f"   版本: {data['version']}")
        print(f"   功能: {', '.join(data['features'])}")
        
        print("[PASS] 健康檢查測試通過")
        return True
    except Exception as e:
        print(f"[FAIL] 健康檢查失敗: {e}")
        return False

def test_create_session():
    """測試創建會話"""
    print("\n" + "=" * 60)
    print("測試 2: 創建會話")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{API_BASE}/api/game/v2/start",
            json={"persona_type": "A"}
        )
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["success"] is True, "創建失敗"
        assert "session_id" in data, "缺少 session_id"
        assert "persona" in data, "缺少 persona"
        
        session_id = data["session_id"]
        
        print(f"[OK] 會話創建成功")
        print(f"   Session ID: {session_id}")
        print(f"   Persona: {data['persona']['name']}")
        
        print("[PASS] 創建會話測試通過")
        return session_id
    except Exception as e:
        print(f"[FAIL] 創建會話失敗: {e}")
        return None

def test_send_message(session_id):
    """測試發送消息"""
    print("\n" + "=" * 60)
    print("測試 3: 發送消息")
    print("=" * 60)
    
    try:
        print("發送消息給騙徒...")
        response = requests.post(
            f"{API_BASE}/api/game/v2/message",
            json={
                "session_id": session_id,
                "message": "你好，請問有什麼事？",
                "target_ai": "AI-D",
                "persona_type": "A"
            }
        )
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["success"] is True, "發送失敗"
        assert "reply" in data, "缺少 reply"
        
        print(f"[OK] 消息發送成功")
        print(f"   AI 回覆長度: {len(data['reply'])} 字元")
        
        if data['reply']:
            print(f"   前100字: {data['reply'][:100]}...")
        else:
            print("   [WARNING] 回覆為空（可能被過濾）")
        
        # 檢查新增字段
        if "trust_in_scammer" in data:
            print(f"   [OK] 信任度數據可用")
            print(f"      對騙徒: {data['trust_in_scammer']}")
        
        if "trust_in_expert" in data:
            print(f"      對專家: {data['trust_in_expert']}")
        
        if "metrics" in data and data['metrics']:
            print(f"   [OK] 性能指標可用")
            metrics = data['metrics']
            if 'persuasiveness' in metrics:
                print(f"      說服力: {metrics['persuasiveness']}")
        
        print("[PASS] 發送消息測試通過")
        return True
    except Exception as e:
        print(f"[FAIL] 發送消息失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_turn_conversation(session_id):
    """測試多輪對話"""
    print("\n" + "=" * 60)
    print("測試 4: 多輪對話")
    print("=" * 60)
    
    try:
        messages = [
            ("AI-C", "這可能是詐騙，小心"),
            ("AI-D", "我真的是警察，你必須配合"),
        ]
        
        for i, (target_ai, message) in enumerate(messages, 1):
            print(f"\n   第 {i} 輪...")
            response = requests.post(
                f"{API_BASE}/api/game/v2/message",
                json={
                    "session_id": session_id,
                    "message": message,
                    "target_ai": target_ai,
                    "persona_type": "A"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            print(f"   [OK] {target_ai} 回覆: {data['reply'][:80] if data['reply'] else '(空)'}...")
            
            time.sleep(1)  # 避免請求過快
        
        print("\n[PASS] 多輪對話測試通過")
        return True
    except Exception as e:
        print(f"[FAIL] 多輪對話失敗: {e}")
        return False

def test_analyze_session(session_id):
    """測試會話分析"""
    print("\n" + "=" * 60)
    print("測試 5: 會話分析 (RecorderAgent)")
    print("=" * 60)
    
    try:
        print("請求 RecorderAgent 分析...")
        response = requests.post(
            f"{API_BASE}/api/game/v2/analyze",
            json={"session_id": session_id}
        )
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert data["success"] is True, "分析失敗"
        assert "analysis" in data, "缺少 analysis"
        
        analysis = data["analysis"]
        
        print(f"[OK] 分析生成成功")
        print(f"   對話數: {data.get('conversation_count', 0)}")
        
        if "scammer_performance" in analysis:
            sp = analysis["scammer_performance"]
            print(f"   [OK] 騙徒評分: {sp.get('overall_score', 'N/A')}/100")
        elif "raw_analysis" in analysis:
            print(f"   [WARNING] 騙徒評分未解析（JSON 格式問題）")
        
        if "expert_performance" in analysis:
            ep = analysis["expert_performance"]
            print(f"   [OK] 專家評分: {ep.get('overall_score', 'N/A')}/100")
        elif "raw_analysis" in analysis:
            print(f"   [WARNING] 專家評分未解析（JSON 格式問題）")
        
        # 只要有分析結果就算通過
        if "scammer_performance" in analysis or "raw_analysis" in analysis:
            print("[PASS] 會話分析測試通過")
            return True
        else:
            print("[FAIL] 沒有生成任何分析")
            return False
            
    except Exception as e:
        print(f"[FAIL] 會話分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_session(session_id):
    """測試獲取會話"""
    print("\n" + "=" * 60)
    print("測試 6: 獲取會話信息")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/game/v2/session/{session_id}")
        
        assert response.status_code == 200, f"狀態碼錯誤: {response.status_code}"
        
        data = response.json()
        assert "session_id" in data, "缺少 session_id"
        assert "conversations" in data, "缺少 conversations"
        
        print(f"[OK] 獲取會話成功")
        print(f"   對話數: {len(data['conversations'])}")
        print(f"   狀態: {data.get('status', 'N/A')}")
        
        print("[PASS] 獲取會話測試通過")
        return True
    except Exception as e:
        print(f"[FAIL] 獲取會話失敗: {e}")
        return False

def main():
    print("=" * 60)
    print("V2 API 集成測試")
    print("=" * 60)
    
    results = []
    
    # 健康檢查
    health_ok = test_health_check()
    results.append(("健康檢查", health_ok))
    
    if not health_ok:
        print("\n[ERROR] 健康檢查失敗，停止測試")
        print("   請確保 Backend 服務運行中")
        return False
    
    # 創建會話
    session_id = test_create_session()
    results.append(("創建會話", session_id is not None))
    
    if session_id:
        # 發送消息
        results.append(("發送消息", test_send_message(session_id)))
        
        # 多輪對話
        results.append(("多輪對話", test_multi_turn_conversation(session_id)))
        
        # 會話分析
        results.append(("會話分析", test_analyze_session(session_id)))
        
        # 獲取會話
        results.append(("獲取會話", test_get_session(session_id)))
    
    print("\n" + "=" * 60)
    print("測試結果匯總")
    print("=" * 60)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name:20s} {status}")
    
    all_passed = all(r for _, r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有 V2 API 測試通過！")
        print("\n✅ AgentService 和 V2 API 已驗證")
        print("✅ 可以開始實施新功能：")
        print("   1. 數據分類系統")
        print("   2. 可視化訓練界面")
        print("   3. 玩家互動模式")
    else:
        print("[WARNING] 部分測試未通過")
        print("   建議: 查看日誌文件了解詳情")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

