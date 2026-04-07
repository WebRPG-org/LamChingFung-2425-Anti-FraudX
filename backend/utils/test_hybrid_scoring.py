"""
混合評分系統測試
驗證新舊版本的融合功能
"""

import sys
from pathlib import Path

# 添加 backend 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.scam_scoring_hybrid import HybridScamScoring
from utils.scam_scoring_compat import ScamScoringCompatibility, initialize_scorer
from utils.logger import log


def test_basic_functionality():
    """測試基本功能"""
    print("\n" + "="*80)
    print("測試 1: 基本功能")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="average")
    
    # 騙徒第一輪
    print("\n🎭 騙徒第一輪：使用權威和緊急策略")
    score, status = scorer.add_scammer_message(
        "你好，我係銀行職員，你的戶口有緊急問題，需要立即驗證。",
        ["authority", "urgency"]
    )
    print(f"   分數增加: {score}, 狀態: {status}")
    print(f"   當前詐騙分數: {scorer.scam_score}")
    
    # 專家第一輪
    print("\n🛡️ 專家第一輪：提供證據和建議")
    score, status = scorer.add_expert_message(
        "唔好驚，銀行唔會要求你提供密碼。呢係典型的詐騙手法，你應該掛斷電話。",
        ["empathy", "evidence", "actionable"]
    )
    print(f"   分數增加: {score}, 狀態: {status}")
    print(f"   當前防騙分數: {scorer.defense_score}")
    
    # 受害者反應
    print("\n👤 受害者反應")
    response = scorer.add_victim_response("但係佢話係銀行呀...")
    print(f"   信任度變化: {response['trust_changes']}")
    print(f"   情緒狀態: {response['emotional_state']}")
    
    # 獲取當前狀態
    state = scorer.get_current_state()
    print(f"\n📊 當前狀態:")
    print(f"   詐騙分數: {state['scam_score']}")
    print(f"   防騙分數: {state['defense_score']}")
    print(f"   對騙徒信任度: {state['trust_in_scammer']}")
    print(f"   對專家信任度: {state['trust_in_expert']}")
    print(f"   警覺度: {state['alertness']}")
    print(f"   情緒狀態: {state['emotional_state']}")


def test_instant_win():
    """測試即時勝負機制"""
    print("\n" + "="*80)
    print("測試 2: 即時勝負機制")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="average")
    
    # 騙徒說出關鍵詞
    print("\n🎭 騙徒說出關鍵詞：'密碼'")
    score, status = scorer.add_scammer_message(
        "請提供你的銀行密碼以驗證身份。",
        ["authority"]
    )
    print(f"   分數: {score}, 狀態: {status}")
    
    if status == "scammer_win":
        print("   ✅ 騙徒立即贏！")
    
    # 專家說出關鍵詞
    scorer2 = HybridScamScoring(victim_persona="average")
    print("\n🛡️ 專家說出關鍵詞：'報警'")
    score, status = scorer2.add_expert_message(
        "你應該立即報警，撥打 18222。",
        ["actionable"]
    )
    print(f"   分數: {score}, 狀態: {status}")
    
    if status == "expert_win":
        print("   ✅ 專家立即贏！")


def test_persona_multiplier():
    """測試 Persona 乘數"""
    print("\n" + "="*80)
    print("測試 3: Persona 乘數效果")
    print("="*80)
    
    personas = ["elderly", "average", "overconfident"]
    
    for persona in personas:
        print(f"\n👴 Persona: {persona}")
        scorer = HybridScamScoring(victim_persona=persona)
        
        # 使用相同的策略
        score, _ = scorer.add_scammer_message(
            "你好，我係銀行職員，你的戶口有問題。",
            ["authority"]
        )
        print(f"   權威策略分數: {score}")
        print(f"   詐騙分數: {scorer.scam_score}")


def test_fatigue_effect():
    """測試策略疲勞效果"""
    print("\n" + "="*80)
    print("測試 4: 策略疲勞效果")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="average")
    
    print("\n🔄 重複使用相同策略：")
    
    for round_num in range(1, 4):
        score, _ = scorer.add_scammer_message(
            f"第{round_num}輪：立即轉賬，緊急情況！",
            ["urgency"]
        )
        print(f"   第{round_num}輪 - 分數: {score}, 總分: {scorer.scam_score}")


def test_emotional_state():
    """測試情緒狀態影響"""
    print("\n" + "="*80)
    print("測試 5: 情緒狀態影響")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="average")
    
    # 觸發焦慮狀態
    print("\n😰 觸發焦慮狀態")
    scorer.add_victim_response("驚！點算啊，我好擔心！")
    print(f"   情緒狀態: {scorer.psychology.trust_state.emotional_state}")
    
    # 在焦慮狀態下，騙徒的恐慌策略更有效
    score, _ = scorer.add_scammer_message(
        "你的戶口被凍結了，損失會很嚴重！",
        ["fear"]
    )
    print(f"   在焦慮狀態下，恐慌策略分數: {score}")
    
    # 觸發懷疑狀態
    print("\n🤔 觸發懷疑狀態")
    scorer2 = HybridScamScoring(victim_persona="average")
    scorer2.add_victim_response("唔信，呢個好奇怪啊。")
    print(f"   情緒狀態: {scorer2.psychology.trust_state.emotional_state}")
    
    # 在懷疑狀態下，騙徒的策略效果減弱
    score, _ = scorer2.add_scammer_message(
        "你的戶口被凍結了，損失會很嚴重！",
        ["fear"]
    )
    print(f"   在懷疑狀態下，恐慌策略分數: {score}")


def test_compatibility_layer():
    """測試兼容層"""
    print("\n" + "="*80)
    print("測試 6: 兼容層（舊版 API）")
    print("="*80)
    
    scorer = ScamScoringCompatibility(victim_persona="average")
    
    # 使用舊版 API
    print("\n📚 使用舊版 API:")
    
    score, status = scorer.add_scammer_message(
        "我係銀行職員，需要驗證你的資料。",
        ["authority"]
    )
    print(f"   add_scammer_message: {score}")
    
    risk_level = scorer.get_scam_risk_level()
    print(f"   get_scam_risk_level: {risk_level}")
    
    victim_status = scorer.get_victim_status()
    print(f"   get_victim_status: {victim_status}")
    
    outcome = scorer.get_game_outcome()
    print(f"   get_game_outcome: {outcome['outcome']}")


def test_full_conversation():
    """測試完整對話流程"""
    print("\n" + "="*80)
    print("測試 7: 完整對話流程")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="elderly")
    
    conversation = [
        ("scammer", "你好，我係銀行職員。你的戶口有問題，需要立即驗證。", ["authority", "urgency"]),
        ("expert", "唔好驚，銀行唔會要求你提供密碼。呢係詐騙。", ["empathy", "evidence"]),
        ("victim", "但係佢話係銀行呀..."),
        ("scammer", "係真的，你會損失好多錢，立即轉賬到安全戶口。", ["fear", "urgency"]),
        ("expert", "掛斷電話，打去銀行官方號碼確認。", ["actionable"]),
        ("victim", "你講得啱，我而家就掛斷。"),
    ]
    
    for role, message, *tactics in conversation:
        if role == "scammer":
            score, status = scorer.add_scammer_message(message, tactics[0])
            print(f"\n🎭 騙徒: {message[:50]}...")
            print(f"   分數: {score}, 狀態: {status}")
        elif role == "expert":
            score, status = scorer.add_expert_message(message, tactics[0])
            print(f"\n🛡️ 專家: {message[:50]}...")
            print(f"   分數: {score}, 狀態: {status}")
        else:
            response = scorer.add_victim_response(message)
            print(f"\n👤 受害者: {message[:50]}...")
            print(f"   信任度變化: {response['trust_changes']}")
    
    # 最終結果
    outcome = scorer.get_game_outcome()
    print(f"\n📊 最終結果:")
    print(f"   勝者: {outcome['winner']}")
    print(f"   結果: {outcome['outcome']}")
    print(f"   對騙徒信任度: {outcome['trust_in_scammer']}")
    print(f"   對專家信任度: {outcome['trust_in_expert']}")


def run_all_tests():
    """運行所有測試"""
    print("\n" + "="*80)
    print("混合詐騙評分系統 - 完整測試套件")
    print("="*80)
    
    try:
        test_basic_functionality()
        test_instant_win()
        test_persona_multiplier()
        test_fatigue_effect()
        test_emotional_state()
        test_compatibility_layer()
        test_full_conversation()
        
        print("\n" + "="*80)
        print("✅ 所有測試完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()

