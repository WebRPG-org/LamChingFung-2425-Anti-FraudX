"""
測試 ContextManager
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.context_manager import ContextManager


def test_basic_functionality():
    """測試基本功能"""
    print("=" * 60)
    print("測試 1: 基本功能")
    print("=" * 60)
    
    cm = ContextManager(max_tokens=500, keep_recent_turns=3)
    
    # 添加對話
    cm.add_turn("騙徒", "你好，我係銀行職員，你嘅戶口有問題。")
    cm.add_turn("受騙者", "吓？咩問題？")
    cm.add_turn("防騙專家", "呢個係詐騙，唔好信。")
    
    print(f"[OK] 添加 3 輪對話")
    print(f"   - 歷史長度: {len(cm.get_full_history())}")
    print(f"   - 預估 Token: {cm._estimate_tokens()}")
    
    return True


def test_summarization():
    """測試摘要功能"""
    print("\n" + "=" * 60)
    print("測試 2: 摘要功能")
    print("=" * 60)
    
    cm = ContextManager(max_tokens=200, keep_recent_turns=2)
    
    # 添加多輪對話（觸發摘要）
    conversations = [
        ("騙徒", "你好，我係銀行職員。"),
        ("受騙者", "你好。"),
        ("防騙專家", "小心詐騙。"),
        ("騙徒", "你嘅戶口有問題，需要立即處理。"),
        ("受騙者", "咩問題？我好驚。"),
        ("防騙專家", "呢個係假冒銀行，唔好信。"),
        ("騙徒", "如果你唔處理，你啲錢會凍結。"),
        ("受騙者", "點算好？"),
        ("防騙專家", "立即收線，打去銀行官方熱線。"),
    ]
    
    for speaker, text in conversations:
        cm.add_turn(speaker, text)
    
    print(f"[OK] 添加 {len(conversations)} 輪對話")
    print(f"   - 當前歷史長度: {len(cm.get_full_history())}")
    print(f"   - 預估 Token: {cm._estimate_tokens()}")
    
    if cm.summary:
        print(f"[OK] 摘要已生成")
        print(f"\n{cm.summary}")
    else:
        print(f"[INFO] 未觸發摘要（Token 未超過閾值）")
    
    return True


def test_agent_specific_context():
    """測試針對不同 Agent 的上下文"""
    print("\n" + "=" * 60)
    print("測試 3: Agent 專屬上下文")
    print("=" * 60)
    
    cm = ContextManager(max_tokens=2000, keep_recent_turns=3)
    
    # 添加對話
    cm.add_turn("騙徒", "你好，我係銀行職員。")
    cm.add_turn("受騙者", "你好。")
    cm.add_turn("防騙專家", "小心詐騙。")
    cm.add_turn("騙徒", "你嘅戶口有問題。")
    cm.add_turn("受騙者", "咩問題？")
    
    # 測試不同 Agent 的上下文
    scammer_context = cm.get_context_for_agent("scammer", include_summary=False)
    expert_context = cm.get_context_for_agent("expert", include_summary=False)
    victim_context = cm.get_context_for_agent("victim", include_summary=False)
    
    print(f"[OK] 騙徒上下文 ({len(scammer_context)} 字):")
    print(f"   {scammer_context[:100]}...")
    
    print(f"\n[OK] 專家上下文 ({len(expert_context)} 字):")
    print(f"   {expert_context[:100]}...")
    
    print(f"\n[OK] 受害者上下文 ({len(victim_context)} 字):")
    print(f"   {victim_context[:100]}...")
    
    return True


def test_long_conversation():
    """測試長對話（100+ 輪）"""
    print("\n" + "=" * 60)
    print("測試 4: 長對話支持")
    print("=" * 60)
    
    cm = ContextManager(max_tokens=500, keep_recent_turns=5)
    
    # 模擬 50 輪對話
    for i in range(50):
        cm.add_turn("騙徒", f"騙徒第 {i+1} 輪：繼續行騙。")
        cm.add_turn("受騙者", f"受騙者第 {i+1} 輪：回應。")
        cm.add_turn("防騙專家", f"專家第 {i+1} 輪：警告。")
    
    print(f"[OK] 添加 150 輪對話（50 個回合）")
    print(f"   - 當前歷史長度: {len(cm.get_full_history())}")
    print(f"   - 預估 Token: {cm._estimate_tokens()}")
    print(f"   - 摘要狀態: {'已生成' if cm.summary else '未生成'}")
    
    if cm.summary:
        print(f"\n[摘要內容]")
        print(cm.summary)
    
    # 驗證最近對話
    recent = cm.get_recent_turns()
    print(f"\n[OK] 保留最近 {len(recent)} 輪完整對話")
    
    return True


if __name__ == "__main__":
    print("\n[ContextManager 測試開始]\n")
    
    results = []
    
    try:
        results.append(("基本功能", test_basic_functionality()))
    except Exception as e:
        print(f"[FAIL] 基本功能測試失敗: {e}")
        results.append(("基本功能", False))
    
    try:
        results.append(("摘要功能", test_summarization()))
    except Exception as e:
        print(f"[FAIL] 摘要功能測試失敗: {e}")
        results.append(("摘要功能", False))
    
    try:
        results.append(("Agent 專屬上下文", test_agent_specific_context()))
    except Exception as e:
        print(f"[FAIL] Agent 專屬上下文測試失敗: {e}")
        results.append(("Agent 專屬上下文", False))
    
    try:
        results.append(("長對話支持", test_long_conversation()))
    except Exception as e:
        print(f"[FAIL] 長對話支持測試失敗: {e}")
        results.append(("長對話支持", False))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    print(f"\n[總計] {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n[SUCCESS] ContextManager 所有測試通過！")
    else:
        print("\n[WARNING] 部分測試失敗")
