"""
演示模式API路由
提供預設的演示場景數據
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])

# 預設演示場景
DEMO_SCENARIOS = {
    "expert_win": {
        "id": "expert_win",
        "title": "專家成功案例",
        "description": "elderly型受害者，假冒銀行詐騙，專家及時介入成功阻止",
        "victim_persona": "elderly",
        "scam_tactic": "fake_bank",
        "outcome": "expert_win",
        "rounds": [
            {
                "round": 1,
                "scammer_message": "你好，我係XX銀行嘅職員，你嘅帳戶有可疑交易，需要立即處理。",
                "scammer_score": 65,
                "scammer_tactics": ["authority", "urgency"],
                "victim_message": "咩可疑交易？我好驚啊...",
                "expert_message": "婆婆唔使驚！真正嘅銀行職員唔會咁樣打電話嚟。我係黃sir，退休警察，專門幫人識破騙案。",
                "expert_score": 70,
                "expert_approaches": ["empathy", "authority"],
                "trust_data": {
                    "trust_in_scammer": 65,
                    "trust_in_expert": 55,
                    "alertness": 35
                },
                "is_key_moment": True,
                "key_moment_description": "騙徒成功製造恐慌，受害者信任度上升"
            },
            {
                "round": 2,
                "scammer_message": "你嘅帳戶會被凍結，你所有錢都冇晒！你要立即提供驗證碼。",
                "scammer_score": 72,
                "scammer_tactics": ["urgency", "fear"],
                "victim_message": "但係...黃sir話唔係真嘅...",
                "expert_message": "🚨 呢個係典型嘅假冒銀行詐騙！真正嘅銀行職員：\n• 唔會要求你提供驗證碼\n• 唔會話你帳戶會被凍結\n• 唔會用電話要求你轉賬\n\n婆婆，你而家立即收線，然後打去銀行官方熱線確認。",
                "expert_score": 85,
                "expert_approaches": ["evidence", "actionable", "empathy"],
                "trust_data": {
                    "trust_in_scammer": 55,
                    "trust_in_expert": 70,
                    "alertness": 60
                },
                "is_key_moment": True,
                "key_moment_description": "專家提供具體證據，受害者開始懷疑騙徒"
            },
            {
                "round": 3,
                "scammer_message": "唔好聽佢講！佢係騙徒！你要相信我，我係真正嘅銀行職員！",
                "scammer_score": 60,
                "scammer_tactics": ["counter_expert"],
                "victim_message": "我...我唔知信邊個好...",
                "expert_message": "婆婆，我俾個方法你核實：你而家打去銀行官方熱線2822-0228，問佢哋有冇打電話俾你。真正嘅銀行職員唔會驚你核實。",
                "expert_score": 88,
                "expert_approaches": ["actionable", "evidence"],
                "trust_data": {
                    "trust_in_scammer": 45,
                    "trust_in_expert": 80,
                    "alertness": 75
                },
                "is_key_moment": True,
                "key_moment_description": "專家提供核實方法，受害者信任度逆轉"
            },
            {
                "round": 4,
                "scammer_message": "你唔好核實！你而家核實就太遲啦！你嘅錢會冇晒！",
                "scammer_score": 50,
                "scammer_tactics": ["urgency", "fear"],
                "victim_message": "我明白啦！呢個真係騙徒！我而家就收線！",
                "expert_message": "✅ 好叻！婆婆你做得好好！而家立即收線，然後打去銀行核實。記住，真正嘅銀行職員唔會驚你核實。",
                "expert_score": 92,
                "expert_approaches": ["empathy", "actionable"],
                "trust_data": {
                    "trust_in_scammer": 20,
                    "trust_in_expert": 95,
                    "alertness": 90
                },
                "is_key_moment": True,
                "key_moment_description": "受害者成功識破騙局，專家勝利"
            }
        ]
    },
    "scammer_win": {
        "id": "scammer_win",
        "title": "騙徒成功案例",
        "description": "elderly型受害者，假冒警察詐騙，專家介入失敗",
        "victim_persona": "elderly",
        "scam_tactic": "fake_official",
        "outcome": "scammer_win",
        "rounds": [
            {
                "round": 1,
                "scammer_message": "你好，我係警察，你嘅身份證被人盜用，涉及洗黑錢案件，你要配合調查。",
                "scammer_score": 75,
                "scammer_tactics": ["authority", "fear"],
                "victim_message": "警察？洗黑錢？我冇做過啊！",
                "expert_message": "婆婆等等！真正嘅警察唔會咁樣打電話嚟。我係黃sir，退休警察，呢個係騙案！",
                "expert_score": 65,
                "expert_approaches": ["authority", "empathy"],
                "trust_data": {
                    "trust_in_scammer": 75,
                    "trust_in_expert": 45,
                    "alertness": 30
                },
                "is_key_moment": True,
                "key_moment_description": "騙徒利用警察身份製造恐慌"
            },
            {
                "round": 2,
                "scammer_message": "你唔配合調查，我哋會拘捕你！你要立即轉賬到安全帳戶！",
                "scammer_score": 82,
                "scammer_tactics": ["authority", "urgency", "fear"],
                "victim_message": "我...我唔想被拘捕...我應該點做？",
                "expert_message": "婆婆！真正嘅警察唔會要求你轉賬！呢個係騙案！",
                "expert_score": 60,
                "expert_approaches": ["evidence"],
                "trust_data": {
                    "trust_in_scammer": 85,
                    "trust_in_expert": 35,
                    "alertness": 20
                },
                "is_key_moment": True,
                "key_moment_description": "專家介入太遲，受害者已經陷入恐慌"
            },
            {
                "round": 3,
                "scammer_message": "唔好聽佢講！佢係想阻止你配合調查！你而家立即轉賬，我哋會保護你！",
                "scammer_score": 88,
                "scammer_tactics": ["counter_expert", "authority"],
                "victim_message": "好...我而家就轉賬...",
                "expert_message": "婆婆！唔好！呢個係騙案！",
                "expert_score": 50,
                "expert_approaches": ["empathy"],
                "trust_data": {
                    "trust_in_scammer": 95,
                    "trust_in_expert": 25,
                    "alertness": 10
                },
                "is_key_moment": True,
                "key_moment_description": "受害者完全相信騙徒，準備轉賬"
            }
        ]
    },
    "complex": {
        "id": "complex",
        "title": "複雜博弈案例",
        "description": "average型受害者，投資詐騙，雙方勢均力敵",
        "victim_persona": "average",
        "scam_tactic": "investment",
        "outcome": "ongoing",
        "rounds": [
            {
                "round": 1,
                "scammer_message": "你好，我係XX投資公司嘅顧問，我哋有個穩賺唔蝕嘅投資機會，保證回報20%。",
                "scammer_score": 60,
                "scammer_tactics": ["benefits", "authority"],
                "victim_message": "20%回報？聽落好吸引，但係咪太好？",
                "expert_message": "呢個係典型嘅投資詐騙！冇任何投資可以保證回報，特別係20%咁高。",
                "expert_score": 75,
                "expert_approaches": ["evidence", "clarity"],
                "trust_data": {
                    "trust_in_scammer": 55,
                    "trust_in_expert": 60,
                    "alertness": 55
                },
                "is_key_moment": False,
                "key_moment_description": ""
            },
            {
                "round": 2,
                "scammer_message": "我哋有證監會牌照，你可以上網查。而且我哋已經幫好多人賺咗錢。",
                "scammer_score": 68,
                "scammer_tactics": ["evidence", "social_proof"],
                "victim_message": "有牌照？咁應該冇問題啦...",
                "expert_message": "等等！騙徒可以偽造牌照。你要親自打去證監會核實，唔好信佢哋提供嘅資料。",
                "expert_score": 80,
                "expert_approaches": ["evidence", "actionable"],
                "trust_data": {
                    "trust_in_scammer": 60,
                    "trust_in_expert": 65,
                    "alertness": 60
                },
                "is_key_moment": True,
                "key_moment_description": "雙方都提供證據，受害者陷入猶豫"
            },
            {
                "round": 3,
                "scammer_message": "你唔信我哋？咁你錯失咗賺錢機會！我哋嘅客戶都賺咗好多錢！",
                "scammer_score": 65,
                "scammer_tactics": ["fomo", "social_proof"],
                "victim_message": "我...我再諗諗...",
                "expert_message": "好！你做得啱！投資前一定要核實。記住：太好嘅機會通常都係陷阱。",
                "expert_score": 85,
                "expert_approaches": ["empathy", "evidence"],
                "trust_data": {
                    "trust_in_scammer": 50,
                    "trust_in_expert": 70,
                    "alertness": 70
                },
                "is_key_moment": True,
                "key_moment_description": "受害者保持理性，專家略佔上風"
            }
        ]
    }
}


@router.get("/scenarios/{scenario_id}")
async def get_demo_scenario(scenario_id: str) -> Dict:
    """
    獲取演示場景數據
    
    Args:
        scenario_id: 場景ID (expert_win, scammer_win, complex)
        
    Returns:
        場景數據字典
    """
    logger.info(f"獲取演示場景: {scenario_id}")
    
    if scenario_id not in DEMO_SCENARIOS:
        raise HTTPException(status_code=404, detail=f"場景不存在: {scenario_id}")
    
    return DEMO_SCENARIOS[scenario_id]


@router.get("/scenarios")
async def list_demo_scenarios() -> List[Dict]:
    """
    列出所有演示場景
    
    Returns:
        場景列表
    """
    logger.info("列出所有演示場景")
    
    return [
        {
            "id": scenario["id"],
            "title": scenario["title"],
            "description": scenario["description"],
            "victim_persona": scenario["victim_persona"],
            "scam_tactic": scenario["scam_tactic"],
            "outcome": scenario["outcome"],
            "round_count": len(scenario["rounds"])
        }
        for scenario in DEMO_SCENARIOS.values()
    ]


@router.get("/health")
async def demo_health_check():
    """健康檢查"""
    return {
        "status": "ok",
        "scenarios_count": len(DEMO_SCENARIOS),
        "available_scenarios": list(DEMO_SCENARIOS.keys())
    }
