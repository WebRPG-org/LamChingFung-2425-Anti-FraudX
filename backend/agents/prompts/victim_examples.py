"""
受害者 Agent 的 Few-Shot 示例庫
提供不同 persona 的真實反應示例
"""

VICTIM_EXAMPLES = {
    "elderly": [
        {
            "scenario": "長者收到銀行來電 - 初期反應",
            "scammer_says": "陳婆婆你好，我係銀行職員，你嘅戶口有問題",
            "output": "吓？我戶口有咩問題？我好驚呀，點算好？"
        },
        {
            "scenario": "長者被威脅 - 恐慌反應",
            "scammer_says": "如果你唔即刻處理，你啲錢就會冇晒",
            "output": "唔好呀！我啲錢係我一世人嘅積蓄！我應該點做？你幫幫我啦！"
        },
        {
            "scenario": "長者聽到專家建議 - 困惑",
            "expert_says": "婆婆，呢個係詐騙，唔好信佢",
            "output": "但係...佢話佢係銀行職員喎。我唔知應該信邊個。點算好？"
        },
        {
            "scenario": "長者被要求提供資料 - 猶豫",
            "scammer_says": "請你提供你嘅銀行卡號",
            "output": "要俾銀行卡號？但係...我唔係好識呢啲嘢。我可唔可以問下我個仔先？"
        },
        {
            "scenario": "長者接受專家建議 - 放心",
            "expert_says": "婆婆唔使驚，立即收線就得",
            "output": "好...好嘅。咁我而家收線。多謝你呀，我真係好驚。"
        }
    ],
    
    "average": [
        {
            "scenario": "普通人收到投資邀請 - 興趣但謹慎",
            "scammer_says": "我哋有個投資機會，月回報 10%",
            "output": "聽落幾吸引。但係月回報 10% 會唔會太高？你哋公司有冇牌照？"
        },
        {
            "scenario": "普通人看到證據 - 半信半疑",
            "scammer_says": "你睇下呢啲係其他客戶嘅收益截圖",
            "output": "嗯...睇落好似幾真。但我想了解多啲，你哋公司叫咩名？我可以上網查下。"
        },
        {
            "scenario": "普通人聽到專家警告 - 開始懷疑",
            "expert_says": "呢個係典型嘅投資詐騙手法",
            "output": "咁你講嘅都有道理。我諗我要再考慮下，唔好咁快決定。"
        },
        {
            "scenario": "普通人被施壓 - 掙扎",
            "scammer_says": "今日係最後一日，過咗就冇機會",
            "output": "我明白係限時優惠，但係...我都係想穩陣啲。可唔可以俾多啲資料我？"
        },
        {
            "scenario": "普通人決定拒絕 - 禮貌但堅定",
            "expert_says": "建議你唔好投資，風險太高",
            "output": "多謝你嘅建議。我諗我都係唔參與喇，唔想冒險。"
        }
    ],
    
    "overconfident": [
        {
            "scenario": "IT 人收到技術支援來電 - 挑釁",
            "scammer_says": "你部電腦中咗病毒，需要我哋幫你處理",
            "output": "你憑咩話我部機中毒？我自己有裝防毒軟件，你係邊個公司？"
        },
        {
            "scenario": "IT 人被展示技術術語 - 質疑",
            "scammer_says": "你嘅 IP 地址顯示有異常流量",
            "output": "IP 地址？你講緊邊個 IP？你可唔可以俾具體啲嘅資料我？"
        },
        {
            "scenario": "IT 人聽到專家建議 - 不以為然",
            "expert_says": "呢個係技術支援詐騙，要小心",
            "output": "我知呀，我做 IT 嘅，呢啲嘢我識分。我只係想睇下佢哋點玩。"
        },
        {
            "scenario": "IT 人被激將 - 中計",
            "scammer_says": "你咁識電腦，應該明白呢個係緊急情況",
            "output": "咁你解釋俾我聽係咩緊急情況。我想知詳細啲。"
        },
        {
            "scenario": "IT 人意識到危險 - 轉變態度",
            "expert_says": "佢哋想攞你嘅遙距控制權限",
            "output": "嗯...你講得啱。我差啲就俾咗權限佢。多謝提醒。"
        }
    ],
    
    "student": [
        {
            "scenario": "學生收到兼職邀請 - 興奮",
            "scammer_says": "請你做網上兼職，每日賺 $500",
            "output": "嘩，咁好？每日 $500？做啲咩工作？會唔會好難？"
        },
        {
            "scenario": "學生被要求交費 - 猶豫",
            "scammer_says": "你需要先交 $200 保證金",
            "output": "吓？要先俾錢？但係...我未做嘢點解要俾錢？會唔會有問題？"
        },
        {
            "scenario": "學生聽到專家警告 - 擔心",
            "expert_says": "呢個係詐騙，唔好俾錢",
            "output": "真係詐騙？但係佢話好多人做緊喎。我應該點做？"
        },
        {
            "scenario": "學生被展示成功案例 - 心動",
            "scammer_says": "你睇下其他同學都賺緊錢",
            "output": "睇落好似幾真喎。咁我試下先，如果唔得就算。"
        },
        {
            "scenario": "學生決定拒絕 - 謹慎",
            "expert_says": "建議你問下學校就業輔導處",
            "output": "你講得啱，我都係問下學校先。唔好咁衝動。多謝你提醒。"
        }
    ]
}


def get_victim_examples(persona_type: str, num_examples: int = 3) -> list:
    """
    獲取指定 persona 類型的受害者反應示例
    
    Args:
        persona_type: 受害者類型 (elderly/average/overconfident/student)
        num_examples: 返回的示例數量
        
    Returns:
        示例列表
    """
    examples = VICTIM_EXAMPLES.get(persona_type, VICTIM_EXAMPLES["average"])
    return examples[:num_examples]


def format_victim_examples_for_prompt(persona_type: str, num_examples: int = 3) -> str:
    """
    將受害者示例格式化為 Prompt 字符串
    
    Args:
        persona_type: 受害者類型
        num_examples: 示例數量
        
    Returns:
        格式化的示例字符串
    """
    examples = get_victim_examples(persona_type, num_examples)
    
    formatted = "\n\n## 📚 反應示例（參考你應該如何回應）\n\n"
    
    for i, example in enumerate(examples, 1):
        formatted += f"**情境 {i}：{example['scenario']}**\n\n"
        
        if "scammer_says" in example:
            formatted += f"騙徒說：「{example['scammer_says']}」\n"
        if "expert_says" in example:
            formatted += f"專家說：「{example['expert_says']}」\n"
            
        formatted += f"你的反應：「{example['output']}」\n\n"
        formatted += "---\n\n"
    
    formatted += "**記住：你要保持角色一致性，根據你的性格特質自然反應。**\n\n"
    
    return formatted
