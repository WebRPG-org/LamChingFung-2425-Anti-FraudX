"""
受害人Agent評分實驗腳本
測試混合評分系統的可行性
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from typing import List, Dict
from utils.victim_evaluator import VictimEvaluator
from utils.performance_tracker import PerformanceTracker
from agents.victim import VictimAgent

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VictimScoringExperiment:
    """受害人評分實驗"""
    
    # 測試對話數據
    TEST_CONVERSATIONS = [
        {
            "id": 1,
            "persona": "elderly",
            "scenario": "假冒銀行",
            "turns": [
                {
                    "scammer": "你好，我係銀行職員，你嘅帳戶有問題，需要立即處理。",
                    "victim": "咩問題？我唔記得有問題。",
                    "expert": "唔好驚，銀行唔會咁樣打電話嚟，呢個係詐騙。"
                },
                {
                    "scammer": "你嘅帳戶被凍結咗，如果唔處理，你啲錢會冇咗。",
                    "victim": "真係？咁點算？",
                    "expert": "銀行唔會話凍結就凍結，你應該掛斷電話，打去銀行官方熱線確認。"
                }
            ]
        },
        {
            "id": 2,
            "persona": "average",
            "scenario": "假冒警察",
            "turns": [
                {
                    "scammer": "我係警察，你涉嫌一宗洗黑錢案件，需要配合調查。",
                    "victim": "我冇做過啊，點解會咁？",
                    "expert": "真正嘅警察唔會電話通知，而且唔會要求你轉帳。"
                },
                {
                    "scammer": "你需要將你嘅存款轉到安全帳戶，證明你嘅清白。",
                    "victim": "但係我真係冇做過...要轉幾多？",
                    "expert": "呢個係典型嘅詐騙手法，千萬唔好轉帳，立即報警。"
                }
            ]
        },
        {
            "id": 3,
            "persona": "overconfident",
            "scenario": "投資詐騙",
            "turns": [
                {
                    "scammer": "我哋有個穩賺唔賠嘅投資項目，回報率高達30%。",
                    "victim": "30%？聽落好吸引，但會唔會有風險？",
                    "expert": "世界上冇穩賺唔賠嘅投資，呢個係詐騙。"
                },
                {
                    "scammer": "你咁聰明，應該明白呢個機會難得，唔係人人都有資格。",
                    "victim": "咁都係...不過我想睇下詳細資料先。",
                    "expert": "激將法係詐騙常用手法，唔好被佢哋影響，要理性分析。"
                }
            ]
        }
    ]
    
    def __init__(self):
        """初始化實驗"""
        self.results = []
        logger.info("🧪 受害人評分實驗初始化")
    
    def run_experiment(self, enable_agent_scoring: bool = True):
        """
        運行實驗
        
        Args:
            enable_agent_scoring: 是否啟用Agent評分
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 開始實驗 - Agent評分={'啟用' if enable_agent_scoring else '禁用'}")
        logger.info(f"{'='*60}\n")
        
        for conv in self.TEST_CONVERSATIONS:
            logger.info(f"\n--- 測試對話 #{conv['id']}: {conv['scenario']} ({conv['persona']}型) ---\n")
            
            # 創建Agent和Tracker
            try:
                victim_agent = VictimAgent(persona_type=conv['persona'])
                tracker = PerformanceTracker(victim_persona=conv['persona'])
                
                # 創建評估器
                evaluator = VictimEvaluator(
                    victim_agent=victim_agent,
                    performance_tracker=tracker,
                    rule_weight=0.7,
                    agent_weight=0.3,
                    enable_agent_scoring=enable_agent_scoring
                )
                
                # 評估每一輪
                conv_results = []
                for i, turn in enumerate(conv['turns'], 1):
                    logger.info(f"\n📍 第{i}輪對話:")
                    
                    # 評估騙徒訊息
                    logger.info(f"騙徒: {turn['scammer'][:50]}...")
                    scammer_result = evaluator.evaluate_message(
                        message=turn['scammer'],
                        sender='scammer',
                        victim_response=turn['victim'],
                        use_hybrid=enable_agent_scoring
                    )
                    
                    logger.info(f"  規則評分: {scammer_result.rule_score.get('trust_change', 0):+.1f}")
                    if scammer_result.agent_score:
                        logger.info(f"  Agent評分: {scammer_result.agent_score.get('trust_change', 0):+.1f}")
                        logger.info(f"  Agent理由: {scammer_result.agent_score.get('reasoning', 'N/A')}")
                    logger.info(f"  ✅ 最終分數: {scammer_result.trust_change:+.1f}")
                    logger.info(f"  信心度: {scammer_result.confidence:.1f}%")
                    
                    # 評估專家訊息
                    logger.info(f"\n專家: {turn['expert'][:50]}...")
                    expert_result = evaluator.evaluate_message(
                        message=turn['expert'],
                        sender='expert',
                        victim_response=turn['victim'],
                        use_hybrid=enable_agent_scoring
                    )
                    
                    logger.info(f"  規則評分: {expert_result.rule_score.get('trust_change', 0):+.1f}")
                    if expert_result.agent_score:
                        logger.info(f"  Agent評分: {expert_result.agent_score.get('trust_change', 0):+.1f}")
                        logger.info(f"  Agent理由: {expert_result.agent_score.get('reasoning', 'N/A')}")
                    logger.info(f"  ✅ 最終分數: {expert_result.trust_change:+.1f}")
                    logger.info(f"  信心度: {expert_result.confidence:.1f}%")
                    
                    conv_results.append({
                        "turn": i,
                        "scammer": scammer_result,
                        "expert": expert_result
                    })
                
                # 生成對話報告
                report = evaluator.generate_comparison_report()
                
                self.results.append({
                    "conversation_id": conv['id'],
                    "persona": conv['persona'],
                    "scenario": conv['scenario'],
                    "results": conv_results,
                    "report": report
                })
                
                # 顯示對話總結
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 對話 #{conv['id']} 總結:")
                if report.get('summary'):
                    logger.info(f"  總評估次數: {report['summary']['total_evaluations']}")
                    logger.info(f"  平均差異: {report['summary']['avg_difference']:.2f}")
                    logger.info(f"  相關性: {report['summary']['correlation']:.3f}")
                    logger.info(f"  平均信心度: {report['summary']['avg_confidence']:.1f}%")
                logger.info(f"{'='*60}\n")
                
            except Exception as e:
                logger.error(f"❌ 對話 #{conv['id']} 執行失敗: {e}")
                import traceback
                traceback.print_exc()
    
    def generate_final_report(self) -> Dict:
        """生成最終實驗報告"""
        if not self.results:
            return {"status": "no_data"}
        
        # 統計所有對話的數據
        all_differences = []
        all_correlations = []
        all_confidences = []
        
        for result in self.results:
            report = result.get('report', {})
            summary = report.get('summary', {})
            
            if summary:
                all_differences.append(summary.get('avg_difference', 0))
                all_correlations.append(summary.get('correlation', 0))
                all_confidences.append(summary.get('avg_confidence', 0))
        
        final_report = {
            "experiment_summary": {
                "total_conversations": len(self.results),
                "avg_difference": sum(all_differences) / len(all_differences) if all_differences else 0,
                "avg_correlation": sum(all_correlations) / len(all_correlations) if all_correlations else 0,
                "avg_confidence": sum(all_confidences) / len(all_confidences) if all_confidences else 0
            },
            "by_persona": self._analyze_by_persona(),
            "recommendations": self._generate_final_recommendations(
                sum(all_differences) / len(all_differences) if all_differences else 0,
                sum(all_correlations) / len(all_correlations) if all_correlations else 0
            )
        }
        
        return final_report
    
    def _analyze_by_persona(self) -> Dict:
        """按persona分析結果"""
        by_persona = {}
        
        for result in self.results:
            persona = result['persona']
            report = result.get('report', {})
            summary = report.get('summary', {})
            
            if persona not in by_persona:
                by_persona[persona] = {
                    "count": 0,
                    "avg_difference": 0,
                    "avg_correlation": 0,
                    "avg_confidence": 0
                }
            
            by_persona[persona]["count"] += 1
            if summary:
                by_persona[persona]["avg_difference"] += summary.get('avg_difference', 0)
                by_persona[persona]["avg_correlation"] += summary.get('correlation', 0)
                by_persona[persona]["avg_confidence"] += summary.get('avg_confidence', 0)
        
        # 計算平均值
        for persona in by_persona:
            count = by_persona[persona]["count"]
            if count > 0:
                by_persona[persona]["avg_difference"] /= count
                by_persona[persona]["avg_correlation"] /= count
                by_persona[persona]["avg_confidence"] /= count
        
        return by_persona
    
    def _generate_final_recommendations(self, avg_diff: float, avg_corr: float) -> List[str]:
        """生成最終建議"""
        recommendations = []
        
        if avg_diff < 2:
            recommendations.append("✅ 規則和Agent評分高度一致，混合評分系統可行")
        elif avg_diff < 4:
            recommendations.append("⚠️ 規則和Agent評分有一定差異，建議調整prompt或權重")
        else:
            recommendations.append("❌ 規則和Agent評分差異較大，需要進一步優化")
        
        if avg_corr > 0.7:
            recommendations.append("✅ 規則和Agent評分高度相關，可以增加Agent權重")
        elif avg_corr > 0.5:
            recommendations.append("⚠️ 規則和Agent評分中度相關，當前權重合理")
        else:
            recommendations.append("❌ 規則和Agent評分相關性低，建議增加訓練數據")
        
        recommendations.append(f"📊 建議權重配置: 規則{70-int(avg_corr*20)}% + Agent{30+int(avg_corr*20)}%")
        
        return recommendations
    
    def print_final_report(self):
        """打印最終報告"""
        report = self.generate_final_report()
        
        print("\n" + "="*80)
        print("📊 受害人Agent評分實驗 - 最終報告")
        print("="*80 + "\n")
        
        summary = report.get('experiment_summary', {})
        print("總體統計:")
        print(f"  測試對話數: {summary.get('total_conversations', 0)}")
        print(f"  平均差異: {summary.get('avg_difference', 0):.2f}")
        print(f"  平均相關性: {summary.get('avg_correlation', 0):.3f}")
        print(f"  平均信心度: {summary.get('avg_confidence', 0):.1f}%")
        print()
        
        by_persona = report.get('by_persona', {})
        if by_persona:
            print("按Persona分析:")
            for persona, stats in by_persona.items():
                print(f"\n  {persona}型:")
                print(f"    測試次數: {stats['count']}")
                print(f"    平均差異: {stats['avg_difference']:.2f}")
                print(f"    平均相關性: {stats['avg_correlation']:.3f}")
                print(f"    平均信心度: {stats['avg_confidence']:.1f}%")
        print()
        
        recommendations = report.get('recommendations', [])
        if recommendations:
            print("建議:")
            for rec in recommendations:
                print(f"  {rec}")
        print()
        
        print("="*80 + "\n")


def main():
    """主函數"""
    print("\n" + "="*80)
    print("🧪 受害人Agent評分實驗")
    print("="*80 + "\n")
    
    # 創建實驗
    experiment = VictimScoringExperiment()
    
    # 運行實驗（啟用Agent評分）
    try:
        experiment.run_experiment(enable_agent_scoring=True)
    except Exception as e:
        logger.error(f"❌ 實驗執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 打印最終報告
    experiment.print_final_report()
    
    print("✅ 實驗完成！")
    print("\n詳細評估報告已保存在日誌中。")
    print("如需查看完整數據，請檢查 evaluation_history.json\n")


if __name__ == "__main__":
    main()
