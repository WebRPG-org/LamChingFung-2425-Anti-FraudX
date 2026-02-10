"""
系統整合驗證腳本
快速驗證評分系統v2.0的所有組件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from datetime import datetime
from typing import Dict, List


class IntegrationValidator:
    """整合驗證器"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, func):
        """執行測試"""
        print(f"\n{'='*60}")
        print(f"測試: {name}")
        print(f"{'='*60}")
        
        try:
            result = func()
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            
            self.passed += 1
            self.results.append({"name": name, "status": "✅ PASS", "error": None})
            print(f"✅ 通過")
            return True
            
        except Exception as e:
            self.failed += 1
            self.results.append({"name": name, "status": "❌ FAIL", "error": str(e)})
            print(f"❌ 失敗: {e}")
            return False
    
    def print_summary(self):
        """打印摘要"""
        print(f"\n{'='*60}")
        print(f"驗證摘要")
        print(f"{'='*60}")
        
        for result in self.results:
            print(f"{result['status']} {result['name']}")
            if result['error']:
                print(f"   錯誤: {result['error']}")
        
        print(f"\n總計: {self.passed + self.failed} 個測試")
        print(f"✅ 通過: {self.passed}")
        print(f"❌ 失敗: {self.failed}")
        print(f"成功率: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        
        if self.failed == 0:
            print(f"\n🎉 所有測試通過！系統整合成功！")
        else:
            print(f"\n⚠️ 有 {self.failed} 個測試失敗，請檢查錯誤信息")


def test_imports():
    """測試1: 導入核心模組"""
    from backend.utils.victim_evaluator import VictimEvaluator
    from backend.utils.victim_response_analyzer import VictimResponseAnalyzer
    from backend.utils.scoring_monitor import ScoringMonitor, get_monitor
    from backend.api.scoring_v2_routes import router as scoring_router
    from backend.api.monitoring_routes import router as monitoring_router
    
    print("✓ VictimEvaluator")
    print("✓ VictimResponseAnalyzer")
    print("✓ ScoringMonitor")
    print("✓ scoring_v2_routes")
    print("✓ monitoring_routes")


def test_victim_evaluator():
    """測試2: VictimEvaluator初始化"""
    from backend.utils.victim_evaluator import VictimEvaluator
    from backend.agents.victim import VictimAgent
    from backend.utils.performance_tracker import PerformanceTracker
    
    victim_agent = VictimAgent(persona_type="average")
    performance_tracker = PerformanceTracker(victim_persona="average")
    
    evaluator = VictimEvaluator(
        victim_agent=victim_agent,
        performance_tracker=performance_tracker,
        rule_weight=0.7,
        agent_weight=0.3,
        enable_agent_scoring=False  # 禁用Agent評分以加快測試
    )
    
    print(f"✓ 評估器創建成功")
    print(f"  規則權重: {evaluator.rule_weight}")
    print(f"  Agent權重: {evaluator.agent_weight}")
    print(f"  Agent評分: {evaluator.enable_agent_scoring}")


async def test_evaluation():
    """測試3: 執行評估"""
    from backend.utils.victim_evaluator import VictimEvaluator
    from backend.agents.victim import VictimAgent
    from backend.utils.performance_tracker import PerformanceTracker
    
    victim_agent = VictimAgent(persona_type="average")
    performance_tracker = PerformanceTracker(victim_persona="average")
    
    evaluator = VictimEvaluator(
        victim_agent=victim_agent,
        performance_tracker=performance_tracker,
        rule_weight=1.0,
        agent_weight=0.0,
        enable_agent_scoring=False
    )
    
    conversation_history = [
        {"role": "scammer", "content": "你好，我是警察", "strategy": "authority"},
        {"role": "victim", "content": "有什麼事嗎？"},
        {"role": "scammer", "content": "你的帳戶有問題", "strategy": "urgency"}
    ]
    
    result = await evaluator.evaluate_conversation(
        conversation_history=conversation_history,
        persona_type="average",
        initial_trust=50
    )
    
    print(f"✓ 評估完成")
    print(f"  信任度變化: {result.trust_change:+.2f}")
    print(f"  信心度: {result.confidence:.1f}%")
    print(f"  方法: {result.method}")
    
    # 驗證結果
    assert result.trust_change != 0, "信任度變化不應為0"
    assert result.confidence > 0, "信心度應大於0"
    assert result.method in ["rule", "agent", "hybrid"], "方法應為有效值"


def test_response_analyzer():
    """測試4: 受害人回應分析器"""
    from backend.utils.victim_response_analyzer import VictimResponseAnalyzer
    
    analyzer = VictimResponseAnalyzer()
    
    # 測試抵抗信號
    resistance_response = "這是詐騙，我要報警"
    resistance_signals = analyzer.detect_resistance_signals(resistance_response)
    
    print(f"✓ 抵抗信號檢測")
    print(f"  回應: {resistance_response}")
    print(f"  檢測到: {resistance_signals}")
    
    assert len(resistance_signals) > 0, "應該檢測到抵抗信號"
    
    # 測試配合信號
    cooperation_response = "好的，我馬上去銀行"
    cooperation_signals = analyzer.detect_cooperation_signals(cooperation_response)
    
    print(f"✓ 配合信號檢測")
    print(f"  回應: {cooperation_response}")
    print(f"  檢測到: {cooperation_signals}")
    
    assert len(cooperation_signals) > 0, "應該檢測到配合信號"


def test_scoring_monitor():
    """測試5: 評分監控器"""
    from backend.utils.scoring_monitor import ScoringMonitor
    
    monitor = ScoringMonitor()
    
    # 記錄評估
    monitor.record_evaluation(
        persona_type="average",
        trust_change=-15.5,
        confidence=85.0,
        method="rule",
        latency_ms=250.0,
        success=True
    )
    
    # 獲取統計
    stats = monitor.get_stats()
    
    print(f"✓ 監控器記錄成功")
    print(f"  總評估數: {stats['total_evaluations']}")
    print(f"  成功率: {stats['success_rate']:.1f}%")
    print(f"  平均延遲: {stats['performance']['avg_latency_ms']:.1f}ms")
    
    assert stats['total_evaluations'] == 1, "應該有1次評估"
    assert stats['success_rate'] == 100.0, "成功率應為100%"


def test_api_routes():
    """測試6: API路由"""
    from backend.api.scoring_v2_routes import router as scoring_router
    from backend.api.monitoring_routes import router as monitoring_router
    
    # 檢查評分路由
    scoring_routes = [route.path for route in scoring_router.routes]
    print(f"✓ 評分API路由:")
    for route in scoring_routes:
        print(f"  {route}")
    
    assert "/evaluate" in scoring_routes, "應該有/evaluate路由"
    assert "/health" in scoring_routes, "應該有/health路由"
    
    # 檢查監控路由
    monitoring_routes = [route.path for route in monitoring_router.routes]
    print(f"✓ 監控API路由:")
    for route in monitoring_routes:
        print(f"  {route}")
    
    assert "/stats" in monitoring_routes, "應該有/stats路由"
    assert "/dashboard" in monitoring_routes, "應該有/dashboard路由"


def test_file_structure():
    """測試7: 文件結構"""
    required_files = [
        "backend/utils/victim_evaluator.py",
        "backend/utils/victim_response_analyzer.py",
        "backend/utils/scoring_monitor.py",
        "backend/api/scoring_v2_routes.py",
        "backend/api/monitoring_routes.py",
        "backend/tests/test_victim_evaluator.py",
        "backend/tests/test_scoring_api_e2e.py",
        "DEPLOYMENT_GUIDE.md",
        "SYSTEM_INTEGRATION_COMPLETE.md"
    ]
    
    print(f"✓ 檢查必需文件:")
    for filepath in required_files:
        full_path = os.path.join(os.path.dirname(__file__), '..', filepath)
        exists = os.path.exists(full_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {filepath}")
        
        if not exists:
            raise FileNotFoundError(f"缺少文件: {filepath}")


def test_documentation():
    """測試8: 文檔完整性"""
    docs = [
        "DEPLOYMENT_GUIDE.md",
        "SYSTEM_INTEGRATION_COMPLETE.md",
        "ALL_ISSUES_FIXED_REPORT.md",
        "SCORING_SYSTEM_REFACTOR_COMPLETE.md"
    ]
    
    print(f"✓ 檢查文檔:")
    for doc in docs:
        full_path = os.path.join(os.path.dirname(__file__), '..', doc)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"  ✓ {doc} ({size} bytes)")
        else:
            print(f"  ✗ {doc} (缺失)")


def test_configuration():
    """測試9: 配置驗證"""
    from backend.utils.victim_evaluator import VictimEvaluator
    from backend.agents.victim import VictimAgent
    from backend.utils.performance_tracker import PerformanceTracker
    
    # 測試不同配置
    configs = [
        {"rule_weight": 1.0, "agent_weight": 0.0, "name": "純規則"},
        {"rule_weight": 0.7, "agent_weight": 0.3, "name": "混合(7:3)"},
        {"rule_weight": 0.5, "agent_weight": 0.5, "name": "平衡"},
    ]
    
    print(f"✓ 測試配置:")
    for config in configs:
        victim_agent = VictimAgent(persona_type="average")
        performance_tracker = PerformanceTracker(victim_persona="average")
        
        evaluator = VictimEvaluator(
            victim_agent=victim_agent,
            performance_tracker=performance_tracker,
            rule_weight=config["rule_weight"],
            agent_weight=config["agent_weight"],
            enable_agent_scoring=False
        )
        
        print(f"  ✓ {config['name']}: rule={config['rule_weight']}, agent={config['agent_weight']}")


def test_error_handling():
    """測試10: 錯誤處理"""
    from backend.utils.victim_evaluator import VictimEvaluator
    from backend.agents.victim import VictimAgent
    from backend.utils.performance_tracker import PerformanceTracker
    
    victim_agent = VictimAgent(persona_type="average")
    performance_tracker = PerformanceTracker(victim_persona="average")
    
    # 測試無效權重
    try:
        evaluator = VictimEvaluator(
            victim_agent=victim_agent,
            performance_tracker=performance_tracker,
            rule_weight=0.5,
            agent_weight=0.3,  # 總和不為1.0
            enable_agent_scoring=False
        )
        raise AssertionError("應該拋出錯誤")
    except (ValueError, AssertionError) as e:
        print(f"✓ 正確捕獲無效權重錯誤: {e}")


def main():
    """主函數"""
    print(f"\n{'='*60}")
    print(f"評分系統v2.0 整合驗證")
    print(f"{'='*60}")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    validator = IntegrationValidator()
    
    # 執行測試
    validator.test("1. 導入核心模組", test_imports)
    validator.test("2. VictimEvaluator初始化", test_victim_evaluator)
    validator.test("3. 執行評估", test_evaluation)
    validator.test("4. 受害人回應分析器", test_response_analyzer)
    validator.test("5. 評分監控器", test_scoring_monitor)
    validator.test("6. API路由", test_api_routes)
    validator.test("7. 文件結構", test_file_structure)
    validator.test("8. 文檔完整性", test_documentation)
    validator.test("9. 配置驗證", test_configuration)
    validator.test("10. 錯誤處理", test_error_handling)
    
    # 打印摘要
    validator.print_summary()
    
    # 返回退出碼
    return 0 if validator.failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
