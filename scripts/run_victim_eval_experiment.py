"""
受害人Agent評分實驗腳本
測試Agent評分與規則評分的對比效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import json
from datetime import datetime
from typing import List, Dict

# 添加backend到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from utils.victim_evaluator import VictimEvaluator, EvaluationResult
from agents.victim import VictimAgent
from utils.performance_tracker import PerformanceTracker


# 測試對話數據
TEST_CONVERSATIONS = [
    {
        "id": 1,
        "name": "高壓恐嚇案例",
        "persona": "elderly",
        "initial_trust": 50,
        "messages": [
            {"role": "scammer", "content": "你好，我是警察局的，你的銀行帳戶涉嫌洗錢！", "strategy": "authority"},
            {"role": "victim", "content": "什麼？我沒有做違法的事啊！"},
            {"role": "scammer", "content": "現在必須立即配合調查，否則會凍結你所有資產！", "strategy": "urgency"},
            {"role": "victim", "content": "那我該怎麼辦？"},
            {"role": "scammer", "content": "把你的銀行卡號和密碼告訴我，我們需要核實。", "strategy": "authority"}
        ],
        "expected_trust_change": -25,  # 應該大幅下降
        "expected_outcome": "scammer_win"
    },
    {
        "id": 2,
        "name": "溫和誘導案例",
        "persona": "average",
        "initial_trust": 50,
        "messages": [
            {"role": "scammer", "content": "您好，我們公司有個投資機會，年收益15%。", "strategy": "greed"},
            {"role": "victim", "content": "聽起來不錯，但我需要了解更多細節。"},
            {"role": "scammer", "content": "當然，這是政府支持的項目，非常安全。", "strategy": "authority"},
            {"role": "victim", "content": "有什麼證明文件嗎？"},
            {"role": "scammer", "content": "我可以發給您，但名額有限，今天就要決定。", "strategy": "urgency"}
        ],
        "expected_trust_change": -10,  # 輕微下降
        "expected_outcome": "victim_cautious"
    },
    {
        "id": 3,
        "name": "情感操控案例",
        "persona": "elderly",
        "initial_trust": 60,
        "messages": [
            {"role": "scammer", "content": "奶奶，我是你孫子，我出車禍了需要錢！", "strategy": "sympathy"},
            {"role": "victim", "content": "天啊！你在哪裡？嚴重嗎？"},
            {"role": "scammer", "content": "很嚴重，醫院要我先付5萬塊，不然不給治療！", "strategy": "urgency"},
            {"role": "victim", "content": "我馬上去銀行！"},
            {"role": "scammer", "content": "謝謝奶奶，把錢匯到這個帳戶...", "strategy": "sympathy"}
        ],
        "expected_trust_change": -35,  # 大幅下降（情感操控成功）
        "expected_outcome": "scammer_win"
    },
    {
        "id": 4,
        "name": "受害人警覺案例",
        "persona": "overconfident",
        "initial_trust": 30,
        "messages": [
            {"role": "scammer", "content": "恭喜您中獎了！獎金100萬！", "strategy": "greed"},
            {"role": "victim", "content": "我沒參加任何抽獎活動。"},
            {"role": "scammer", "content": "這是系統自動抽選的，您只需要支付稅金5000元。", "strategy": "greed"},
            {"role": "victim", "content": "這明顯是詐騙，我要報警。"},
            {"role": "scammer", "content": "別誤會，這是真的..."}
        ],
        "expected_trust_change": 15,  # 上升（受害人識破騙局）
        "expected_outcome": "victim_win"
    },
    {
        "id": 5,
        "name": "複雜多策略案例",
        "persona": "student",
        "initial_trust": 45,
        "messages": [
            {"role": "scammer", "content": "同學你好，我是學校財務處的。", "strategy": "authority"},
            {"role": "victim", "content": "有什麼事嗎？"},
            {"role": "scammer", "content": "你的獎學金申請通過了，但需要先繳保證金。", "strategy": "greed"},
            {"role": "victim", "content": "保證金？多少錢？"},
            {"role": "scammer", "content": "3000元，今天下午5點前要匯款，否則名額給別人。", "strategy": "urgency"},
            {"role": "victim", "content": "我可以去學校辦公室確認嗎？"},
            {"role": "scammer", "content": "辦公室今天休息，只能線上處理。", "strategy": "authority"}
        ],
        "expected_trust_change": -15,  # 中度下降
        "expected_outcome": "uncertain"
    },
    {
        "id": 6,
        "name": "技術支援詐騙",
        "persona": "elderly",
        "initial_trust": 55,
        "messages": [
            {"role": "scammer", "content": "您的電腦檢測到病毒，我是微軟技術支援。", "strategy": "fear"},
            {"role": "victim", "content": "真的嗎？我該怎麼辦？"},
            {"role": "scammer", "content": "需要遠程連接您的電腦清除病毒，費用200美元。", "strategy": "authority"},
            {"role": "victim", "content": "這麼貴？"},
            {"role": "scammer", "content": "不處理的話，您的銀行資料會被盜取！", "strategy": "fear"}
        ],
        "expected_trust_change": -20,
        "expected_outcome": "scammer_advantage"
    },
    {
        "id": 7,
        "name": "浪漫詐騙案例",
        "persona": "average",
        "initial_trust": 70,
        "messages": [
            {"role": "scammer", "content": "親愛的，我在國外遇到麻煩了。", "strategy": "sympathy"},
            {"role": "victim", "content": "怎麼了？需要幫忙嗎？"},
            {"role": "scammer", "content": "我的錢包被偷了，需要借2000元買機票回國。", "strategy": "sympathy"},
            {"role": "victim", "content": "你為什麼不找當地警察？"},
            {"role": "scammer", "content": "警察說要等很久，我真的很需要你的幫助。", "strategy": "sympathy"}
        ],
        "expected_trust_change": -18,
        "expected_outcome": "uncertain"
    },
    {
        "id": 8,
        "name": "投資詐騙（專業包裝）",
        "persona": "overconfident",
        "initial_trust": 40,
        "messages": [
            {"role": "scammer", "content": "我們是持牌投資顧問，專注加密貨幣投資。", "strategy": "authority"},
            {"role": "victim", "content": "你們的牌照號碼是？"},
            {"role": "scammer", "content": "SEC-2024-8888，您可以查證。我們有專業團隊。", "strategy": "authority"},
            {"role": "victim", "content": "最低投資金額是多少？"},
            {"role": "scammer", "content": "1萬美元起，但本週有優惠，5千就可以。", "strategy": "greed"}
        ],
        "expected_trust_change": -8,
        "expected_outcome": "victim_cautious"
    },
    {
        "id": 9,
        "name": "政府補助詐騙",
        "persona": "elderly",
        "initial_trust": 65,
        "messages": [
            {"role": "scammer", "content": "您好，政府有疫情補助金，您符合資格。", "strategy": "greed"},
            {"role": "victim", "content": "真的嗎？我需要做什麼？"},
            {"role": "scammer", "content": "提供您的身份證號和銀行帳號即可。", "strategy": "authority"},
            {"role": "victim", "content": "為什麼需要銀行帳號？"},
            {"role": "scammer", "content": "要把補助金匯給您啊，這是標準程序。", "strategy": "authority"}
        ],
        "expected_trust_change": -22,
        "expected_outcome": "scammer_advantage"
    },
    {
        "id": 10,
        "name": "受害人完全識破",
        "persona": "student",
        "initial_trust": 25,
        "messages": [
            {"role": "scammer", "content": "您的包裹被海關扣留，需要繳稅。", "strategy": "authority"},
            {"role": "victim", "content": "我沒有訂購任何國際包裹。"},
            {"role": "scammer", "content": "可能是朋友寄給您的驚喜。", "strategy": "greed"},
            {"role": "victim", "content": "這是詐騙，我已經錄音了。"},
            {"role": "scammer", "content": "不是詐騙，請相信我們..."}
        ],
        "expected_trust_change": 20,
        "expected_outcome": "victim_win"
    }
]


class ExperimentRunner:
    """實驗執行器"""
    
    def __init__(self):
        self.results = []
        self.performance_tracker = PerformanceTracker()
        
    async def run_experiment(self):
        """執行完整實驗"""
        print("=" * 80)
        print("受害人Agent評分實驗")
        print("=" * 80)
        print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"測試案例數: {len(TEST_CONVERSATIONS)}")
        print()
        
        # 初始化Agent和評估器
        victim_agent = VictimAgent()
        
        # 測試三種模式
        modes = [
            {"name": "純規則評分", "rule_weight": 1.0, "agent_weight": 0.0, "enable_agent": False},
            {"name": "純Agent評分", "rule_weight": 0.0, "agent_weight": 1.0, "enable_agent": True},
            {"name": "混合評分(7:3)", "rule_weight": 0.7, "agent_weight": 0.3, "enable_agent": True}
        ]
        
        for mode in modes:
            print(f"\n{'=' * 80}")
            print(f"測試模式: {mode['name']}")
            print(f"{'=' * 80}\n")
            
            evaluator = VictimEvaluator(
                victim_agent=victim_agent,
                performance_tracker=self.performance_tracker,
                rule_weight=mode['rule_weight'],
                agent_weight=mode['agent_weight'],
                enable_agent_scoring=mode['enable_agent']
            )
            
            mode_results = []
            
            for i, conv in enumerate(TEST_CONVERSATIONS, 1):
                print(f"[{i}/{len(TEST_CONVERSATIONS)}] 測試: {conv['name']}")
                print(f"  人設: {conv['persona']}, 初始信任度: {conv['initial_trust']}")
                
                try:
                    # 執行評估
                    result = await evaluator.evaluate_conversation(
                        conversation_history=conv['messages'],
                        persona_type=conv['persona'],
                        initial_trust=conv['initial_trust']
                    )
                    
                    # 計算誤差
                    error = abs(result.trust_change - conv['expected_trust_change'])
                    
                    print(f"  預期變化: {conv['expected_trust_change']}")
                    print(f"  實際變化: {result.trust_change:.2f}")
                    print(f"  誤差: {error:.2f}")
                    print(f"  信心度: {result.confidence:.1f}%")
                    print(f"  方法: {result.method}")
                    print()
                    
                    mode_results.append({
                        "conversation_id": conv['id'],
                        "conversation_name": conv['name'],
                        "expected": conv['expected_trust_change'],
                        "actual": result.trust_change,
                        "error": error,
                        "confidence": result.confidence,
                        "method": result.method,
                        "rule_score": result.rule_score,
                        "agent_score": result.agent_score
                    })
                    
                except Exception as e:
                    print(f"  ❌ 錯誤: {str(e)}")
                    mode_results.append({
                        "conversation_id": conv['id'],
                        "conversation_name": conv['name'],
                        "error": str(e)
                    })
            
            # 計算統計數據
            valid_results = [r for r in mode_results if 'actual' in r]
            if valid_results:
                avg_error = sum(r['error'] for r in valid_results) / len(valid_results)
                avg_confidence = sum(r['confidence'] for r in valid_results) / len(valid_results)
                
                print(f"\n{mode['name']} - 統計結果:")
                print(f"  平均誤差: {avg_error:.2f}")
                print(f"  平均信心度: {avg_confidence:.1f}%")
                print(f"  成功率: {len(valid_results)}/{len(TEST_CONVERSATIONS)}")
            
            self.results.append({
                "mode": mode['name'],
                "config": mode,
                "results": mode_results,
                "statistics": {
                    "avg_error": avg_error if valid_results else None,
                    "avg_confidence": avg_confidence if valid_results else None,
                    "success_rate": f"{len(valid_results)}/{len(TEST_CONVERSATIONS)}"
                }
            })
        
        # 保存結果
        self.save_results()
        
        # 生成報告
        self.generate_report()
        
    def save_results(self):
        """保存實驗結果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"victim_eval_experiment_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_conversations": len(TEST_CONVERSATIONS),
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 結果已保存至: {filepath}")
        
    def generate_report(self):
        """生成實驗報告"""
        print("\n" + "=" * 80)
        print("實驗總結報告")
        print("=" * 80)
        
        for mode_result in self.results:
            print(f"\n【{mode_result['mode']}】")
            stats = mode_result['statistics']
            
            if stats['avg_error'] is not None:
                print(f"  平均誤差: {stats['avg_error']:.2f}")
                print(f"  平均信心度: {stats['avg_confidence']:.1f}%")
                print(f"  成功率: {stats['success_rate']}")
                
                # 評分
                if stats['avg_error'] < 5:
                    grade = "優秀"
                elif stats['avg_error'] < 10:
                    grade = "良好"
                elif stats['avg_error'] < 15:
                    grade = "及格"
                else:
                    grade = "需改進"
                    
                print(f"  評級: {grade}")
        
        print("\n" + "=" * 80)
        print("建議:")
        print("=" * 80)
        
        # 比較三種模式
        if len(self.results) >= 3:
            errors = [r['statistics']['avg_error'] for r in self.results if r['statistics']['avg_error']]
            
            if errors:
                best_idx = errors.index(min(errors))
                best_mode = self.results[best_idx]['mode']
                
                print(f"✅ 最佳模式: {best_mode}")
                print(f"   平均誤差: {errors[best_idx]:.2f}")
                
                if best_idx == 2:  # 混合模式
                    print("\n推薦使用混合評分模式，因為:")
                    print("  1. 結合規則穩定性和Agent靈活性")
                    print("  2. 誤差最小，準確度最高")
                    print("  3. 可根據實際情況調整權重")
                elif best_idx == 0:  # 純規則
                    print("\n純規則評分表現最佳，建議:")
                    print("  1. 繼續優化規則系統")
                    print("  2. Agent評分可作為輔助參考")
                elif best_idx == 1:  # 純Agent
                    print("\n純Agent評分表現最佳，但需注意:")
                    print("  1. 確保Agent穩定性")
                    print("  2. 考慮計算成本")
                    print("  3. 建議仍保留規則作為備份")
        
        print("\n實驗完成！")


async def main():
    """主函數"""
    runner = ExperimentRunner()
    await runner.run_experiment()


if __name__ == "__main__":
    asyncio.run(main())
