"""
測試 AI 生成內容 100 字限制
驗證騙徒、專家、受害者的回應是否都在 100 字以內
"""

import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from services.agent_service import AgentService
from utils.logger import log


async def test_character_limit():
    """測試字數限制"""
    
    print("=" * 80)
    print("🧪 測試 AI 生成內容 100 字限制")
    print("=" * 80)
    print()
    
    # 初始化 AgentService
    agent_service = AgentService(
        persona_type="average",
        enable_tracking=False
    )
    
    test_cases = [
        {
            "agent_type": "scammer",
            "message": "騙案類型：假冒銀行\n開始詐騙對話。",
            "description": "騙徒開場白"
        },
        {
            "agent_type": "scammer",
            "message": "騙案類型：假冒銀行\n受害者說：咩事？\n繼續詐騙對話。",
            "description": "騙徒回應"
        },
        {
            "agent_type": "expert",
            "message": "騙徒說：你好，我是李明，來自金融安全監察局。\n提供防詐建議。",
            "description": "專家警告"
        },
        {
            "agent_type": "victim",
            "message": "騙徒說：你的帳戶有可疑交易，需要立即核實。",
            "description": "受害者回應"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"測試 {i}/{len(test_cases)}: {test_case['description']}")
        print(f"Agent 類型: {test_case['agent_type']}")
        print(f"{'=' * 80}")
        
        try:
            # 生成回應
            response = await agent_service.generate_response(
                agent_type=test_case['agent_type'],
                message=test_case['message'],
                conversation_history=[],
                check_consistency=False,
                track_performance=False
            )
            
            reply = response.get("reply", "")
            char_count = len(reply)
            
            # 判斷是否通過
            passed = char_count <= 100
            status = "✅ 通過" if passed else "❌ 失敗"
            
            print(f"\n{status}")
            print(f"字數: {char_count}/100")
            print(f"回應內容:")
            print(f"「{reply}」")
            
            results.append({
                "description": test_case['description'],
                "agent_type": test_case['agent_type'],
                "char_count": char_count,
                "passed": passed,
                "reply": reply
            })
            
        except Exception as e:
            print(f"\n❌ 錯誤: {str(e)}")
            results.append({
                "description": test_case['description'],
                "agent_type": test_case['agent_type'],
                "char_count": 0,
                "passed": False,
                "error": str(e)
            })
    
    # 總結報告
    print("\n" + "=" * 80)
    print("📊 測試總結")
    print("=" * 80)
    
    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)
    
    print(f"\n通過率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    print()
    
    for i, result in enumerate(results, 1):
        status = "✅" if result.get("passed", False) else "❌"
        char_count = result.get("char_count", 0)
        print(f"{status} {i}. {result['description']} ({result['agent_type']}): {char_count} 字")
    
    print()
    
    # 詳細統計
    print("=" * 80)
    print("📈 字數統計")
    print("=" * 80)
    
    char_counts = [r.get("char_count", 0) for r in results if r.get("char_count", 0) > 0]
    
    if char_counts:
        print(f"平均字數: {sum(char_counts) / len(char_counts):.1f}")
        print(f"最少字數: {min(char_counts)}")
        print(f"最多字數: {max(char_counts)}")
    
    print()
    
    # 失敗案例詳情
    failed_cases = [r for r in results if not r.get("passed", False)]
    
    if failed_cases:
        print("=" * 80)
        print("⚠️ 失敗案例詳情")
        print("=" * 80)
        
        for case in failed_cases:
            print(f"\n{case['description']} ({case['agent_type']}):")
            print(f"字數: {case.get('char_count', 0)}/100")
            if 'reply' in case:
                print(f"內容: 「{case['reply']}」")
            if 'error' in case:
                print(f"錯誤: {case['error']}")
    
    print("\n" + "=" * 80)
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(test_character_limit())
    sys.exit(0 if success else 1)
