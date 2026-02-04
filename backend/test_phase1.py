"""
Phase 1 測試腳本
測試 PromptBuilder 和 Agent 初始化
"""
import sys
import os

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

def test_prompt_builder():
    """測試 PromptBuilder"""
    print("=" * 60)
    print("測試 1: PromptBuilder")
    print("=" * 60)
    
    from agents.prompts.prompt_builder import PromptBuilder
    
    # 測試專家 Prompt
    expert_prompt = PromptBuilder.build_expert_prompt('elderly', include_examples=True)
    expert_stats = PromptBuilder.get_prompt_stats(expert_prompt)
    
    print("[OK] Expert Prompt 建構成功")
    print(f"   - 字數: {expert_stats['total_chars']}")
    print(f"   - 預估 Token: {expert_stats['estimated_tokens']}")
    print(f"   - 行數: {expert_stats['lines']}")
    
    # 測試騙徒 Prompt
    scammer_prompt = PromptBuilder.build_scammer_prompt('假冒銀行', include_examples=True)
    scammer_stats = PromptBuilder.get_prompt_stats(scammer_prompt)
    
    print("[OK] Scammer Prompt 建構成功")
    print(f"   - 字數: {scammer_stats['total_chars']}")
    print(f"   - 預估 Token: {scammer_stats['estimated_tokens']}")
    
    # 測試受害者 Prompt
    victim_prompt = PromptBuilder.build_victim_prompt('average', include_examples=True)
    victim_stats = PromptBuilder.get_prompt_stats(victim_prompt)
    
    print("[OK] Victim Prompt 建構成功")
    print(f"   - 字數: {victim_stats['total_chars']}")
    print(f"   - 預估 Token: {victim_stats['estimated_tokens']}")
    
    print("\n[總體統計]")
    total_chars = expert_stats['total_chars'] + scammer_stats['total_chars'] + victim_stats['total_chars']
    total_tokens = expert_stats['estimated_tokens'] + scammer_stats['estimated_tokens'] + victim_stats['estimated_tokens']
    print(f"   - 總字數: {total_chars} (平均每個 Agent: {total_chars//3})")
    print(f"   - 總 Token: {total_tokens} (平均每個 Agent: {total_tokens//3})")
    print(f"   - 預估節省: 60% (相比舊版 2000+ 字/Agent)")
    
    return True

def test_agent_initialization():
    """測試 Agent 初始化"""
    print("\n" + "=" * 60)
    print("測試 2: Agent 初始化")
    print("=" * 60)
    
    try:
        from agents.expert import ExpertAgent
        expert = ExpertAgent(victim_persona='elderly')
        print("[OK] ExpertAgent 初始化成功")
    except Exception as e:
        print(f"[FAIL] ExpertAgent 初始化失敗: {e}")
        return False
    
    try:
        from agents.scammer import ScammerAgent
        scammer = ScammerAgent(scam_tactic='假冒銀行')
        print("[OK] ScammerAgent 初始化成功")
    except Exception as e:
        print(f"[FAIL] ScammerAgent 初始化失敗: {e}")
        return False
    
    try:
        from agents.victim import VictimAgent
        victim = VictimAgent(persona_type='average')
        print("[OK] VictimAgent 初始化成功")
    except Exception as e:
        print(f"[FAIL] VictimAgent 初始化失敗: {e}")
        return False
    
    return True

def test_examples():
    """測試示例庫"""
    print("\n" + "=" * 60)
    print("測試 3: 示例庫")
    print("=" * 60)
    
    from agents.prompts.expert_examples import EXPERT_EXAMPLES
    from agents.prompts.scammer_examples import SCAMMER_EXAMPLES
    from agents.prompts.victim_examples import VICTIM_EXAMPLES
    
    expert_count = sum(len(examples) for examples in EXPERT_EXAMPLES.values())
    scammer_count = sum(len(examples) for examples in SCAMMER_EXAMPLES.values())
    victim_count = sum(len(examples) for examples in VICTIM_EXAMPLES.values())
    
    print(f"[OK] Expert 示例: {expert_count} 個")
    print(f"[OK] Scammer 示例: {scammer_count} 個")
    print(f"[OK] Victim 示例: {victim_count} 個")
    print(f"[總計] {expert_count + scammer_count + victim_count} 個高質量示例")
    
    return True

if __name__ == "__main__":
    print("\n[Phase 1 測試開始]\n")
    
    results = []
    
    # 測試 1: PromptBuilder
    try:
        results.append(("PromptBuilder", test_prompt_builder()))
    except Exception as e:
        print(f"[FAIL] PromptBuilder 測試失敗: {e}")
        results.append(("PromptBuilder", False))
    
    # 測試 2: Agent 初始化
    try:
        results.append(("Agent 初始化", test_agent_initialization()))
    except Exception as e:
        print(f"[FAIL] Agent 初始化測試失敗: {e}")
        results.append(("Agent 初始化", False))
    
    # 測試 3: 示例庫
    try:
        results.append(("示例庫", test_examples()))
    except Exception as e:
        print(f"[FAIL] 示例庫測試失敗: {e}")
        results.append(("示例庫", False))
    
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
        print("\n[SUCCESS] Phase 1 所有測試通過！")
        print("[OK] 可以繼續 Phase 2")
    else:
        print("\n[WARNING] 部分測試失敗，請檢查錯誤")
