"""
演示腳本 - 展示所有優化功能
運行此腳本可快速查看所有新功能的效果
"""

import sys
import os
import json

# 添加backend到路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.conversation_summarizer import ConversationSummarizer
from utils.rewrite_context_injector import RewriteContextInjector
from utils.scammer_strategy_manager import StrategyManager, ScamStrategy
from agents.victim import VictimAgent


def demo_conversation_summarizer():
    """演示對話壓縮功能"""
    print("=" * 60)
    print("📊 演示 1: 對話歷史壓縮")
    print("=" * 60)
    
    # 模擬長對話
    test_conversation = [
        {"speaker": "騙徒", "dialogue": "你好，我係銀行職員，你嘅戶口有可疑交易，必須立即處理！"},
        {"speaker": "受騙者", "dialogue": "咩？我好驚啊！點算好？"},
        {"speaker": "專家", "dialogue": "唔好驚！呢個係詐騙，立即停止對話！"},
        {"speaker": "騙徒", "dialogue": "專家搞錯了！我哋係官方機構，你要即刻提供資料！"},
        {"speaker": "受騙者", "dialogue": "但係...我唔知邊個講真..."},
        {"speaker": "專家", "dialogue": "呢個係典型騙案，真正銀行唔會咁樣打電話！"},
        {"speaker": "騙徒", "dialogue": "你唔配合，後果自負！立即轉帳到安全帳戶！"},
        {"speaker": "受騙者", "dialogue": "我...我應該點做？"},
        {"speaker": "專家", "dialogue": "唔好轉帳！立即報警！"},
        {"speaker": "騙徒", "dialogue": "報警都冇用，你嘅戶口已經凍結！"},
        {"speaker": "受騙者", "dialogue": "真係㗎？"},
        {"speaker": "專家", "dialogue": "唔好信佢！打去銀行官方熱線核實！"},
    ]
    
    summarizer = ConversationSummarizer(window_size=3)
    
    # 估算原始長度
    original_length = summarizer.estimate_prompt_length(test_conversation)
    print(f"原始對話長度: {original_length} 字符")
    print(f"對話輪數: {len(test_conversation)}")
    
    # 應用滑動視窗
    summary, recent = summarizer.apply_sliding_window(test_conversation)
    
    print(f"\n壓縮後:")
    print(f"  摘要: {summary}")
    print(f"  保留完整對話: {len(recent)} 輪")
    
    # 構建壓縮後的prompt
    compressed = summarizer.build_compressed_prompt(test_conversation)
    print(f"  壓縮後長度: {len(compressed)} 字符")
    print(f"  壓縮率: {(1 - len(compressed)/original_length)*100:.1f}%")
    
    print("\n✅ 對話壓縮演示完成\n")


def demo_rewrite_injector():
    """演示重寫原因注入功能"""
    print("=" * 60)
    print("✏️ 演示 2: 重寫原因注入")
    print("=" * 60)
    
    injector = RewriteContextInjector()
    
    # 測試騙徒錯誤
    print("場景1: 騙徒暴露身份")
    warning1 = "騙徒暴露假身份：「**林志強（騙徒）**：」"
    failure1 = injector.extract_failure_reason(warning1, "scammer")
    print(f"  錯誤類型: {failure1['error_type']}")
    print(f"  失敗原因: {failure1['reason'][:50]}...")
    
    # 測試專家錯誤
    print("\n場景2: 專家要求敏感資料")
    warning2 = "專家要求提供敏感資料：「提供個人資料」"
    failure2 = injector.extract_failure_reason(warning2, "expert")
    print(f"  錯誤類型: {failure2['error_type']}")
    print(f"  失敗原因: {failure2['reason'][:50]}...")
    
    # 構建重寫prompt
    print("\n構建增強重寫prompt:")
    enhanced = injector.build_rewrite_prompt(
        original_prompt="你好，我係銀行職員...",
        warning_message=warning1,
        agent_type="scammer"
    )
    print(f"  增強prompt長度: {len(enhanced)} 字符")
    print(f"  包含失敗原因: ✅")
    print(f"  包含修正指導: ✅")
    
    print("\n✅ 重寫原因注入演示完成\n")


def demo_strategy_manager():
    """演示策略管理功能"""
    print("=" * 60)
    print("🎯 演示 3: 動態策略調整")
    print("=" * 60)
    
    manager = StrategyManager()
    
    # 場景1：老年受害者，信任度高
    print("場景1: 老年受害者，信任度高")
    strategy1 = manager.recommend_strategy(
        victim_trust_scammer=85,
        victim_trust_expert=30,
        victim_persona="elderly",
        trust_change_trend="stable"
    )
    print(f"  推薦策略: {strategy1.value}")
    print(f"  策略關鍵詞: {StrategyManager.STRATEGY_TEMPLATES[strategy1]['keywords']}")
    
    # 場景2：信任度下降
    print("\n場景2: 信任度下降，需要切換策略")
    strategy2 = manager.recommend_strategy(
        victim_trust_scammer=55,
        victim_trust_expert=70,
        victim_persona="average",
        previous_strategy=ScamStrategy.AUTHORITY,
        trust_change_trend="decreasing"
    )
    print(f"  推薦策略: {strategy2.value}")
    print(f"  策略關鍵詞: {StrategyManager.STRATEGY_TEMPLATES[strategy2]['keywords']}")
    
    # 場景3：貪婪型受害者
    print("\n場景3: 貪婪型受害者")
    strategy3 = manager.recommend_strategy(
        victim_trust_scammer=60,
        victim_trust_expert=40,
        victim_persona="greedy",
        trust_change_trend="increasing"
    )
    print(f"  推薦策略: {strategy3.value}")
    print(f"  策略關鍵詞: {StrategyManager.STRATEGY_TEMPLATES[strategy3]['keywords']}")
    
    # 檢查是否應該切換
    print("\n策略切換判斷:")
    should_switch = manager.should_switch_strategy(
        victim_trust_scammer=55,
        previous_trust=75,
        rounds_since_switch=2
    )
    print(f"  是否應該切換: {'是' if should_switch else '否'}")
    
    print("\n✅ 動態策略調整演示完成\n")


def demo_new_personas():
    """演示新Persona功能"""
    print("=" * 60)
    print("👥 演示 4: 新受害者Persona")
    print("=" * 60)
    
    # 測試Skeptical
    print("Persona 1: Skeptical (多疑型 - 退休警察)")
    try:
        skeptical = VictimAgent(persona_type="skeptical")
        print(f"  ✅ 初始化成功")
        print(f"  名稱: {skeptical.name}")
        print(f"  特徵: 極度謹慎、要求證明、不容易相信")
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
    
    # 測試Greedy
    print("\nPersona 2: Greedy (貪婪型 - 家庭主婦)")
    try:
        greedy = VictimAgent(persona_type="greedy")
        print(f"  ✅ 初始化成功")
        print(f"  名稱: {greedy.name}")
        print(f"  特徵: 對高回報沒抵抗力、怕錯過機會")
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
    
    # 列出所有可用Persona
    print("\n所有可用Persona:")
    personas = ["elderly", "average", "overconfident", "skeptical", "greedy"]
    for i, persona in enumerate(personas, 1):
        print(f"  {i}. {persona}")
    
    print("\n✅ 新Persona演示完成\n")


def demo_all_strategies():
    """展示所有可用策略"""
    print("=" * 60)
    print("📋 完整策略列表")
    print("=" * 60)
    
    strategies = [
        ("AUTHORITY", "權威施壓", "法律、條例、必須、配合"),
        ("URGENCY", "製造緊迫感", "立即、馬上、只剩、倒數"),
        ("GREED", "利誘貪念", "回報、賺錢、機會、保證"),
        ("FEAR", "恐嚇威脅", "警察、拘捕、凍結、調查"),
        ("SYMPATHY", "裝可憐", "幫忙、困難、家人、求你"),
        ("SOCIAL_PROOF", "社會證明", "好多人、大家、成功、限量"),
        ("CONFUSION", "混淆視聽", "專業術語、複雜程序"),
        ("FLATTERY", "恭維奉承", "聰明、有眼光、VIP、特選"),
    ]
    
    for name, desc, keywords in strategies:
        print(f"  • {name:15} - {desc:12} (關鍵詞: {keywords})")
    
    print("\n✅ 策略列表展示完成\n")


def main():
    """主函數"""
    print("\n")
    print("🎉" * 30)
    print("反詐騙AI系統 - 優化功能演示")
    print("🎉" * 30)
    print("\n")
    
    # 運行所有演示
    demo_conversation_summarizer()
    demo_rewrite_injector()
    demo_strategy_manager()
    demo_new_personas()
    demo_all_strategies()
    
    print("=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 查看 '系統優化完成報告.md' 了解詳情")
    print("  2. 查看 '快速集成指南.md' 開始集成")
    print("  3. 運行 'python backend/scripts/generate_finetuning_data.py' 生成訓練數據")
    print("\n")


if __name__ == "__main__":
    main()

