"""
性能優化實驗腳本
測試不同配置以降低評估誤差到<5（優秀級別）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from datetime import datetime
import json
from typing import Dict, List

from backend.agents.victim import VictimAgent
from backend.utils.performance_tracker import PerformanceTracker
from backend.utils.victim_evaluator import VictimEvaluator


# 測試案例（與之前相同）
TEST_CASES = [
    {
        "name": "高壓權威詐騙",
        "conversation": [
            {"role": "scammer", "content": "你好，我是警察局的，你的銀行帳戶涉嫌洗錢！", "strategy": "authority"},
            {"role": "victim", "content": "什麼？我沒有做違法的事啊！"},
            {"role": "scammer", "content": "現在必須立即配合調查，否則會凍結你所有資產！", "strategy": "urgency"}
        ],
        "persona": "elderly",
        "initial_trust": 50,
        "expected_change": -20,
        "description": "老年人面對高壓權威詐騙"
    },
    {
        "name": "受害人識破騙局",
        "conversation": [
            {"role": "scammer", "content": "恭喜你中獎了！請提供銀行帳號領取獎金。", "strategy": "greed"},
            {"role": "victim", "content": "這是詐騙，我要報警！"}
        ],
        "persona": "overconfident",
        "initial_trust": 30,
        "expected_change": 15,
        "description": "過度自信者識破中獎詐騙"
    },
    {
        "name": "專家介入警告",
        "conversation": [
            {"role": "scammer", "content": "你的快遞有問題，需要補繳費用。", "strategy": "urgency"},
            {"role": "victim", "content": "好的，我馬上處理。"},
            {"role": "expert", "content": "這是典型的詐騙手法，不要相信！", "strategy": "none"}
        ],
        "persona": "student",
        "initial_trust": 60,
        "expected_change": 10,
        "description": "學生受到專家警告"
    },
    {
        "name": "情感操控",
        "conversation": [
            {"role": "scammer", "content": "奶奶，我是你孫子，我出事了需要錢！", "strategy": "sympathy"},
            {"role": "victim", "content": "你是誰？我孫子不是這個聲音。"}
        ],
        "persona": "elderly",
        "initial_trust": 70,
        "expected_change": 5,
        "description": "老年人識別假冒親人"
    },
    {
        "name": "多輪說服",
        "conversation": [
            {"role": "scammer", "content": "我是銀行客服，您的信用卡有異常交易。", "strategy": "authority"},
            {"role": "victim", "content": "什麼異常？"},
            {"role": "scammer", "content": "有人在國外刷了您的卡，需要立即凍結。", "strategy": "urgency"},
            {"role": "victim", "content": "那怎麼辦？"}
        ],
        "persona": "average",
        "initial_trust": 50,
        "expected_change": -15,
        "description": "普通人面對多輪說服"
    },
    {
        "name": "低壓試探",
        "conversation": [
            {"role": "scammer", "content": "你好，請問你需要貸款嗎？", "strategy": "greed"},
            {"role": "victim", "content": "不需要，謝謝。"}
        ],
        "persona": "average",
        "initial_trust": 40,
        "expected_change": 2,
        "description": "普通人拒絕低壓試探"
    },
    {
        "name": "激將法",
        "conversation": [
            {"role": "scammer", "content": "這個投資機會很難得，不過可能不適合你。", "strategy": "greed"},
            {"role": "victim", "content": "為什麼不適合我？"}
        ],
        "persona": "overconfident",
        "initial_trust": 45,
        "expected_change": -8,
        "description": "過度自信者中激將法"
    },
    {
        "name": "專家詳細分析",
        "conversation": [
            {"role": "scammer", "content": "你中獎了，但需要先繳稅。", "strategy": "greed"},
            {"role": "victim", "content": "真的嗎？"},
            {"role": "expert", "content": "這是典型的預付費詐騙，真正的中獎不需要先繳費。", "strategy": "none"}
        ],
        "persona": "student",
        "initial_trust": 55,
        "expected_change": 12,
        "description": "學生接受專家詳細分析"
    },
    {
        "name": "恐嚇威脅",
        "conversation": [
            {"role": "scammer", "content": "你的個人信息已被盜用，立即配合調查！", "strategy": "fear"},
            {"role": "victim", "content": "我該怎麼做？"}
        ],
        "persona": "elderly",
        "initial_trust": 60,
        "expected_change": -18,
        "description": "老年人面對恐嚇威脅"
    },
    {
        "name": "理性分析",
        "conversation": [
            {"role": "scammer", "content": "限時優惠，現在購買可享受50%折扣！", "strategy": "greed"},
            {"role": "victim", "content": "讓我先查一下這個公司的評價。"}
        ],
        "persona": "average",
        "initial_trust": 35,
        "expected_change": 8,
        "description": "普通人理性分析優惠"
    }
]


# 優化配置方案
OPTIMIZATION_CONFIGS = [
    {
        "name": "基準配置（當前）",
        "rule_weight": 0.7,
        "agent_weight": 0.3,
        "enable_agent": True,
        "description": "當前使用的配置"
    },
    {
        "name": "純規則優化",
        "rule_weight": 1.0,
        "agent_weight": 0.0,
        "enable_agent": False,
        "description": "純規則評分，優化規則權重"
    },
    {
        "name": "平衡配置",
        "rule_weight": 0.6,
        "agent_weight": 0.4,
        "enable_agent": True,
        "description": "增加Agent權重"
    },
    {
        "name": "Agent主導",
        "rule_weight": 0.4,
        "agent_weight": 0.6,
        "enable_agent": True,
        "description": "Agent為主導"
    },
    {
        "name": "高信心配置",
        "rule_weight": 0.8,
        "agent_weight": 0.2,
        "enable_agent": True,
        "description": "偏向規則以提高穩定性"
    }
]


async def run_single_test(
    evaluator: VictimEvaluator,
    test_case: Dict,
    config_name: str
) -> Dict:
    """運行單個測試案例"""
    try:
        result = await evaluator.evaluate_conversation(
            conversation_history=test_case["conversation"],
            persona_type=test_case["persona"],
            initial_trust=test_case["initial_trust"]
        )
        
        # 計算誤差
        error = abs(result.trust_change - test_case["expected_change"])
        
        return {
            "test_name": test_case["name"],
            "config": config_name,
            "expected": test_case["expected_change"],
            "actual": result.trust_change,
            "error": error,
            "confidence": result.confidence,
            "method": result.method,
            "success": True
        }
    except Exception as e:
        return {
            "test_name": test_case["name"],
            "config": config_name,
            "success": False,
            "error_message": str(e)
        }


async def run_optimization_experiment():
    """運行優化實驗"""
    print("=" * 80)
    print("評分系統性能優化實驗")
    print("目標：降低平均誤差到 <5（優秀級別）")
    print("=" * 80)
    print()
    
    all_results = []
    
    for config in OPTIMIZATION_CONFIGS:
        print(f"\n{'='*80}")
        print(f"測試配置: {config['name']}")
        print(f"說明: {config['description']}")
        print(f"規則權重: {config['rule_weight']}, Agent權重: {config['agent_weight']}")
        print(f"{'='*80}\n")
        
        config_results = []
        
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"[{i}/{len(TEST_CASES)}] {test_case['name']}")
            print(f"  描述: {test_case['description']}")
            print(f"  預期變化: {test_case['expected_change']:+d}")
            
            # 創建評估器
            victim_agent = VictimAgent(persona_type=test_case["persona"])
            performance_tracker = PerformanceTracker(victim_persona=test_case["persona"])
            
            evaluator = VictimEvaluator(
                victim_agent=victim_agent,
                performance_tracker=performance_tracker,
                rule_weight=config["rule_weight"],
                agent_weight=config["agent_weight"],
                enable_agent_scoring=config["enable_agent"]
            )
            
            # 運行測試
            result = await run_single_test(evaluator, test_case, config["name"])
            config_results.append(result)
            
            if result["success"]:
                print(f"  實際變化: {result['actual']:+.2f}")
                print(f"  誤差: {result['error']:.2f}")
                print(f"  信心度: {result['confidence']:.1f}%")
                print(f"  方法: {result['method']}")
                
                # 評級
                if result['error'] < 5:
                    grade = "優秀 ⭐⭐⭐"
                elif result['error'] < 10:
                    grade = "良好 ⭐⭐"
                elif result['error'] < 15:
                    grade = "及格 ⭐"
                else:
                    grade = "需改進"
                print(f"  評級: {grade}")
            else:
                print(f"  ❌ 失敗: {result['error_message']}")
            
            print()
        
        # 計算配置統計
        successful_results = [r for r in config_results if r["success"]]
        
        if successful_results:
            avg_error = sum(r["error"] for r in successful_results) / len(successful_results)
            avg_confidence = sum(r["confidence"] for r in successful_results) / len(successful_results)
            
            # 評級統計
            excellent = sum(1 for r in successful_results if r["error"] < 5)
            good = sum(1 for r in successful_results if 5 <= r["error"] < 10)
            pass_grade = sum(1 for r in successful_results if 10 <= r["error"] < 15)
            needs_improvement = sum(1 for r in successful_results if r["error"] >= 15)
            
            # 方向正確率
            direction_correct = sum(
                1 for r in successful_results
                if (r["expected"] > 0 and r["actual"] > 0) or
                   (r["expected"] < 0 and r["actual"] < 0) or
                   (r["expected"] == 0 and abs(r["actual"]) < 3)
            )
            direction_accuracy = (direction_correct / len(successful_results)) * 100
            
            config_summary = {
                "config_name": config["name"],
                "avg_error": avg_error,
                "avg_confidence": avg_confidence,
                "direction_accuracy": direction_accuracy,
                "excellent_count": excellent,
                "good_count": good,
                "pass_count": pass_grade,
                "needs_improvement_count": needs_improvement,
                "total_tests": len(successful_results),
                "results": config_results
            }
            
            all_results.append(config_summary)
            
            print(f"\n配置 '{config['name']}' 統計:")
            print(f"  平均誤差: {avg_error:.2f}")
            print(f"  平均信心度: {avg_confidence:.1f}%")
            print(f"  方向正確率: {direction_accuracy:.1f}%")
            print(f"  優秀案例: {excellent}/{len(successful_results)} ({excellent/len(successful_results)*100:.1f}%)")
            print(f"  良好案例: {good}/{len(successful_results)} ({good/len(successful_results)*100:.1f}%)")
            print(f"  及格案例: {pass_grade}/{len(successful_results)} ({pass_grade/len(successful_results)*100:.1f}%)")
            print(f"  需改進: {needs_improvement}/{len(successful_results)} ({needs_improvement/len(successful_results)*100:.1f}%)")
            
            # 評級
            if avg_error < 5:
                overall_grade = "優秀 ⭐⭐⭐"
            elif avg_error < 10:
                overall_grade = "良好 ⭐⭐"
            elif avg_error < 15:
                overall_grade = "及格 ⭐"
            else:
                overall_grade = "需改進"
            
            print(f"  整體評級: {overall_grade}")
    
    # 生成最終報告
    print(f"\n{'='*80}")
    print("優化實驗總結")
    print(f"{'='*80}\n")
    
    # 排序配置（按平均誤差）
    all_results.sort(key=lambda x: x["avg_error"])
    
    print("配置排名（按平均誤差）:\n")
    for i, result in enumerate(all_results, 1):
        print(f"{i}. {result['config_name']}")
        print(f"   平均誤差: {result['avg_error']:.2f}")
        print(f"   方向正確率: {result['direction_accuracy']:.1f}%")
        print(f"   優秀案例比例: {result['excellent_count']}/{result['total_tests']} ({result['excellent_count']/result['total_tests']*100:.1f}%)")
        print()
    
    # 最佳配置
    best_config = all_results[0]
    print(f"🏆 最佳配置: {best_config['config_name']}")
    print(f"   平均誤差: {best_config['avg_error']:.2f}")
    print(f"   平均信心度: {best_config['avg_confidence']:.1f}%")
    print(f"   方向正確率: {best_config['direction_accuracy']:.1f}%")
    
    if best_config['avg_error'] < 5:
        print(f"\n✅ 目標達成！平均誤差 {best_config['avg_error']:.2f} < 5（優秀級別）")
    else:
        print(f"\n⚠️ 未達目標。平均誤差 {best_config['avg_error']:.2f} >= 5")
        print(f"   建議: 繼續優化Agent提示詞或調整規則評分邏輯")
    
    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/optimization_experiment_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "configs_tested": len(OPTIMIZATION_CONFIGS),
            "test_cases": len(TEST_CASES),
            "results": all_results,
            "best_config": best_config
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 結果已保存到: {output_file}")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(run_optimization_experiment())
