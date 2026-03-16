"""測試 AgentService"""
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.agent_service import AgentService
from utils.logger import log

async def test_scammer_agent():
    print("=" * 60)
    print("測試 ScammerAgent")
    print("=" * 60)
    
    # 創建 AgentService
    service = AgentService(persona_type="elderly", enable_tracking=True)
    
    # 測試生成響應
    result = await service.generate_response(
        agent_type="scammer",
        message="你好",
        conversation_history=[],
        check_consistency=False,
        track_performance=False
    )
    
    print(f"\n✅ 回應: {result['reply']}")
    print(f"回應長度: {len(result['reply'])}")
    
    if not result['reply']:
        print("\n❌ 回應為空！")
    else:
        print("\n✅ 測試成功！")

if __name__ == "__main__":
    asyncio.run(test_scammer_agent())
