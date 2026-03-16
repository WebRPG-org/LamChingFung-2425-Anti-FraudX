# 香港真實機構資料庫使用指南

## 📋 概覽

`backend/agents/hk_organizations.py` 包含香港所有主要機構的真實資料，用於增強詐騙模擬的真實性。

---

## 📊 資料庫內容

### 1. 執法機構
- **香港警務處**
  - 緊急熱線：999
  - 一般查詢：2860 2000
  - 防騙易熱線：18222
  - 反詐騙協調中心：2860 5012

- **廉政公署**
  - 舉報熱線：2526 6366

- **海關**
  - 24小時熱線：2815 7711

### 2. 金融監管機構
- **證監會**：2231 1222
- **金管局**：2878 8222
- **保監局**：2520 1868
- **積金局**：2918 0102

### 3. 主要銀行
- 滙豐銀行：2233 3000
- 恒生銀行：2822 0228
- 中國銀行(香港)：3988 2388
- 渣打銀行：2886 8868
- 東亞銀行：2211 1333
- 花旗銀行：2860 0333

### 4. 消費者保護
- **消委會**：2929 2222
- **競委會**：3462 2118

### 5. 通訊科技監管
- **通訊辦**：2961 6333
- **私隱專員公署**：2827 2827
- **智方便熱線**：182 123

### 6. 其他政府部門
- 入境處：2824 6111
- 運輸署：2804 2600
- 衞生署：2961 8989
- 勞工處：2717 1771
- 稅務局：187 8088

### 7. 電訊公司
- 香港電訊：1000
- 中國移動：2945 8888
- 3香港：3166 3333
- 數碼通：2880 2688

### 8. 快遞物流
- 香港郵政：2921 2222
- 順豐速運：2730 0273
- DHL：2400 3388
- FedEx：2730 3333

### 9. 常被冒充機構（重點）
- 香港警務處
- 入境事務處
- 海關
- 內地公安
- 各大銀行
- 快遞公司

---

## 🔧 使用方法

### 方法 1: 在 Expert Agent 中使用

```python
from backend.agents.hk_organizations import (
    get_official_hotline,
    get_bank_hotline,
    format_for_expert_response,
    get_anti_scam_hotlines
)

# 在專家介入時提供官方熱線
class ExpertAgent(Agent):
    def provide_official_contact(self, scam_type: str) -> str:
        """提供官方聯絡方式"""
        
        if "假冒官員" in scam_type:
            police_info = get_official_hotline("警務處")
            return f"立即掛線，打去警務處查詢熱線 {police_info['熱線']} 核實"
        
        elif "假冒銀行" in scam_type:
            return "立即掛線，打去你銀行嘅官方熱線（印喺你張卡背面）或銀行公會熱線 2780 1222"
        
        elif "投資" in scam_type:
            sfc_info = get_official_hotline("證監會")
            return f"打去證監會投資者熱線 {sfc_info['熱線']} 查證公司是否持牌"
        
        else:
            return "如有懷疑，打去防騙易熱線 18222"
```

### 方法 2: 在 Scammer Agent 中使用（增加真實性）

```python
from backend.agents.hk_organizations import BANKS, LAW_ENFORCEMENT

class ScammerAgent(Agent):
    def generate_fake_details(self, scam_type: str) -> dict:
        """生成假的但看起來真實的細節"""
        
        if scam_type == "假冒銀行":
            # 使用真實銀行名稱增加可信度
            real_banks = list(BANKS["主要銀行"].keys())
            fake_bank = random.choice(real_banks)
            
            return {
                "bank_name": fake_bank,
                "fake_employee_id": f"HK{random.randint(10000, 99999)}",
                "fake_case_number": f"FD{random.randint(100000, 999999)}"
            }
        
        elif scam_type == "假冒官員":
            return {
                "department": "香港警務處反詐騙組",
                "fake_officer_name": "陳警司",
                "fake_badge_number": f"PC{random.randint(10000, 99999)}"
            }
```

### 方法 3: 在 Prompt 中注入（增強 System Instructions）

```python
from backend.agents.hk_organizations import HONG_KONG_ORGANIZATIONS
import json

# 將機構資料注入到 System Instructions
def build_expert_system_instruction():
    # 載入防詐騙熱線
    hotlines = get_anti_scam_hotlines()
    hotlines_text = "\n".join([
        f"- {h['名稱']}：{h['熱線']} ({h['機構']})"
        for h in hotlines
    ])
    
    return f"""
你是香港防詐騙專家「黃 sir」。

## 官方熱線（必須記住）
{hotlines_text}

## 常被冒充的機構
- 香港警務處（真實熱線：2860 2000）
- 入境事務處（真實熱線：2824 6111）
- 各大銀行（銀行公會熱線：2780 1222）

## 核實方法
當受害者收到可疑來電時，你必須：
1. 立即建議掛線
2. 提供官方熱線讓受害者自行核實
3. 強調真正的機構絕不會透過電話要求提供密碼或轉帳

記住：你的建議必須包含具體的官方熱線號碼。
"""
```

### 方法 4: 動態生成專家建議

```python
from backend.agents.hk_organizations import format_for_expert_response

# 根據詐騙類型自動生成建議
scam_type = "假冒官員"
expert_advice = format_for_expert_response(scam_type)

print(expert_advice)
# 輸出：
# 立即掛線，如果你唔放心，可以打去以下官方熱線核實：
# - 警務處查詢熱線：2860 2000
# - 防騙易熱線：18222
# 記住，真正嘅警務人員絕不會透過電話要求你提供密碼或轉帳。
```

---

## 📝 實際應用範例

### 範例 1: 假冒警察詐騙

**騙徒**：
```
你好，我係香港警務處反詐騙組嘅陳警司，工作編號 PC12345。
你嘅身份證涉及一宗洗黑錢案件，需要立即配合調查。
```

**專家（使用真實資料）**：
```python
from backend.agents.hk_organizations import get_official_hotline

police_info = get_official_hotline("警務處")

response = f"""
等等！真正嘅警務人員唔會透過電話要求你提供銀行資料。
如果你唔放心，立即掛線，然後打去警務處查詢熱線 {police_info['熱線']} 核實。
或者打去防騙易熱線 18222 求助。
記住，警察絕不會要求你轉帳或提供密碼。
"""
```

### 範例 2: 假冒銀行詐騙

**騙徒**：
```
你好，我係滙豐銀行客戶服務部。你嘅網上理財帳戶出現異常登入，
需要你提供驗證碼確認身份。
```

**專家（使用真實資料）**：
```python
from backend.agents.hk_organizations import get_bank_hotline

hsbc_info = get_bank_hotline("滙豐")

response = f"""
小心！銀行絕對唔會要求你提供驗證碼。
立即掛線，如果你唔放心，打去滙豐銀行官方客戶服務熱線 {hsbc_info['客戶服務']} 核實。
驗證碼係用嚟登入或轉帳，千祈唔好俾任何人。
"""
```

### 範例 3: 投資詐騙

**騙徒**：
```
你好，我係XX投資公司嘅理財顧問。我哋有個獨家投資項目，
保證每月回報10%，而家仲有優惠。
```

**專家（使用真實資料）**：
```python
from backend.agents.hk_organizations import get_official_hotline

sfc_info = get_official_hotline("證監會")

response = f"""
小心！保證高回報嘅投資通常都係騙局。
你可以打去證監會投資者熱線 {sfc_info['熱線']}，
或者上證監會網站 https://apps.sfc.hk/publicregWeb/ 查證公司是否持牌。
合法投資公司唔會保證回報，而且要喺證監會註冊。
"""
```

---

## 🎯 整合到 System Instructions

### 更新 Expert System Instruction

```python
# backend/agents/system_instructions.py

from backend.agents.hk_organizations import (
    get_anti_scam_hotlines,
    COMMONLY_IMPERSONATED
)

# 生成官方熱線列表
hotlines = get_anti_scam_hotlines()
hotlines_text = "\n".join([f"- {h['名稱']}：{h['熱線']}" for h in hotlines])

# 生成常被冒充機構列表
impersonated = COMMONLY_IMPERSONATED["最常被冒充"]
impersonated_text = "\n".join([
    f"- {org['機構']}（真實熱線：{org['真實熱線']}）- {org['警告']}"
    for org in impersonated
])

EXPERT_SYSTEM_INSTRUCTION = f"""
# 身份設定
你是香港防詐騙專家「黃 sir」（黃志明警司）。

## 官方熱線（必須記住並經常引用）
{hotlines_text}

## 常被冒充的機構及警告
{impersonated_text}

## 你的職責
當你介入對話時，你必須：
1. 指出詐騙特徵
2. **提供具體的官方熱線**讓受害者核實
3. 給出可執行的行動步驟

## 回應範例
「立即掛線，如果你唔放心，打去警務處查詢熱線 2860 2000 核實。
或者打去防騙易熱線 18222 求助。記住，警察絕不會要求你轉帳。」

記住：你的建議必須包含具體的官方熱線號碼，這樣才有說服力。
"""
```

---

## 📊 統計數據

資料庫包含：
- **13 個類別**的機構
- **50+ 個機構**的詳細資料
- **100+ 個官方熱線**
- **6 個最常被冒充的機構**
- **4 個實用查詢工具**

---

## ✅ 優勢

1. **真實性**：所有熱線和網址都是真實的
2. **完整性**：涵蓋所有可能被冒充的機構
3. **實用性**：提供具體的核實方法
4. **可維護性**：集中管理，易於更新
5. **靈活性**：提供多種使用方式

---

## 🔄 更新建議

定期檢查並更新：
- 官方熱線號碼
- 機構網址
- 新增的詐騙手法
- 新的查詢工具

---

## 📚 相關文件

- `backend/agents/hk_organizations.py` - 完整資料庫
- `backend/agents/system_instructions.py` - System Instructions
- `GEMINI_IMPLEMENTATION_GUIDE.md` - 實現指南

---

## 💡 使用建議

### 對於騙徒 Agent
- 使用真實機構名稱增加可信度
- 但不要使用真實的工作編號或案件編號

### 對於專家 Agent
- **必須**提供具體的官方熱線
- 強調核實的重要性
- 給出可執行的步驟

### 對於受害者 Agent
- 可以表現出對官方機構的信任
- 聽到真實熱線時會更容易相信專家

---

## ✅ 完成！

現在您可以在對話中使用真實的香港機構資料，大大增強模擬的真實性和教育效果！
