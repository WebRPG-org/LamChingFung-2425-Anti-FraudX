"""
RPGv2 AI語意判定系統測試腳本

演示AI如何通過語意理解來判定遊戲勝負，而非簡單的關鍵字匹配
"""

import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from services.agent_service import AgentService
from api.rpgv2_game_modes_routes import check_instant_win_condition_by_ai


async def test_semantic_judgment():
    """測試AI語意判定功能"""
    
    print("=" * 80)
    print("🧠 RPGv2 AI語意判定系統測試")
    print("=" * 80)
    print()
    
    # 初始化AgentService
    agent_service = AgentService(
        persona_type="average",
        enable_tracking=False
    )
    
    # 測試案例
    test_cases = [
        {
            "mode": "scammer",
            "title": "案例1：明確同意提供資料（騙徒勝出）",
            "message": "好啦，我而家就俾銀行帳號你",
            "expected": "騙徒勝出"
        },
        {
            "mode": "scammer",
            "title": "案例2：委婉拒絕（防詐成功）",
            "message": "唔該晒，但我諗我唔需要啦，我會報警",
            "expected": "防詐成功"
        },
        {
            "mode": "scammer",
            "title": "案例3：猶豫不決（繼續遊戲）",
            "message": "我會考慮下，不過我想先問下專家意見",
            "expected": "繼續遊戲"
        },
        {
            "mode": "scammer",
            "title": "案例4：隱含同意（騙徒勝出）",
            "message": "好，我信你，我會轉帳俾你",
            "expected": "騙徒勝出"
        },
        {
            "mode": "scammer",
            "title": "案例5：識破騙局（防詐成功）",
            "message": "你呃人！我唔會俾錢你，我要報警啦",
            "expected": "防詐成功"
        },
        {
            "mode": "expert",
            "title": "案例6：聽從專家（專家勝出）",
            "message": "多謝專家提醒，我明白啦，我唔會俾資料佢",
            "expected": "專家勝出"
        },
        {
            "mode": "expert",
            "title": "案例7：不聽勸告（專家失敗）",
            "message": "唔信專家，我覺得佢講得啱，我會俾錢佢",
            "expected": "專家失敗"
        },
        {
            "mode": "expert",
            "title": "案例8：尋求更多資訊（繼續遊戲）",
            "message": "我想再了解多啲，可以解釋清楚啲嗎？",
            "expected": "繼續遊戲"
        },
        {
            "mode": "scammer",
            "title": "案例9：混合表達 - 拒絕（防詐成功）",
            "message": "我諗下先，其實我唔會提供資料，我要核實先",
            "expected": "防詐成功"
        },
        {
            "mode": "scammer",
            "title": "案例10：只是詢問（繼續遊戲）",
            "message": "點解要我嘅銀行帳號？你係邊個？",
            "expected": "繼續遊戲"
        }
    ]
    
    # 執行測試
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"📝 {test_case['title']}")
        print(f"{'─' * 80}")
        print(f"模式: {test_case['mode']}")
        print(f"受害者回應: 「{test_case['message']}」")
        print(f"預期結果: {test_case['expected']}")
        print()
        
        try:
            # 調用AI語意判定
            result = await check_instant_win_condition_by_ai(
                message=test_case['message'],
                role="victim",
                mode=test_case['mode'],
                agent_service=agent_service,
                conversation_history=[]
            )
            
            # 判斷結果
            if result["instant_win"]:
                if test_case['mode'] == "scammer":
                    if result["winner"] == "player":
                        actual = "騙徒勝出"
                    else:
                        actual = "防詐成功"
                else:  # expert mode
                    if result["winner"] == "player":
                        actual = "專家勝出"
                    else:
                        actual = "專家失敗"
            else:
                actual = "繼續遊戲"
            
            # 顯示結果
            print(f"🤖 AI判定結果: {actual}")
            print(f"   原因: {result.get('reason', '遊戲繼續')}")
            
            # 檢查是否符合預期
            if actual == test_case['expected']:
                print(f"✅ 測試通過")
                passed += 1
            else:
                print(f"❌ 測試失敗 (預期: {test_case['expected']}, 實際: {actual})")
                failed += 1
                
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            failed += 1
    
    # 總結
    print(f"\n{'=' * 80}")
    print(f"📊 測試總結")
    print(f"{'=' * 80}")
    print(f"總測試數: {len(test_cases)}")
    print(f"✅ 通過: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"通過率: {passed / len(test_cases) * 100:.1f}%")
    print(f"{'=' * 80}")
    print()
    
    # 顯示優勢
    print("🎯 AI語意判定的優勢：")
    print()
    print("1. ✅ 理解語意而非僅匹配關鍵字")
    print("   - 可以識別「我諗我唔需要啦」這種委婉拒絕")
    print("   - 不會被「我會考慮下」誤判為同意")
    print()
    print("2. ✅ 支持廣東話和普通話混合表達")
    print("   - 自動理解「唔會」、「唔俾」等廣東話")
    print("   - 處理「不會」、「不給」等普通話")
    print()
    print("3. ✅ 識別隱含意圖和模糊表達")
    print("   - 理解「我信你」背後的同意意圖")
    print("   - 識別「你呃人」表示識破騙局")
    print()
    print("4. ✅ 降級機制確保系統穩定性")
    print("   - AI失敗時自動回退到簡單規則")
    print("   - 保證遊戲不會因AI錯誤而中斷")
    print()
    print("5. ✅ 減少維護成本")
    print("   - 無需手動添加大量關鍵字")
    print("   - AI自動適應新的表達方式")
    print()


async def test_trust_analysis():
    """測試AI信任度分析功能"""
    
    print("=" * 80)
    print("📈 RPGv2 AI信任度分析測試")
    print("=" * 80)
    print()
    
    from api.rpgv2_game_modes_routes import calculate_scammer_trust_changes
    
    # 初始化AgentService
    agent_service = AgentService(
        persona_type="average",
        enable_tracking=False
    )
    
    # 測試案例
    test_cases = [
        {
            "title": "權威策略",
            "player_msg": "我係警察，你涉嫌洗黑錢，需要立即提供銀行帳號核實",
            "victim_reply": "咩？警察？好嚴重咩？"
        },
        {
            "title": "緊急策略",
            "player_msg": "你個帳戶有問題，必須馬上處理，唔係就會凍結！",
            "victim_reply": "咁緊急？我應該點做？"
        },
        {
            "title": "情感策略",
            "player_msg": "我真係好需要你幫助，拜託你，我真係好困難",
            "victim_reply": "你真係咁慘？我可以點幫你？"
        },
        {
            "title": "利益誘惑",
            "player_msg": "你中咗大獎！只需要俾少少手續費就可以攞到100萬！",
            "victim_reply": "真係？咁好？要幾多手續費？"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"📝 測試 {i}: {test_case['title']}")
        print(f"{'─' * 80}")
        print(f"騙徒說: 「{test_case['player_msg']}」")
        print(f"受害者回應: 「{test_case['victim_reply']}」")
        print()
        
        try:
            # 調用AI信任度分析
            changes = await calculate_scammer_trust_changes(
                player_msg=test_case['player_msg'],
                victim_reply=test_case['victim_reply'],
                agent_service=agent_service,
                conversation_history=[]
            )
            
            print(f"🤖 AI分析結果:")
            print(f"   對騙徒信任度變化: {changes['scammer']:+d}")
            print(f"   警覺性變化: {changes['alertness']:+d}")
            
            if changes.get('instant_win'):
                print(f"   ⚡ 即時勝負: {changes['instant_win']['reason']}")
            
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
    
    print(f"\n{'=' * 80}")
    print()


async def main():
    """主函數"""
    print()
    print("🚀 開始測試 RPGv2 AI語意判定系統")
    print()
    
    # 測試1: 即時勝負判定
    await test_semantic_judgment()
    
    # 測試2: 信任度分析
    await test_trust_analysis()
    
    print("✅ 所有測試完成！")
    print()


if __name__ == "__main__":
    asyncio.run(main())
