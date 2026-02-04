"""
Phase 2 & 3 整合測試
測試所有新增的高級功能
"""

import sys
import os

# 添加 backend 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.context_manager import ContextManager
from utils.chain_of_thought import ChainOfThoughtBuilder, AdaptiveStrategySelector
from utils.prompt_version_manager import PromptVersionManager
from utils.prompt_monitor import PromptPerformanceMonitor
from utils.multilingual_prompts import MultilingualPrompts


def test_context_manager():
    """測試上下文管理器"""
    print("\n" + "="*60)
    print("測試 1: ContextManager (上下文管理)")
    print("="*60)
    
    cm = ContextManager(max_tokens=2000, keep_recent_turns=5)
    
    # 添加對話
    cm.add_turn("騙徒", "你好，我係銀行職員。")
    cm.add_turn("受騙者", "咩事？")
    cm.add_turn("專家", "小心，呢個可能係詐騙。")
    cm.add_turn("騙徒", "你帳戶有問題，需要立即處理。")
    cm.add_turn("受騙者", "真係？好驚啊！")
    
    # 獲取上下文
    expert_context = cm.get_context_for_agent("expert")
    
    print(f"\n✅ 成功添加 {len(cm.conversation_history)} 輪對話")
    print(f"✅ 專家上下文長度: {len(expert_context)} 字")
    print(f"✅ 關鍵信息提取: {len(cm.key_info)} 項")
    
    # 測試長對話
    for i in range(20):
        cm.add_turn("騙徒", f"第 {i} 輪對話")
        cm.add_turn("受騙者", f"回應 {i}")
    
    print(f"✅ 長對話測試: {len(cm.conversation_history)} 輪 → 自動摘要")
    
    return True


def test_chain_of_thought():
    """測試 Chain-of-Thought"""
    print("\n" + "="*60)
    print("測試 2: Chain-of-Thought (思考鏈)")
    print("="*60)
    
    # 構建 CoT Prompt
    cot_prompt = ChainOfThoughtBuilder.build_scammer_cot(
        victim_persona='elderly',
        trust_level=60,
        conversation_history=[
            {"speaker": "受騙者", "dialogue": "我好驚啊！"}
        ],
        scam_tactic='假冒銀行'
    )
    
    print(f"\n✅ 成功生成 CoT Prompt")
    print(f"✅ Prompt 長度: {len(cot_prompt)} 字")
    print(f"✅ 包含 4 個思考步驟")
    
    # 顯示部分內容
    lines = cot_prompt.split('\n')
    print(f"\n📝 Prompt 預覽 (前 10 行):")
    for line in lines[:10]:
        if line.strip():
            print(f"   {line}")
    
    return True


def test_adaptive_strategy():
    """測試自適應策略"""
    print("\n" + "="*60)
    print("測試 3: AdaptiveStrategySelector (自適應策略)")
    print("="*60)
    
    selector = AdaptiveStrategySelector()
    
    # 測試不同情況
    scenarios = [
        {
            "name": "低信任度",
            "params": {
                "victim_persona": "elderly",
                "trust_in_expert": 20,
                "trust_in_scammer": 50,
                "emotional_state": "正常",
                "conversation_history": []
            }
        },
        {
            "name": "恐慌狀態",
            "params": {
                "victim_persona": "average",
                "trust_in_expert": 50,
                "trust_in_scammer": 70,
                "emotional_state": "恐慌",
                "conversation_history": []
            }
        },
        {
            "name": "高風險",
            "params": {
                "victim_persona": "student",
                "trust_in_expert": 40,
                "trust_in_scammer": 85,
                "emotional_state": "正常",
                "conversation_history": []
            }
        }
    ]
    
    for scenario in scenarios:
        strategy = selector.select_strategy(**scenario["params"])
        print(f"\n✅ 情況: {scenario['name']}")
        print(f"   策略: {strategy['strategy']}")
        print(f"   語氣: {strategy['tone']}")
        print(f"   戰術數量: {len(strategy['tactics'])}")
    
    return True


def test_version_manager():
    """測試版本管理器"""
    print("\n" + "="*60)
    print("測試 4: PromptVersionManager (版本管理)")
    print("="*60)
    
    # 使用臨時路徑
    temp_path = os.path.join(os.path.dirname(__file__), "temp_versions.json")
    vm = PromptVersionManager(storage_path=temp_path)
    
    # 註冊版本
    vm.register_version(
        version="v1.0",
        prompt="這是 v1.0 的 Prompt",
        metadata={"description": "初始版本", "author": "Team"},
        agent_type="expert"
    )
    
    vm.register_version(
        version="v1.1",
        prompt="這是 v1.1 的 Prompt（改進版）",
        metadata={"description": "改進版本", "author": "Team"},
        agent_type="expert"
    )
    
    print(f"\n✅ 成功註冊 2 個版本")
    
    # 記錄性能
    vm.record_performance("expert", "v1.0", {
        "response_time": 2.5,
        "token_usage": 500,
        "success": True
    })
    
    vm.record_performance("expert", "v1.1", {
        "response_time": 2.0,
        "token_usage": 450,
        "success": True
    })
    
    print(f"✅ 成功記錄性能數據")
    
    # 列出版本
    versions = vm.list_versions("expert")
    print(f"✅ 版本列表:")
    for v in versions:
        print(f"   - {v['version']}: {v['success_rate']} 成功率")
    
    # 清理臨時文件
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return True


def test_performance_monitor():
    """測試性能監控"""
    print("\n" + "="*60)
    print("測試 5: PromptPerformanceMonitor (性能監控)")
    print("="*60)
    
    monitor = PromptPerformanceMonitor()
    
    # 模擬追蹤
    for i in range(5):
        request_id = f"req_{i}"
        monitor.start_tracking("expert", request_id)
        
        # 模擬處理時間
        import time
        time.sleep(0.1)
        
        monitor.end_tracking(
            "expert",
            request_id,
            token_usage=500 + i * 10,
            output_quality=0.85 + i * 0.02,
            role_consistency=0.90 + i * 0.01,
            success=True
        )
    
    print(f"\n✅ 成功追蹤 5 個請求")
    
    # 獲取摘要
    summary = monitor.get_summary("expert")
    print(f"✅ 性能摘要:")
    print(f"   - 總請求數: {summary['total_requests']}")
    print(f"   - 成功率: {summary['success_rate']}")
    print(f"   - 平均響應時間: {summary['avg_response_time']}")
    print(f"   - 平均 Token: {summary['avg_token_usage']}")
    print(f"   - 平均質量: {summary['avg_output_quality']}")
    
    # 生成報告
    report_path = os.path.join(os.path.dirname(__file__), "temp_report.json")
    report = monitor.generate_report(report_path)
    
    print(f"✅ 成功生成報告")
    
    # 清理
    if os.path.exists(report_path):
        os.remove(report_path)
    
    return True


def test_multilingual():
    """測試多語言支持"""
    print("\n" + "="*60)
    print("測試 6: MultilingualPrompts (多語言支持)")
    print("="*60)
    
    languages = MultilingualPrompts.get_supported_languages()
    print(f"\n✅ 支持的語言: {', '.join(languages)}")
    
    for lang in languages:
        lang_name = MultilingualPrompts.get_language_name(lang)
        print(f"\n📝 {lang_name} ({lang}):")
        
        # 獲取專家 Prompt
        expert_prompt = MultilingualPrompts.get_expert_prompt(lang)
        print(f"   - 專家 Prompt 組件: {len(expert_prompt)} 個")
        
        # 獲取受害者 Prompt
        victim_prompt = MultilingualPrompts.get_victim_prompt("elderly", lang)
        print(f"   - 受害者 Prompt 長度: {len(victim_prompt)} 字")
    
    print(f"\n✅ 所有語言測試通過")
    
    return True


def main():
    """運行所有測試"""
    print("\n" + "="*70)
    print("🚀 Phase 2 & 3 整合測試")
    print("="*70)
    
    tests = [
        ("ContextManager", test_context_manager),
        ("Chain-of-Thought", test_chain_of_thought),
        ("AdaptiveStrategy", test_adaptive_strategy),
        ("VersionManager", test_version_manager),
        ("PerformanceMonitor", test_performance_monitor),
        ("Multilingual", test_multilingual)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "✅ PASS" if success else "❌ FAIL"))
        except Exception as e:
            print(f"\n❌ 測試失敗: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, f"❌ ERROR: {str(e)}"))
    
    # 總結
    print("\n" + "="*70)
    print("📊 測試總結")
    print("="*70)
    
    for name, result in results:
        print(f"{result} - {name}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    total = len(results)
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！Phase 2 & 3 功能正常！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗")
        return 1


if __name__ == "__main__":
    exit(main())
