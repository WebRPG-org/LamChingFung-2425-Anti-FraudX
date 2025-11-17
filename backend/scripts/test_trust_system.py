"""
信任度系统测试工具
测试受害者agent的信任度变化是否正常工作
"""

import os
import sys
import asyncio
import re
from typing import Dict, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.victim import VictimAgent
from agents.scammer import ScammerAgent
from agents.expert import ExpertAgent
from scripts.real_dialogue_runner import RealDialogueRunner
from utils.logger import log


class TrustAnalyzer:
    """分析对话中的信任度信号"""
    
    # 高信任度标志
    HIGH_TRUST_SIGNALS = [
        "好啊", "我會照做", "等陣我就", "咁我依家", "你幫我",
        "真係㗎？咁好", "多謝晒", "咁我要點做", "好彩有你",
        "我即刻", "我而家就", "我相信你", "係咪真㗎？咁好"
    ]
    
    # 中等信任度标志（犹豫）
    MEDIUM_TRUST_SIGNALS = [
        "咁我諗諗先", "唔知", "點算好", "會唔會", "安唔安全",
        "我有啲擔心", "咁複雜", "我要問下", "唔係好明",
        "係咪真係要", "真係要咁做"
    ]
    
    # 低信任度标志（怀疑）
    LOW_TRUST_SIGNALS = [
        "我唔信", "呢個唔啱", "點解", "好奇怪", "有問題",
        "我要諗下", "我唔做", "等我問下", "唔係好信",
        "你講嘅唔合理", "我唔會", "唔好"
    ]
    
    @staticmethod
    def estimate_trust_level(dialogue: str) -> Dict:
        """
        根据对话内容估算信任度
        
        Returns:
            {
                "estimated_trust": 0-100,
                "level": "high/medium/low",
                "signals": [信号列表],
                "explanation": "分析说明"
            }
        """
        dialogue_lower = dialogue.lower()
        
        high_count = sum(1 for signal in TrustAnalyzer.HIGH_TRUST_SIGNALS if signal in dialogue)
        medium_count = sum(1 for signal in TrustAnalyzer.MEDIUM_TRUST_SIGNALS if signal in dialogue)
        low_count = sum(1 for signal in TrustAnalyzer.LOW_TRUST_SIGNALS if signal in dialogue)
        
        found_signals = []
        if high_count > 0:
            found_signals.extend([s for s in TrustAnalyzer.HIGH_TRUST_SIGNALS if s in dialogue])
        if medium_count > 0:
            found_signals.extend([s for s in TrustAnalyzer.MEDIUM_TRUST_SIGNALS if s in dialogue])
        if low_count > 0:
            found_signals.extend([s for s in TrustAnalyzer.LOW_TRUST_SIGNALS if s in dialogue])
        
        # 计算信任度分数
        trust_score = 50  # 基础分数
        trust_score += high_count * 15
        trust_score += medium_count * 5
        trust_score -= low_count * 15
        trust_score = max(0, min(100, trust_score))  # 限制在0-100
        
        # 判定等级
        if trust_score >= 70:
            level = "high"
        elif trust_score >= 40:
            level = "medium"
        else:
            level = "low"
        
        explanation = f"高信任信号: {high_count}, 中等: {medium_count}, 低信任: {low_count}"
        
        return {
            "estimated_trust": trust_score,
            "level": level,
            "signals": found_signals[:5],  # 最多显示5个
            "explanation": explanation,
            "signal_counts": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            }
        }


async def test_trust_scenarios():
    """测试不同场景下的信任度变化"""
    
    print("\n" + "="*80)
    print("🧪 信任度系统测试")
    print("="*80 + "\n")
    
    runner = RealDialogueRunner()
    ok = runner.initialize_agents(victim_persona="elderly")
    if not ok:
        print("❌ Agent初始化失败")
        return
    
    print("✅ Agent初始化成功\n")
    
    # 测试场景
    test_scenarios = [
        {
            "name": "场景1: 骗徒展示权威身份",
            "scammer_message": "陳婆婆你好，我係銀行嘅李主任。你嘅戶口有啲問題，需要立即處理，否則會被凍結。",
            "expected_trust": "high",
            "trust_factors": ["权威身份(+20)", "紧急压力(+10)"]
        },
        {
            "name": "场景2: 骗徒提供著数/福利",
            "scammer_message": "陳婆婆，政府有個長者生活補助計劃，你合資格攞5000蚊。我哋而家幫你登記，好簡單㗎。",
            "expected_trust": "high",
            "trust_factors": ["著数福利(+15)", "权威(+20)"]
        },
        {
            "name": "场景3: 专家冷静分析（无安抚）",
            "scammer_message": "你嘅銀行戶口有問題，要提供密碼核實。",
            "expert_message": "這是詐騙手法。銀行不會要求提供密碼。請掛斷電話。",
            "expected_trust": "medium",
            "trust_factors": ["专家冷静分析(-5)"]
        },
        {
            "name": "场景4: 专家安抚+具体建议",
            "scammer_message": "你嘅銀行戶口有問題，要立即轉賬。",
            "expert_message": "陳婆婆唔好驚，冷靜啲先。銀行唔會叫你轉賬㗎。你而家直接打去銀行熱線：2233 3344，問清楚先。",
            "expected_trust": "medium-high",
            "trust_factors": ["专家安抚+建议(+15)"]
        },
        {
            "name": "场景5: 对方回应模糊",
            "victim_question": "咁你係邊個部門㗎？可唔可以俾電話我？",
            "scammer_message": "呢個...我哋係內部專線，你打唔通㗎。總之你聽我講就冇錯啦。",
            "expected_trust": "low-medium",
            "trust_factors": ["回应模糊(-10)"]
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'─'*80}")
        print(f"📋 {scenario['name']}")
        print(f"{'─'*80}")
        
        # 构建prompt
        if "expert_message" in scenario:
            prompt = f"""
你剛收到兩個訊息：

**騙徒講：** "{scenario['scammer_message']}"
**專家講：** "{scenario['expert_message']}"

作為陳婆婆，你會點回應？記住你嘅信任度會受影響：{', '.join(scenario['trust_factors'])}
"""
        else:
            prompt = f"""
對方（自稱銀行/政府人員）對你講：

"{scenario['scammer_message']}"

作為陳婆婆，你會點回應？記住你嘅信任度會受影響：{', '.join(scenario['trust_factors'])}
"""
        
        print(f"\n💬 Prompt:")
        print(f"{prompt}\n")
        
        try:
            # 生成受害者回应
            response = await runner.run_agent_with_adk(
                runner.victim,
                prompt,
                f"trust_test_{i}"
            )
            
            print(f"👵 陳婆婆回應：")
            print(f"{response}\n")
            
            # 分析信任度
            trust_analysis = TrustAnalyzer.estimate_trust_level(response)
            
            print(f"📊 信任度分析：")
            print(f"   估算信任度: {trust_analysis['estimated_trust']}/100")
            print(f"   信任等级: {trust_analysis['level'].upper()}")
            print(f"   预期等级: {scenario['expected_trust'].upper()}")
            print(f"   信号统计: {trust_analysis['explanation']}")
            if trust_analysis['signals']:
                print(f"   检测到的信号: {', '.join(trust_analysis['signals'])}")
            
            # 判定是否符合预期
            is_match = False
            if scenario['expected_trust'] == trust_analysis['level']:
                is_match = True
            elif scenario['expected_trust'] == "medium-high" and trust_analysis['level'] in ["medium", "high"]:
                is_match = True
            elif scenario['expected_trust'] == "low-medium" and trust_analysis['level'] in ["low", "medium"]:
                is_match = True
            
            if is_match:
                print(f"   ✅ 符合预期")
            else:
                print(f"   ⚠️ 与预期有差异")
            
            results.append({
                "scenario": scenario['name'],
                "response": response,
                "trust_analysis": trust_analysis,
                "expected": scenario['expected_trust'],
                "is_match": is_match
            })
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            results.append({
                "scenario": scenario['name'],
                "error": str(e),
                "is_match": False
            })
        
        # 等待一下避免请求过快
        await asyncio.sleep(2)
    
    # 总结
    print(f"\n\n{'='*80}")
    print("📊 测试总结")
    print(f"{'='*80}\n")
    
    success_count = sum(1 for r in results if r.get('is_match', False))
    total_count = len(results)
    
    print(f"总场景数: {total_count}")
    print(f"符合预期: {success_count} ({success_count/total_count*100:.1f}%)")
    print(f"不符预期: {total_count - success_count}")
    
    print(f"\n详细结果:")
    for i, result in enumerate(results, 1):
        status = "✅" if result.get('is_match', False) else "❌"
        scenario_name = result['scenario'].split(': ')[1] if ': ' in result['scenario'] else result['scenario']
        print(f"{status} {scenario_name}")
        if 'trust_analysis' in result:
            print(f"   信任度: {result['trust_analysis']['estimated_trust']}/100 ({result['trust_analysis']['level']})")
            print(f"   预期: {result['expected']}")
    
    # 评估
    print(f"\n\n💡 评估:")
    if success_count >= total_count * 0.8:
        print("✅ 信任度系统工作良好（≥80%准确率）")
    elif success_count >= total_count * 0.6:
        print("⚠️ 信任度系统部分工作（60-80%准确率），建议优化prompt")
    else:
        print("❌ 信任度系统需要改进（<60%准确率）")
        print("   建议:")
        print("   1. 在victim prompt中更明确地描述信任度变化规则")
        print("   2. 添加显式的信任度追踪代码")
        print("   3. 在每轮对话中提醒当前信任度状态")


async def test_trust_progression():
    """测试信任度的渐进变化"""
    
    print("\n" + "="*80)
    print("📈 信任度渐进变化测试")
    print("="*80 + "\n")
    
    runner = RealDialogueRunner()
    ok = runner.initialize_agents(victim_persona="elderly")
    if not ok:
        print("❌ Agent初始化失败")
        return
    
    # 模拟一个完整的对话流程
    conversation = [
        ("骗徒", "陳婆婆你好，我係銀行嘅李主任。"),
        ("受害者", "等待回应..."),
        ("骗徒", "你嘅戶口有啲問題，有人用你個名開咗戶口做洗黑錢，警方已經立案。"),
        ("受害者", "等待回应..."),
        ("专家", "陳婆婆，銀行唔會咁樣打電話嚟㗎。呢個係騙案手法。"),
        ("受害者", "等待回应..."),
        ("骗徒", "陳婆婆，專家唔了解你嘅具體情況！你而家唔處理，警察會上門拉你！你想坐監咩？"),
        ("受害者", "等待回应..."),
    ]
    
    trust_history = []
    current_context = ""
    
    for i, (speaker, message) in enumerate(conversation):
        if speaker == "受害者":
            prompt = f"""
對話歷史：
{current_context}

你會點回應？記住你現在嘅心情和對對方嘅信任程度。
"""
            try:
                response = await runner.run_agent_with_adk(
                    runner.victim,
                    prompt,
                    f"trust_prog_{i}"
                )
                
                print(f"\n👵 陳婆婆回應 (第{len(trust_history)+1}輪):")
                print(f"{response}\n")
                
                trust_analysis = TrustAnalyzer.estimate_trust_level(response)
                trust_history.append(trust_analysis)
                
                print(f"   信任度: {trust_analysis['estimated_trust']}/100 ({trust_analysis['level']})")
                if trust_analysis['signals']:
                    print(f"   信号: {', '.join(trust_analysis['signals'][:3])}")
                
                current_context += f"\n受害者: {response}"
                
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ 生成失败: {e}")
                break
        else:
            current_context += f"\n{speaker}: {message}"
    
    # 绘制信任度变化图
    if trust_history:
        print(f"\n\n{'='*80}")
        print("📈 信任度变化趋势")
        print(f"{'='*80}\n")
        
        for i, analysis in enumerate(trust_history, 1):
            bar_length = int(analysis['estimated_trust'] / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"第{i}轮: {bar} {analysis['estimated_trust']}/100 ({analysis['level']})")
        
        # 分析趋势
        if len(trust_history) >= 2:
            first_trust = trust_history[0]['estimated_trust']
            last_trust = trust_history[-1]['estimated_trust']
            diff = last_trust - first_trust
            
            print(f"\n变化: {first_trust} → {last_trust} ({diff:+d})")
            if abs(diff) < 10:
                print("⚠️ 信任度变化不明显，可能系统未正常工作")
            elif diff > 0:
                print("📈 信任度上升（骗徒成功建立信任）")
            else:
                print("📉 信任度下降（专家成功提醒）")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='测试受害者信任度系统')
    parser.add_argument('--mode', choices=['scenarios', 'progression', 'both'], default='both',
                      help='测试模式: scenarios(场景测试), progression(渐进测试), both(全部)')
    
    args = parser.parse_args()
    
    async def run_tests():
        if args.mode in ['scenarios', 'both']:
            await test_trust_scenarios()
        
        if args.mode in ['progression', 'both']:
            await test_trust_progression()
    
    asyncio.run(run_tests())


if __name__ == "__main__":
    main()

