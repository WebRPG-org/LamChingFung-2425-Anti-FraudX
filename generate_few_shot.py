"""
從 scraped_alerts.json 生成 Few-Shot 範例和完整知識庫
用於 Gemini 3 Flash Preview 的 System Instructions
"""

import json
import random
from typing import List, Dict

def load_alerts() -> List[Dict]:
    """載入所有詐騙案例"""
    with open('data/scraped_alerts.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def categorize_scam_type(title: str, content: str) -> str:
    """根據標題和內容判斷詐騙類型"""
    keywords = {
        "假冒官員": ["警務處", "入境處", "海關", "政府部門", "執法人員", "公安"],
        "假冒銀行": ["銀行", "信用卡", "帳戶", "網上理財", "提款卡"],
        "投資詐騙": ["投資", "股票", "虛擬貨幣", "加密貨幣", "理財", "高回報"],
        "網購詐騙": ["網購", "購物", "淘寶", "代購", "送貨"],
        "求職詐騙": ["招聘", "兼職", "工作", "求職"],
        "愛情詐騙": ["交友", "約會", "感情", "戀愛"],
        "釣魚詐騙": ["釣魚", "短訊", "連結", "SMS", "WhatsApp"],
        "電話詐騙": ["電話", "來電", "致電"],
    }
    
    text = title + " " + content
    for scam_type, words in keywords.items():
        if any(word in text for word in words):
            return scam_type
    return "其他詐騙"

def extract_key_tactics(content: str) -> List[str]:
    """提取詐騙手法特徵"""
    tactics = []
    
    # 常見手法關鍵詞
    tactic_patterns = {
        "製造恐慌": ["凍結", "封鎖", "涉案", "調查", "拘捕", "刑事"],
        "假冒權威": ["警務處", "政府", "銀行", "官方"],
        "時間壓力": ["立即", "馬上", "盡快", "限時", "今日內"],
        "要求轉帳": ["轉帳", "匯款", "過數", "入錢"],
        "索取資料": ["密碼", "驗證碼", "身份證", "信用卡", "個人資料"],
        "利誘": ["優惠", "回贈", "獎品", "中獎", "賺錢"],
        "假網站": ["網站", "連結", "網址", "登入"],
    }
    
    for tactic, keywords in tactic_patterns.items():
        if any(keyword in content for keyword in keywords):
            tactics.append(tactic)
    
    return tactics

def generate_dialogue_from_case(case: Dict) -> Dict:
    """從真實案例生成對話範例"""
    scam_type = categorize_scam_type(case['title'], case['content'])
    tactics = extract_key_tactics(case['content'])
    
    # 根據詐騙類型生成對話
    dialogues = {
        "假冒官員": {
            "scammer": "你好，我係香港警務處反詐騙組嘅警員，你嘅身份證涉及一宗洗黑錢案件，需要立即配合調查。",
            "victim_initial": "咩話？我冇做過呢啲嘢啊！",
            "scammer_pressure": "你嘅帳戶有可疑交易，如果唔立即處理，你嘅帳戶會被凍結，所有存款都會冇晒。你需要提供你嘅銀行帳戶資料俾我哋核實。",
            "victim_worried": "咁點算好？我真係好驚...",
            "expert_intervention": "等等！真正嘅警務人員唔會透過電話要求你提供銀行資料或密碼。呢個係典型嘅假冒官員詐騙。",
            "outcome": "SUCCESS"
        },
        "假冒銀行": {
            "scammer": "你好，我係XX銀行客戶服務部。你嘅網上理財帳戶出現異常登入，為咗保障你嘅資金安全，需要你提供驗證碼確認身份。",
            "victim_initial": "異常登入？我冇收到通知喎。",
            "scammer_pressure": "系統剛偵測到，如果唔立即處理，你嘅帳戶會被盜用。我哋會發送一個驗證碼到你手機，你收到後話俾我知。",
            "victim_worried": "好，我等陣收到話你知。",
            "expert_intervention": "小心！銀行職員絕對唔會要求你提供驗證碼。驗證碼係用嚟登入或轉帳，千祈唔好俾任何人。",
            "outcome": "SUCCESS"
        },
        "投資詐騙": {
            "scammer": "你好，我係XX投資公司嘅理財顧問。我哋有個獨家投資項目，保證每月回報10%，而家仲有優惠，首次投資可以免手續費。",
            "victim_initial": "聽落好吸引，但係咁高回報會唔會有風險？",
            "scammer_pressure": "我哋有專業團隊操作，而且有政府監管，絕對安全。好多客戶都賺咗好多錢，你睇下呢啲真實案例...",
            "victim_tempted": "咁我投資幾多先？",
            "expert_intervention": "小心！保證高回報嘅投資通常都係騙局。合法投資公司唔會保證回報，而且要喺證監會註冊。",
            "outcome": "SUCCESS"
        },
    }
    
    # 選擇對應的對話模板
    dialogue_template = dialogues.get(scam_type, dialogues["假冒官員"])
    
    return {
        "case_title": case['title'],
        "case_date": case['date'],
        "scam_type": scam_type,
        "tactics": tactics,
        "dialogue": dialogue_template,
        "real_case_summary": case['content'][:200] + "..."
    }

def generate_few_shot_examples(alerts: List[Dict], num_examples: int = 8) -> List[Dict]:
    """生成 Few-Shot 範例"""
    # 按詐騙類型分類
    categorized = {}
    for alert in alerts:
        scam_type = categorize_scam_type(alert['title'], alert['content'])
        if scam_type not in categorized:
            categorized[scam_type] = []
        categorized[scam_type].append(alert)
    
    # 從每個類型選擇案例
    examples = []
    for scam_type, cases in categorized.items():
        if len(examples) >= num_examples:
            break
        # 選擇內容最豐富的案例
        best_case = max(cases, key=lambda x: len(x['content']))
        examples.append(generate_dialogue_from_case(best_case))
    
    return examples[:num_examples]

def generate_knowledge_base(alerts: List[Dict]) -> Dict:
    """生成完整知識庫（用於長文本注入）"""
    knowledge = {
        "total_cases": len(alerts),
        "scam_types": {},
        "common_tactics": {},
        "warning_signs": [],
        "prevention_tips": []
    }
    
    # 統計詐騙類型
    for alert in alerts:
        scam_type = categorize_scam_type(alert['title'], alert['content'])
        if scam_type not in knowledge["scam_types"]:
            knowledge["scam_types"][scam_type] = {
                "count": 0,
                "cases": []
            }
        knowledge["scam_types"][scam_type]["count"] += 1
        knowledge["scam_types"][scam_type]["cases"].append({
            "title": alert['title'],
            "date": alert['date'],
            "summary": alert['content'][:150] + "..."
        })
    
    # 提取常見手法
    all_tactics = []
    for alert in alerts:
        tactics = extract_key_tactics(alert['content'])
        all_tactics.extend(tactics)
    
    from collections import Counter
    tactic_counts = Counter(all_tactics)
    knowledge["common_tactics"] = dict(tactic_counts.most_common(10))
    
    # 警告信號
    knowledge["warning_signs"] = [
        "來電顯示 +852 開頭（可能是改號電話）",
        "要求提供密碼、驗證碼或個人資料",
        "製造恐慌，聲稱帳戶被凍結或涉案",
        "要求立即轉帳或匯款",
        "保證高回報的投資機會",
        "提供可疑網站連結",
        "聲稱是政府部門或銀行職員",
        "使用時間壓力（「立即」、「今日內」）",
    ]
    
    # 防範建議
    knowledge["prevention_tips"] = [
        "接到可疑電話，立即掛線並致電官方熱線核實",
        "絕不透過電話或短訊提供密碼、驗證碼",
        "不要點擊可疑連結或下載不明應用程式",
        "投資前查證公司是否在證監會註冊",
        "遇到要求轉帳的情況，先與家人朋友商量",
        "使用雙重認證保護網上帳戶",
        "定期檢查銀行帳戶交易記錄",
    ]
    
    return knowledge

def format_for_system_instruction(examples: List[Dict], knowledge: Dict) -> str:
    """格式化為 System Instruction 格式"""
    output = "# 香港詐騙案例知識庫\n\n"
    output += f"## 統計資料\n"
    output += f"- 總案例數：{knowledge['total_cases']}\n"
    output += f"- 詐騙類型：{len(knowledge['scam_types'])} 種\n\n"
    
    output += "## 詐騙類型分布\n"
    for scam_type, data in knowledge['scam_types'].items():
        output += f"### {scam_type}（{data['count']} 案）\n"
        for case in data['cases'][:3]:  # 每種類型顯示 3 個案例
            output += f"- **{case['title']}**（{case['date']}）\n"
            output += f"  {case['summary']}\n\n"
    
    output += "## 常見詐騙手法\n"
    for tactic, count in knowledge['common_tactics'].items():
        output += f"- **{tactic}**：出現 {count} 次\n"
    
    output += "\n## 警告信號\n"
    for sign in knowledge['warning_signs']:
        output += f"- {sign}\n"
    
    output += "\n## 防範建議\n"
    for tip in knowledge['prevention_tips']:
        output += f"- {tip}\n"
    
    return output

def format_few_shot_examples(examples: List[Dict]) -> str:
    """格式化為 Few-Shot 範例"""
    output = "# Few-Shot 對話範例\n\n"
    output += "以下是真實詐騙案例改編的對話範例，請模仿這些對話的風格和結構：\n\n"
    
    for i, example in enumerate(examples, 1):
        output += f"## 範例 {i}：{example['scam_type']}\n"
        output += f"**真實案例**：{example['case_title']}（{example['case_date']}）\n"
        output += f"**詐騙手法**：{', '.join(example['tactics'])}\n\n"
        
        output += "**對話流程**：\n\n"
        dialogue = example['dialogue']
        output += f"**騙徒**：{dialogue['scammer']}\n\n"
        output += f"**受害者**：{dialogue['victim_initial']}\n\n"
        output += f"**騙徒**：{dialogue['scammer_pressure']}\n\n"
        output += f"**受害者**：{dialogue.get('victim_worried', dialogue.get('victim_tempted', ''))}\n\n"
        output += f"**專家**：{dialogue['expert_intervention']}\n\n"
        output += f"**結果**：{dialogue['outcome']}（專家成功阻止詐騙）\n\n"
        output += "---\n\n"
    
    return output

def main():
    print("正在載入詐騙案例...")
    alerts = load_alerts()
    print(f"已載入 {len(alerts)} 個案例")
    
    print("\n正在生成 Few-Shot 範例...")
    examples = generate_few_shot_examples(alerts, num_examples=8)
    print(f"已生成 {len(examples)} 個對話範例")
    
    print("\n正在生成知識庫...")
    knowledge = generate_knowledge_base(alerts)
    
    # 輸出 Few-Shot 範例
    few_shot_text = format_few_shot_examples(examples)
    with open('backend/agents/few_shot_examples.md', 'w', encoding='utf-8') as f:
        f.write(few_shot_text)
    print("[OK] Few-Shot examples saved to: backend/agents/few_shot_examples.md")
    
    # 輸出完整知識庫
    knowledge_text = format_for_system_instruction(examples, knowledge)
    with open('backend/agents/scam_knowledge_base.md', 'w', encoding='utf-8') as f:
        f.write(knowledge_text)
    print("[OK] Knowledge base saved to: backend/agents/scam_knowledge_base.md")
    
    # 輸出 JSON 格式（用於程式讀取）
    with open('backend/agents/few_shot_examples.json', 'w', encoding='utf-8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)
    print("[OK] JSON format saved to: backend/agents/few_shot_examples.json")
    
    with open('backend/agents/scam_knowledge_base.json', 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    print("[OK] JSON format saved to: backend/agents/scam_knowledge_base.json")
    
    print("\n[Statistics]")
    print(f"- Scam types: {len(knowledge['scam_types'])}")
    for scam_type, data in knowledge['scam_types'].items():
        print(f"  - {scam_type}: {data['count']} cases")
    print(f"- Common tactics: {len(knowledge['common_tactics'])}")
    print(f"- Warning signs: {len(knowledge['warning_signs'])}")
    print(f"- Prevention tips: {len(knowledge['prevention_tips'])}")
    
    print("\n[DONE] Ready for Gemini 3 System Instructions and Few-Shot Prompting!")

if __name__ == "__main__":
    main()
