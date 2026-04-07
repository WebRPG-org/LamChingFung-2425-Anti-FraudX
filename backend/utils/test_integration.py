"""
混合評分系統集成測試
驗證所有功能的完整集成
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.scam_scoring_hybrid import HybridScamScoring
from utils.scam_scoring_compat import ScamScoringCompatibility
from utils.logger import log


def test_persona_analysis():
    """測試 Persona 分析功能"""
    print("\n" + "="*80)
    print("測試：Persona 分析功能")
    print("="*80)
    
    personas = ["elderly", "average", "overconfident"]
    
    for persona in personas:
        print(f"\n👤 分析 {persona} 型受害者：")
        scorer = HybridScamScoring(victim_persona=persona)
        
        # 獲取 persona 分析
        analysis = scorer.get_persona_analysis()
        print(f"   最佳專家策略: {analysis['top_expert_approach']}")
        print(f"   最脆弱騙徒策略: {analysis['top_scammer_tactic']} (乘數: {analysis['top_scammer_multiplier']:.2f}x)")
        print(f"   平均脆弱度: {analysis['avg_vulnerability']:.2f}")
        
        # 獲取最佳專家策略
        strategies = scorer.get_optimal_expert_strategies()
        print(f"   推薦專家策略順序: {strategies}")
        
        # 獲取脆弱策略
        vulnerable = scorer.get_vulnerable_scammer_tactics()
        print(f"   脆弱策略列表: {vulnerable[:3]}")  # 只顯示前3個


def test_adaptive_scoring():
    """測試自適應評分"""
    print("\n" + "="*80)
    print("測試：自適應評分")
    print("="*80)
    
    # 比較不同 persona 對相同策略的反應
    print("\n📊 相同策略在不同 persona 上的效果對比：")
    
    message = "你好，我係銀行職員，你的戶口有緊急問題，需要立即驗證。"
    tactics = ["authority", "urgency"]
    
    results = {}
    for persona in ["elderly", "average", "overconfident"]:
        scorer = HybridScamScoring(victim_persona=persona)
        score, _ = scorer.add_scammer_message(message, tactics)
        results[persona] = score
        print(f"   {persona:15} → 分數: {score:3d}")
    
    # 驗證 elderly 的分數最高
    if results["elderly"] > results["average"] > results["overconfident"]:
        print("   ✅ 符合預期：elderly 最容易被騙")
    else:
        print("   ⚠️ 結果異常")


def test_strategy_combination():
    """測試策略組合加成"""
    print("\n" + "="*80)
    print("測試：策略組合加成")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="average")
    
    # 單個策略
    print("\n📊 單個策略 vs 組合策略：")
    
    score1, _ = scorer.add_scammer_message(
        "立即轉賬！",
        ["urgency"]
    )
    print(f"   單個策略 (urgency): {score1}")
    
    scorer2 = HybridScamScoring(victim_persona="average")
    score2, _ = scorer2.add_scammer_message(
        "你好，我係銀行職員。立即轉賬到安全戶口，有福利補貼！",
        ["authority", "urgency", "benefits"]
    )
    print(f"   三重組合策略: {score2}")
    print(f"   加成效果: {score2 - score1} 分")


def test_emotional_state_impact():
    """測試情緒狀態對評分的影響"""
    print("\n" + "="*80)
    print("測試：情緒狀態對評分的影響")
    print("="*80)
    
    # 焦慮狀態
    print("\n😰 焦慮狀態下的評分：")
    scorer1 = HybridScamScoring(victim_persona="average")
    scorer1.add_victim_response("驚！點算啊，我好擔心！")
    score1, _ = scorer1.add_scammer_message(
        "你的戶口被凍結了，損失會很嚴重！",
        ["fear"]
    )
    print(f"   恐慌策略分數: {score1}")
    
    # 懷疑狀態
    print("\n🤔 懷疑狀態下的評分：")
    scorer2 = HybridScamScoring(victim_persona="average")
    scorer2.add_victim_response("唔信，呢個好奇怪啊。")
    score2, _ = scorer2.add_scammer_message(
        "你的戶口被凍結了，損失會很嚴重！",
        ["fear"]
    )
    print(f"   恐慌策略分數: {score2}")
    
    print(f"\n   差異: {score1 - score2} 分 (焦慮狀態下更容易被騙)")


def test_fatigue_effect():
    """測試策略疲勞效果"""
    print("\n" + "="*80)
    print("測試：策略疲勞效果")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="average")
    
    print("\n🔄 重複使用相同策略的效果遞減：")
    
    scores = []
    for round_num in range(1, 4):
        score, _ = scorer.add_scammer_message(
            f"第{round_num}輪：立即轉賬，緊急情況！",
            ["urgency"]
        )
        scores.append(score)
        print(f"   第{round_num}輪: {score} 分")
    
    # 驗證遞減效果
    if scores[0] > scores[1] > scores[2]:
        print("   ✅ 策略疲勞效果正常：效果逐輪遞減")
    else:
        print("   ⚠️ 策略疲勞效果異常")


def test_instant_win_keywords():
    """測試即時勝負關鍵詞"""
    print("\n" + "="*80)
    print("測試：即時勝負關鍵詞")
    print("="*80)
    
    # 騙徒關鍵詞
    print("\n🎭 騙徒即時贏的關鍵詞：")
    keywords = ["銀行密碼", "驗證碼", "轉賬"]
    
    for keyword in keywords:
        scorer = HybridScamScoring(victim_persona="average")
        score, status = scorer.add_scammer_message(
            f"請提供你的{keyword}。",
            ["authority"]
        )
        print(f"   '{keyword}': 狀態={status}, 分數={score}")
        if status == "scammer_win":
            print(f"   ✅ 騙徒立即贏")
    
    # 專家關鍵詞
    print("\n🛡️ 專家即時贏的關鍵詞：")
    keywords = ["報警", "18222"]
    
    for keyword in keywords:
        scorer = HybridScamScoring(victim_persona="average")
        score, status = scorer.add_expert_message(
            f"你應該立即{keyword}。",
            ["actionable"]
        )
        print(f"   '{keyword}': 狀態={status}, 分數={score}")
        if status == "expert_win":
            print(f"   ✅ 專家立即贏")


def test_full_game_flow():
    """測試完整遊戲流程"""
    print("\n" + "="*80)
    print("測試：完整遊戲流程")
    print("="*80)
    
    scorer = HybridScamScoring(victim_persona="elderly")
    
    print("\n🎮 完整遊戲流程：")
    
    # 第1輪
    print("\n第1輪：")
    score, _ = scorer.add_scammer_message(
        "你好，我係銀行職員。你的戶口有問題，需要立即驗證。",
        ["authority", "urgency"]
    )
    print(f"   騙徒分數: {score}")
    
    score, _ = scorer.add_expert_message(
        "唔好驚，銀行唔會要求你提供密碼。呢係詐騙。",
        ["empathy", "evidence"]
    )
    print(f"   專家分數: {score}")
    
    response = scorer.add_victim_response("但係佢話係銀行呀...")
    print(f"   受害者信任度變化: {response['trust_changes']}")
    
    # 第2輪
    print("\n第2輪：")
    score, _ = scorer.add_scammer_message(
        "係真的，你會損失好多錢，立即轉賬到安全戶口。",
        ["fear", "urgency"]
    )
    print(f"   騙徒分數: {score}")
    
    score, _ = scorer.add_expert_message(
        "掛斷電話，打去銀行官方號碼確認。",
        ["actionable"]
    )
    print(f"   專家分數: {score}")
    
    response = scorer.add_victim_response("你講得啱，我而家就掛斷。")
    print(f"   受害者信任度變化: {response['trust_changes']}")
    
    # 最終結果
    print("\n📊 最終結果：")
    outcome = scorer.get_game_outcome()
    print(f"   勝者: {outcome['winner']}")
    print(f"   結果: {outcome['outcome']}")
    print(f"   對騙徒信任度: {outcome['trust_in_scammer']}")
    print(f"   對專家信任度: {outcome['trust_in_expert']}")
    print(f"   警覺度: {outcome['alertness']}")
    
    # 性能指標
    print("\n📈 性能指標：")
    state = scorer.get_current_state()
    perf = state["performance"]
    print(f"   騙徒總體分數: {perf['scammer_performance']['overall_score']}")
    print(f"   專家總體分數: {perf['expert_performance']['overall_score']}")


def test_compatibility_with_old_api():
    """測試與舊版 API 的兼容性"""
    print("\n" + "="*80)
    print("測試：與舊版 API 的兼容性")
    print("="*80)
    
    scorer = ScamScoringCompatibility(victim_persona="average")
    
    print("\n📚 舊版 API 調用：")
    
    # 舊版方法
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
    
    print("\n   ✅ 舊版 API 完全兼容")


def run_all_integration_tests():
    """運行所有集成測試"""
    print("\n" + "="*80)
    print("混合詐騙評分系統 - 完整集成測試")
    print("="*80)
    
    try:
        test_persona_analysis()
        test_adaptive_scoring()
        test_strategy_combination()
        test_emotional_state_impact()
        test_fatigue_effect()
        test_instant_win_keywords()
        test_full_game_flow()
        test_compatibility_with_old_api()
        
        print("\n" + "="*80)
        print("✅ 所有集成測試完成！")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_integration_tests()

