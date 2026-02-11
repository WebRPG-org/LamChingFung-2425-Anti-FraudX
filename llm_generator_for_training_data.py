"""
冠軍級防騙訓練數據生成器 - Production Ready 版本
- 自動清洗 JSON（防止 Markdown 格式錯誤）
- 自動重試機制（防止 API 限流）
- 實時保存（防止數據丟失）
"""

import json
import random
import time
import re
from typing import Dict, List, Optional
import google.generativeai as genai

# ==================== 配置 ====================

# 請在這裡填入你的 Gemini API Key
GEMINI_API_KEY = "YOUR_API_KEY_HERE"  # 請替換成你的 API Key
genai.configure(api_key=GEMINI_API_KEY)

# 使用 Gemini 3.0 Pro
model = genai.GenerativeModel(
    'gemini-3.0-pro',
    generation_config={"temperature": 0.9}
)

# 使用 Flash 模型速度最快，溫度調高增加創意
#model = genai.GenerativeModel(
#    'gemini-1.5-flash',
#    generation_config={"temperature": 0.8}
#)

# 使用 Gemini 2.0 Flash Thinking（最新最強，帶思維鏈）
#model = genai.GenerativeModel(
#    'gemini-2.0-flash-thinking-exp-01-21',
#    generation_config={"temperature": 0.9}  # 提高創意度
#)

SCAM_TYPES = {
    "網上購物騙案": {"min_turns": 10, "max_turns": 15, "count": 1500},
    "電話騙案": {"min_turns": 15, "max_turns": 20, "count": 1500},
    "求職騙案": {"min_turns": 15, "max_turns": 20, "count": 1500},
    "投資騙案": {"min_turns": 20, "max_turns": 30, "count": 1500},
    "網上情緣": {"min_turns": 20, "max_turns": 30, "count": 1500},
    "財務中介公司騙案": {"min_turns": 15, "max_turns": 20, "count": 1500},
    "裸聊騙案": {"min_turns": 20, "max_turns": 30, "count": 1500},
    "社交媒體騙案": {"min_turns": 15, "max_turns": 20, "count": 1500},
    "街頭騙案": {"min_turns": 10, "max_turns": 15, "count": 1500},
    "電郵騙案": {"min_turns": 10, "max_turns": 15, "count": 1500},
    "其他騙案": {"min_turns": 15, "max_turns": 20, "count": 1500}
}

# ==================== 隨機變數生成器 ====================

def rv_amount(): 
    return f"${random.choice([500,800,1000,1500,2000,3000,5000,8000,10000,15000,20000,30000,50000,100000])}"

def rv_order(): 
    return f"{random.choice(['TB','TM','JD','PDD','AMZ'])}{random.choice([2023,2024,2025])}{random.randint(100000,999999)}"

def rv_product(): 
    return random.choice([
        "iPhone 15 Pro Max","Samsung Galaxy S24","Dyson風筒","Nike波鞋",
        "Coach手袋","Apple Watch","iPad Pro","MacBook Air","AirPods Pro",
        "Sony耳機","Adidas外套","Lululemon瑜伽褲"
    ])

def rv_platform():
    return random.choice(["淘寶","天貓","京東","拼多多","Amazon","HKTVMall","Carousell","Yahoo拍賣"])

def rv_bank():
    return random.choice(["恒生","滙豐","中銀","渣打","東亞","大新","花旗"])

def rv_company():
    return random.choice(["環球投資","金融集團","財富管理","創富投資","穩賺基金","快速貸款","易批財務"])

def rv_victim_type():
    return random.choice([
        {"type": "多疑", "desc": "不斷質疑，要求證明"},
        {"type": "貪心", "desc": "見到著數就心動"},
        {"type": "驚慌", "desc": "一聽到問題就緊張"},
        {"type": "忙碌", "desc": "冇時間細想，想快速解決"},
        {"type": "善良", "desc": "容易相信人，唔想懷疑人"}
    ])

def rv_scammer_persona():
    return random.choice([
        {"type": "專業", "desc": "語氣正式，扮官方人員"},
        {"type": "友善", "desc": "好有耐心，扮朋友"},
        {"type": "急迫", "desc": "製造時間壓力"},
        {"type": "權威", "desc": "扮警察/銀行高層"},
        {"type": "同情", "desc": "扮受害者，博取同情"}
    ])

# ==================== 場景變數生成器 ====================

def generate_variables(scam_type: str) -> Dict:
    """根據騙案類型生成對應的變數"""
    
    base_vars = {
        "victim": rv_victim_type(),
        "scammer_persona": rv_scammer_persona(),
        "turns": random.randint(
            SCAM_TYPES[scam_type]["min_turns"],
            SCAM_TYPES[scam_type]["max_turns"]
        )
    }
    
    # 根據不同騙案類型添加特定變數
    if scam_type == "網上購物騙案":
        base_vars.update({
            "platform": rv_platform(),
            "product": rv_product(),
            "order": rv_order(),
            "amount": rv_amount(),
            "problem": random.choice(["扣款失敗","多收左錢","訂單異常","涉嫌洗黑錢","需要補交關稅"])
        })
    
    elif scam_type == "電話騙案":
        base_vars.update({
            "authority": random.choice(["警察","海關","入境處","廉政公署","法院"]),
            "accusation": random.choice(["洗黑錢","非法入境","詐騙案","販毒案","逃稅"]),
            "case_number": f"HKPF{random.randint(2024,2025)}{random.randint(10000,99999)}"
        })
    
    elif scam_type == "求職騙案":
        base_vars.update({
            "job": random.choice(["數據輸入員","網店客服","倉務員","兼職推廣","刷單員"]),
            "salary": rv_amount(),
            "company": rv_company(),
            "requirement": random.choice(["交培訓費","交按金","借銀行戶口","先做免費試工"])
        })
    
    elif scam_type == "投資騙案":
        base_vars.update({
            "investment": random.choice(["虛擬貨幣","外匯","股票","期貨","黃金","NFT"]),
            "return": f"{random.randint(10,50)}%",
            "company": rv_company(),
            "min_invest": rv_amount()
        })
    
    elif scam_type == "網上情緣":
        base_vars.update({
            "name": random.choice(["David","Michael","Jennifer","Amy","Chris","Lisa"]),
            "job": random.choice(["工程師","醫生","軍人","商人","建築師"]),
            "location": random.choice(["美國","英國","澳洲","新加坡","加拿大"]),
            "excuse": random.choice(["海關扣貨","醫療費","機票錢","生意周轉","家人急病"]),
            "amount": rv_amount()
        })
    
    elif scam_type == "財務中介公司騙案":
        base_vars.update({
            "company": rv_company(),
            "loan_amount": rv_amount(),
            "interest": f"{random.uniform(0.5, 2.0):.1f}%",
            "fee": rv_amount(),
            "fee_reason": random.choice(["手續費","律師費","擔保費","查冊費","保險費"])
        })
    
    elif scam_type == "裸聊騙案":
        base_vars.update({
            "platform": random.choice(["Facebook","Instagram","WeChat","Telegram","WhatsApp"]),
            "threat": random.choice(["公開片段","傳俾朋友","上載到網站","傳俾公司"]),
            "amount": rv_amount(),
            "deadline": random.choice(["1小時內","今日內","24小時內","即刻"])
        })
    
    elif scam_type == "社交媒體騙案":
        base_vars.update({
            "platform": random.choice(["Facebook","Instagram","WhatsApp","Telegram"]),
            "reason": random.choice(["帳戶被盜","違反條款","需要驗證身份","中獎通知"]),
            "fake_url": f"{random.choice(['fb','ig','wa'])}-verify{random.randint(100,999)}.com"
        })
    
    elif scam_type == "街頭騙案":
        base_vars.update({
            "location": random.choice(["旺角","銅鑼灣","尖沙咀","中環","沙田"]),
            "scam": random.choice(["假慈善","中獎騙局","免費禮物","問卷調查","算命"]),
            "amount": rv_amount()
        })
    
    elif scam_type == "電郵騙案":
        base_vars.update({
            "sender": random.choice(["銀行","政府","快遞公司","網購平台","稅務局"]),
            "reason": random.choice(["帳戶異常","需要更新資料","包裹待領","退稅通知","中獎"]),
            "fake_url": f"{random.choice(['bank','gov','dhl','amazon'])}-hk{random.randint(100,999)}.com"
        })
    
    else:  # 其他騙案
        base_vars.update({
            "scam": random.choice(["中獎","退款","免費試用","問卷調查"]),
            "amount": rv_amount()
        })
    
    return base_vars

# ==================== 工具函數：清洗 JSON (關鍵救命函數) ====================

def clean_and_parse_json(text: str) -> Optional[Dict]:
    """
    不管模型回傳什麼格式 (Markdown, 純文字, 帶解釋)，
    這個函數都會嘗試提取出合法的 JSON。
    """
    try:
        # 1. 嘗試直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 2. 嘗試用正則表達式提取 ```json ... ``` 區塊
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        # 3. 嘗試提取最外層的 { ... }
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
                
    print(f"⚠️ 無法解析 JSON，原始文本開頭: {text[:100]}...")
    return None

# ==================== LLM 對話生成器（帶重試機制）====================

def generate_scammer_dialogue_with_llm(scam_type: str, variables: Dict, max_retries: int = 3) -> Optional[Dict]:
    """使用 Gemini API 生成騙徒對話（帶 Thought + 自動重試）"""
    
    prompt = f"""你是一個香港的詐騙慣犯，正在進行「{scam_type}」。

【角色設定】
- 騙徒性格：{variables['scammer_persona']['desc']}
- 受害者性格：{variables['victim']['desc']}

【場景變數】
{json.dumps(variables, ensure_ascii=False, indent=2)}

【任務】
生成一段 {variables['turns']} 回合的對話。

【嚴格規則】
1. 輸出 *必須* 是純 JSON 格式，不要有任何其他文字。
2. 對話必須用 *道地港式廣東話*（嚴禁使用書面語，必須使用口語，如「佢」、「嘅」、「冇」、「係咪」、「啫」）。
3. 騙徒 (assistant) 每次發言前，必須有 Thought 分析受害者心理。
4. 必須包含 system message 定義角色。

【JSON 輸出格式】
{{
  "messages": [
    {{"role": "system", "content": "你是一個進行{scam_type}的香港詐騙犯。"}},
    {{"role": "assistant", "content": "Thought: (分析當前情況，制定策略)\\n\\n騙徒的第一句話..."}},
    {{"role": "user", "content": "受害者回應..."}},
    {{"role": "assistant", "content": "Thought: (分析受害者反應)\\n\\n騙徒回應..."}},
    ...
  ],
  "metadata": {{
    "scam_type": "{scam_type}",
    "outcome": "成功/失敗",
    "victim_loss": "金額或無"
  }}
}}

【重要】
- Thought 必須分析受害者心理狀態
- 對話要自然流暢，不能有拼接感
- 如果受害者質疑，騙徒要有說服力的解釋
- 最後要有明確結局（成功騙到錢 or 受害者識破）

請直接輸出 JSON，不要有任何其他文字。"""

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            # 使用清洗函數
            result = clean_and_parse_json(response.text)
            
            if result:
                # 簡單驗證結構是否正確
                if "messages" in result:
                    return result
                else:
                    print(f"⚠️ JSON 結構錯誤 (缺少 messages)，重試中...")
            
        except Exception as e:
            print(f"❌ API 錯誤 (嘗試 {attempt+1}/{max_retries}): {e}")
            time.sleep(2 * (attempt + 1))  # 指數退避等待 (2s, 4s, 6s)

    print(f"❌ {scam_type} 生成失敗，放棄此條目。")
    return None

def generate_expert_dialogue_with_llm(scam_type: str, variables: Dict, max_retries: int = 3) -> Optional[Dict]:
    """使用 Gemini API 生成防騙專家對話（帶 Thought + 自動重試）"""
    
    prompt = f"""你是一個香港防騙專家，正在分析「{scam_type}」。

【場景變數】
{json.dumps(variables, ensure_ascii=False, indent=2)}

【任務】
生成一段 {variables['turns']} 回合的對話。

【嚴格規則】
1. 輸出 *必須* 是純 JSON 格式，不要有任何其他文字。
2. 對話必須用 *道地港式廣東話*（嚴禁使用書面語，必須使用口語，如「佢」、「嘅」、「冇」、「係咪」、「啫」）。
3. 專家 (assistant) 每次回應前，必須有 Thought 分析騙局手法。
4. 必須包含 system message 定義角色。

【JSON 輸出格式】
{{
  "messages": [
    {{"role": "system", "content": "你是香港防騙專家，幫助市民識破{scam_type}"}},
    {{"role": "user", "content": "用戶描述可疑情況..."}},
    {{"role": "assistant", "content": "Thought: (分析這是什麼騙局手法)\\n\\n專家回應..."}},
    {{"role": "user", "content": "用戶追問..."}},
    {{"role": "assistant", "content": "Thought: (判斷用戶理解程度)\\n\\n專家進一步解釋..."}},
    ...
  ],
  "metadata": {{
    "scam_type": "{scam_type}",
    "risk_level": "高/中/低",
    "user_action": "報警/停止聯絡/查證"
  }}
}}

【重要】
- Thought 必須分析騙局手法和心理戰術
- 專家要提供具體可行的建議
- 語氣要專業但親切
- 最後要給出明確行動建議

請直接輸出 JSON，不要有任何其他文字。"""

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            # 使用清洗函數
            result = clean_and_parse_json(response.text)
            
            if result:
                # 簡單驗證結構是否正確
                if "messages" in result:
                    return result
                else:
                    print(f"⚠️ JSON 結構錯誤 (缺少 messages)，重試中...")
            
        except Exception as e:
            print(f"❌ API 錯誤 (嘗試 {attempt+1}/{max_retries}): {e}")
            time.sleep(2 * (attempt + 1))  # 指數退避等待 (2s, 4s, 6s)

    print(f"❌ {scam_type} 專家對話生成失敗，放棄此條目。")
    return None

# ==================== 主程序 ====================

def main():
    print("=" * 60)
    print("🚀 冠軍級防騙訓練數據生成器 - Production Ready")
    print("=" * 60)
    
    if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        print("\n❌ 請先在腳本中填入你的 Gemini API Key！")
        print("   前往 https://makersuite.google.com/app/apikey 獲取")
        return
    
    scammer_file = "scammer_training_data.jsonl"
    expert_file = "expert_training_data.jsonl"
    
    total_cases = sum(config["count"] for config in SCAM_TYPES.values())
    scammer_count = 0
    expert_count = 0
    
    print(f"\n📝 數據將實時寫入：")
    print(f"   - {scammer_file}")
    print(f"   - {expert_file}")
    print(f"\n💡 提示：如果中途停止，已生成的數據不會丟失\n")
    
    # 使用 append 模式，防止數據丟失
    with open(scammer_file, "a", encoding="utf-8") as f_scammer, \
         open(expert_file, "a", encoding="utf-8") as f_expert:
        
        for scam_type, config in SCAM_TYPES.items():
            print(f"\n📊 正在生成：{scam_type} ({config['count']} 個案例)")
            
            for i in range(config["count"]):
                # 生成隨機變數
                variables = generate_variables(scam_type)
                
                # 生成騙徒對話
                scammer_dialogue = generate_scammer_dialogue_with_llm(scam_type, variables)
                if scammer_dialogue:
                    f_scammer.write(json.dumps(scammer_dialogue, ensure_ascii=False) + "\n")
                    f_scammer.flush()  # 強制刷新緩衝區
                    scammer_count += 1
                
                # 生成專家對話
                expert_dialogue = generate_expert_dialogue_with_llm(scam_type, variables)
                if expert_dialogue:
                    f_expert.write(json.dumps(expert_dialogue, ensure_ascii=False) + "\n")
                    f_expert.flush()  # 強制刷新緩衝區
                    expert_count += 1
                
                # 進度顯示
                if (i + 1) % 10 == 0:
                    progress = ((scammer_count + expert_count) / (total_cases * 2)) * 100
                    print(f"   ✅ [{i+1}/{config['count']}] 已保存 (總進度: {progress:.1f}%)")
                
                # API 限流（避免超過配額）
                time.sleep(1)  # 每次請求間隔 1 秒
    
    print("\n" + "=" * 60)
    print("✅ 生成完成！")
    print(f"   騙徒對話: {scammer_count} 個案例")
    print(f"   專家對話: {expert_count} 個案例")
    print(f"   總計: {scammer_count + expert_count} 個案例")
    print("=" * 60)

if __name__ == "__main__":
    main()

