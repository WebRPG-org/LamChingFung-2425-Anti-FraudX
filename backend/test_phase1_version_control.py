"""
Phase 1 測試：Prompt 版本控制系統
測試版本註冊、獲取、回退等功能
"""

import sys
import os
import asyncio

# 添加 backend 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.prompt_version_manager import PromptVersionManager
from services.prompt_helper import register_initial_prompts, get_versioned_prompt
from utils.logger import log


def test_version_registration():
    """測試版本註冊"""
    print("\n" + "="*60)
    print("測試 1: 版本註冊")
    print("="*60)
    
    # 使用臨時存儲路徑
    temp_path = os.path.join(os.path.dirname(__file__), "temp_versions_test.json")
    vm = PromptVersionManager(storage_path=temp_path)
    
    # 註冊初始版本
    register_initial_prompts(vm)
    
    # 檢查版本是否註冊成功
    expert_v1 = vm.get_version("expert", "v1.0")
    scammer_v1 = vm.get_version("scammer", "v1.0")
    victim_v1 = vm.get_version("victim", "v1.0")
    
    assert expert_v1 is not None, "Expert v1.0 未註冊"
    assert scammer_v1 is not None, "Scammer v1.0 未註冊"
    assert victim_v1 is not None, "Victim v1.0 未註冊"
    
    print("✅ 版本註冊測試通過")
    print(f"   - Expert v1.0: {len(expert_v1)} 字")
    print(f"   - Scammer v1.0: {len(scammer_v1)} 字")
    print(f"   - Victim v1.0: {len(victim_v1)} 字")
    
    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return True


def test_version_retrieval():
    """測試版本獲取"""
    print("\n" + "="*60)
    print("測試 2: 版本獲取")
    print("="*60)
    
    temp_path = os.path.join(os.path.dirname(__file__), "temp_versions_test.json")
    vm = PromptVersionManager(storage_path=temp_path)
    
    register_initial_prompts(vm)
    
    # 測試獲取活躍版本
    active_expert = vm.get_active_version("expert")
    assert active_expert == "v1.0", f"活躍版本應為 v1.0，實際為 {active_expert}"
    
    # 測試列出版本
    versions = vm.list_versions("expert")
    assert len(versions) == 1, f"應有 1 個版本，實際有 {len(versions)} 個"
    
    print("✅ 版本獲取測試通過")
    print(f"   - 活躍版本: {active_expert}")
    print(f"   - 版本數量: {len(versions)}")
    
    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return True


def test_version_rollback():
    """測試版本回退"""
    print("\n" + "="*60)
    print("測試 3: 版本回退")
    print("="*60)
    
    temp_path = os.path.join(os.path.dirname(__file__), "temp_versions_test.json")
    vm = PromptVersionManager(storage_path=temp_path)
    
    register_initial_prompts(vm)
    
    # 註冊 v1.1
    vm.register_version(
        version="v1.1",
        prompt="這是 v1.1 的測試 Prompt",
        metadata={"description": "測試版本"},
        agent_type="expert"
    )
    
    # 切換到 v1.1
    vm.set_active_version("expert", "v1.1")
    assert vm.get_active_version("expert") == "v1.1"
    
    # 回退到 v1.0
    vm.set_active_version("expert", "v1.0")
    assert vm.get_active_version("expert") == "v1.0"
    
    print("✅ 版本回退測試通過")
    print(f"   - 成功切換到 v1.1")
    print(f"   - 成功回退到 v1.0")
    
    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return True


def test_performance_recording():
    """測試性能記錄"""
    print("\n" + "="*60)
    print("測試 4: 性能記錄")
    print("="*60)
    
    temp_path = os.path.join(os.path.dirname(__file__), "temp_versions_test.json")
    vm = PromptVersionManager(storage_path=temp_path)
    
    register_initial_prompts(vm)
    
    # 記錄性能
    for i in range(5):
        vm.record_performance(
            agent_type="expert",
            version="v1.0",
            metrics={
                "response_time": 2.0 + i * 0.1,
                "token_usage": 500 + i * 10,
                "success": i % 2 == 0
            }
        )
    
    # 檢查統計
    versions = vm.list_versions("expert")
    expert_v1 = versions[0]
    
    assert expert_v1["total_uses"] == 5, f"使用次數應為 5，實際為 {expert_v1['total_uses']}"
    assert "60.0%" in expert_v1["success_rate"], f"成功率應為 60%，實際為 {expert_v1['success_rate']}"
    
    print("✅ 性能記錄測試通過")
    print(f"   - 總使用次數: {expert_v1['total_uses']}")
    print(f"   - 成功率: {expert_v1['success_rate']}")
    print(f"   - 平均響應時間: {expert_v1['avg_response_time']}")
    
    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return True


def test_versioned_prompt_helper():
    """測試版本化 Prompt 輔助函數"""
    print("\n" + "="*60)
    print("測試 5: 版本化 Prompt 輔助函數")
    print("="*60)
    
    temp_path = os.path.join(os.path.dirname(__file__), "temp_versions_test.json")
    vm = PromptVersionManager(storage_path=temp_path)
    
    register_initial_prompts(vm)
    
    # 測試獲取版本化 Prompt
    context = {
        "persona_type": "elderly",
        "scam_tactic": "假冒銀行",
        "context_info": "測試上下文"
    }
    
    prompt = get_versioned_prompt(vm, "expert", context)
    
    assert len(prompt) > 0, "Prompt 不應為空"
    assert "elderly" in prompt or "測試上下文" in prompt, "Prompt 應包含上下文信息"
    
    print("✅ 版本化 Prompt 輔助函數測試通過")
    print(f"   - Prompt 長度: {len(prompt)} 字")
    
    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return True


def test_ab_test():
    """測試 A/B 測試"""
    print("\n" + "="*60)
    print("測試 6: A/B 測試")
    print("="*60)
    
    temp_path = os.path.join(os.path.dirname(__file__), "temp_versions_test.json")
    vm = PromptVersionManager(storage_path=temp_path)
    
    register_initial_prompts(vm)
    
    # 註冊 v1.1
    vm.register_version(
        version="v1.1",
        prompt="這是 v1.1 的測試 Prompt",
        metadata={"description": "測試版本"},
        agent_type="expert"
    )
    
    # 為兩個版本記錄性能
    for i in range(5):
        vm.record_performance("expert", "v1.0", {
            "response_time": 2.0,
            "token_usage": 500,
            "success": True
        })
        
        vm.record_performance("expert", "v1.1", {
            "response_time": 1.8,
            "token_usage": 450,
            "success": i < 4  # v1.1 成功率更高
        })
    
    # 運行 A/B 測試
    results = vm.ab_test("expert", "v1.0", "v1.1")
    
    assert "analysis" in results, "結果應包含分析"
    assert "winner" in results["analysis"], "分析應包含勝者"
    
    print("✅ A/B 測試通過")
    print(f"   - 勝者: {results['analysis']['winner']}")
    print(f"   - 改進幅度: {results['analysis']['improvement']}")
    
    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return True


def main():
    """運行所有測試"""
    print("\n" + "="*70)
    print("🚀 Phase 1 測試：Prompt 版本控制系統")
    print("="*70)
    
    tests = [
        ("版本註冊", test_version_registration),
        ("版本獲取", test_version_retrieval),
        ("版本回退", test_version_rollback),
        ("性能記錄", test_performance_recording),
        ("版本化 Prompt 輔助函數", test_versioned_prompt_helper),
        ("A/B 測試", test_ab_test)
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
        print("\n🎉 所有測試通過！Phase 1 功能正常！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗")
        return 1


if __name__ == "__main__":
    exit(main())
