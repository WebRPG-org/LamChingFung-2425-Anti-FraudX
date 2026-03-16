# 香港真實機構資料庫 - 完整版
## 基於詐騙手法的真實細節還原

---

## 📊 資料庫統計

### 總覽
- **24 個類別**的機構和資料
- **100+ 個機構**的詳細資料
- **200+ 個官方熱線**
- **8 種詐騙手法**的詳細資料
- **50+ 個常用開場白和話術**

### 新增內容（相比基礎版）

#### 1. 網購相關（5 個平台）
- 淘寶、天貓、京東
- HKTVmall、Carousell

#### 2. 支付平台（5 個）
- PayMe、轉數快（FPS）
- 支付寶（香港）、WeChat Pay、八達通

#### 3. 投資證券（3 家公司）
- 耀才證券、富途證券、盈透證券
- 包含證監會查牌網址

#### 4. 虛擬貨幣
- 合法持牌平台查詢方法
- 5 個常見詐騙特徵

#### 5. 社交媒體（5 個平台）
- Facebook、Instagram、WhatsApp
- Telegram、小紅書

#### 6. 求職平台（5 個）
- JobsDB、CTgoodjobs、Indeed
- LinkedIn、勞工處互動就業服務

#### 7. 票務平台（4 個）
- KKTIX、Cityline、HK Ticketing、Klook

#### 8. 內地執法機構
- 常被冒充的 7 個機構
- 5 個詐騙特徵
- 正確處理方法

#### 9. 租屋相關（3 個機構）
- 地產代理監管局
- 差餉物業估價署
- 土地註冊處

#### 10. 貸款財務
- 放債人註冊處
- 5 個警告事項
- 3 個求助熱線

#### 11. 詐騙手法詳細資料（8 種）
- 假冒官員詐騙
- 假冒銀行詐騙
- 投資詐騙
- 網購詐騙
- 求職詐騙
- 愛情詐騙
- 租屋詐騙
- 電話騙案（改號電話）

---

## 🎯 按詐騙手法分類的使用方法

### 1. 假冒官員詐騙

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import (
    get_scammer_opening_lines,
    get_scammer_tactics
)

# 獲取開場白
opening_lines = get_scammer_opening_lines("假冒官員詐騙")
# 返回：
# [
#   "你好，我係香港警務處反詐騙組嘅警員",
#   "我係入境事務處嘅職員，你嘅身份證涉及一宗案件",
#   "我係海關人員，你有包裹被扣查",
#   "我係內地公安，你在深圳涉及一宗刑事案件"
# ]

# 獲取常用話術
tactics = get_scammer_tactics("假冒官員詐騙")
# 返回：
# [
#   "你嘅身份證被人盜用",
#   "你涉及洗黑錢案件",
#   "需要立即配合調查",
#   ...
# ]
```

#### 專家可用資料
```python
from backend.agents.hk_organizations import (
    generate_expert_context,
    format_for_expert_response
)

# 生成完整的專家建議
expert_advice = format_for_expert_response("假冒官員")
# 返回完整的建議文字，包含：
# - 官方熱線（警務處：2860 2000、防騙易：18222）
# - 核實方法
# - 關鍵警告

# 或獲取更詳細的上下文
context = generate_expert_context("假冒官員詐騙")
# 包含核實方法、官方熱線、關鍵警告等
```

---

### 2. 假冒銀行詐騙

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import (
    BANKS,
    get_scammer_opening_lines
)

# 獲取真實銀行名稱（增加可信度）
real_banks = list(BANKS["主要銀行"].keys())
# ['滙豐銀行', '恒生銀行', '中國銀行(香港)', '渣打銀行', '東亞銀行', '花旗銀行']

# 獲取開場白
opening_lines = get_scammer_opening_lines("假冒銀行詐騙")
# [
#   "你好，我係XX銀行客戶服務部",
#   "你嘅網上理財帳戶出現異常登入",
#   "你嘅信用卡有可疑交易",
#   "你嘅帳戶需要更新資料"
# ]
```

#### 專家可用資料
```python
from backend.agents.hk_organizations import (
    get_bank_hotline,
    format_for_expert_response
)

# 獲取特定銀行的官方熱線
hsbc_info = get_bank_hotline("滙豐")
# {
#   "銀行": "滙豐銀行",
#   "客戶服務": "2233 3000",
#   "信用卡": "2748 8033",
#   "網址": "https://www.hsbc.com.hk"
# }

# 生成專家建議
advice = format_for_expert_response("假冒銀行")
# 包含銀行公會熱線、核實方法、關鍵警告
```

---

### 3. 投資詐騙

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import (
    get_scammer_opening_lines,
    get_scammer_tactics,
    INVESTMENT_FIRMS
)

# 獲取開場白
opening_lines = get_scammer_opening_lines("投資詐騙")
# [
#   "你好，我係XX投資公司嘅理財顧問",
#   "我哋有個獨家投資項目",
#   "保證每月回報10%",
#   ...
# ]

# 可參考真實投資公司名稱（但不要完全冒充）
real_firms = list(INVESTMENT_FIRMS.keys())
```

#### 專家可用資料
```python
from backend.agents.hk_organizations import (
    get_official_hotline,
    SCAM_TACTICS_DETAILS
)

# 獲取證監會資料
sfc_info = get_official_hotline("證監會")
# {
#   "機構": "證券及期貨事務監察委員會",
#   "熱線": "2231 1222",
#   "網址": "https://www.sfc.hk"
# }

# 獲取查牌網址
details = SCAM_TACTICS_DETAILS["投資詐騙"]
check_url = details["查牌網址"]
# "https://apps.sfc.hk/publicregWeb/"
```

---

### 4. 網購詐騙

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import (
    ECOMMERCE_PLATFORMS,
    SCAM_TACTICS_DETAILS
)

# 獲取常見網購平台
platforms = list(ECOMMERCE_PLATFORMS.keys())
# ['淘寶', '天貓', '京東', 'HKTVmall', 'Carousell']

# 獲取常見貨品
details = SCAM_TACTICS_DETAILS["網購詐騙"]
common_goods = details["常見貨品"]
# ['演唱會門票', '限量波鞋', '名牌手袋', '電子產品', '口罩']
```

#### 專家可用資料
```python
from backend.agents.hk_organizations import (
    VERIFICATION_TOOLS,
    format_for_expert_response
)

# 獲取防騙視伏器資料
cyberdefender = VERIFICATION_TOOLS["防騙視伏器"]
# {
#   "網址": "https://cyberdefender.hk",
#   "功能": "評估網購風險、檢查可疑網站",
#   "提供者": "香港警務處"
# }

# 生成專家建議
advice = format_for_expert_response("網購")
# 包含防騙視伏器、消委會熱線等
```

---

### 5. 求職詐騙

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import SCAM_TACTICS_DETAILS

details = SCAM_TACTICS_DETAILS["求職詐騙"]

# 常見招聘
job_types = details["常見招聘"]
# ['點讚員', '下單員', '數據輸入員', '在家工作', '兼職打字員']

# 詐騙特徵（騙徒應該使用這些）
features = details["詐騙特徵"]
# [
#   "不需要學歷經驗",
#   "高薪厚職",
#   "在家工作",
#   ...
# ]
```

#### 專家可用資料
```python
from backend.agents.hk_organizations import (
    get_official_hotline,
    format_for_expert_response
)

# 獲取勞工處資料
labour_info = get_official_hotline("勞工處")
# {
#   "機構": "勞工處",
#   "熱線": "2717 1771",
#   "網址": "https://www.labour.gov.hk"
# }

# 生成專家建議
advice = format_for_expert_response("求職")
```

---

### 6. 愛情詐騙

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import SCAM_TACTICS_DETAILS

details = SCAM_TACTICS_DETAILS["愛情詐騙"]

# 騙徒特徵（騙徒應該扮演這些角色）
characteristics = details["騙徒特徵"]
# [
#   "自稱高富帥或白富美",
#   "快速建立戀愛關係",
#   "從未見面或視像通話",
#   ...
# ]

# 詐騙手法
methods = details["詐騙手法"]
# [
#   "游說投資虛擬貨幣",
#   "聲稱遇到困難需要借錢",
#   ...
# ]
```

#### 專家可用資料
```python
from backend.agents.hk_organizations import format_for_expert_response

# 生成專家建議
advice = format_for_expert_response("愛情")
# 包含關鍵警告：網上戀人要求金錢往來，必定是騙局
```

---

### 7. 租屋詐騙

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import SCAM_TACTICS_DETAILS

details = SCAM_TACTICS_DETAILS["租屋詐騙"]

# 常見平台
platforms = details["常見平台"]
# ['小紅書', 'Facebook', 'Instagram']

# 詐騙特徵
features = details["詐騙特徵"]
# [
#   "租金明顯低於市價",
#   "只有照片，不能實地睇樓",
#   ...
# ]
```

#### 專家可用資料
```python
from backend.agents.hk_organizations import (
    PROPERTY_AGENCIES,
    format_for_expert_response
)

# 獲取地產代理監管局資料
eaa_info = PROPERTY_AGENCIES["地產代理監管局"]
# {
#   "查詢熱線": "2111 2777",
#   "持牌人查詢": "https://www.eaa.org.hk/..."
# }

# 生成專家建議
advice = format_for_expert_response("租屋")
```

---

### 8. 電話騙案（改號電話）

#### 騙徒可用資料
```python
from backend.agents.hk_organizations import SCAM_TACTICS_DETAILS

details = SCAM_TACTICS_DETAILS["電話騙案（改號電話）"]

# 特徵
feature = details["特徵"]
# "來電顯示 +852 開頭"

# 常被冒充的機構
impersonated = details["常被冒充"]
# ['政府部門', '銀行', '快遞公司', '電訊公司']
```

#### 專家可用資料
```python
# 專家應該強調
warning = "+852 開頭的來電可能是改號電話，掛線後用自己的電話打去官方熱線核實"
```

---

## 🔧 進階使用方法

### 方法 1: 動態生成騙徒對話

```python
from backend.agents.hk_organizations import generate_scammer_context
import random

def generate_scammer_dialogue(scam_type: str) -> str:
    """動態生成騙徒對話"""
    
    # 獲取上下文
    context = generate_scammer_context(scam_type)
    
    # 獲取開場白
    opening_lines = get_scammer_opening_lines(scam_type)
    opening = random.choice(opening_lines) if opening_lines else "你好"
    
    # 構建完整 Prompt
    prompt = f"""
{context}

## 你的任務
使用以上資料，開始與受害者對話。

## 你的第一句話
{opening}

現在繼續對話，根據受害者的反應調整策略。
"""
    
    return prompt
```

### 方法 2: 動態生成專家建議

```python
from backend.agents.hk_organizations import generate_expert_context

def generate_expert_advice(scam_type: str, victim_concern: str) -> str:
    """動態生成專家建議"""
    
    # 獲取基礎上下文
    context = generate_expert_context(scam_type)
    
    # 根據受害者關注點調整建議
    if "驚" in victim_concern or "恐慌" in victim_concern:
        # 先安撫情緒
        advice = "唔使驚，深呼吸，我幫你。\n\n" + context
    else:
        advice = context
    
    return advice
```

### 方法 3: 整合到 System Instructions

```python
from backend.agents.hk_organizations import (
    SCAM_TACTICS_DETAILS,
    get_anti_scam_hotlines
)

def build_expert_system_instruction_with_real_data():
    """構建包含真實資料的 System Instruction"""
    
    # 獲取所有防詐騙熱線
    hotlines = get_anti_scam_hotlines()
    hotlines_text = "\n".join([
        f"- {h['名稱']}：{h['熱線']}"
        for h in hotlines
    ])
    
    # 獲取所有詐騙手法的核實方法
    verification_methods = {}
    for scam_type, details in SCAM_TACTICS_DETAILS.items():
        if "核實方法" in details:
            verification_methods[scam_type] = details["核實方法"]
    
    instruction = f"""
你是香港防詐騙專家「黃 sir」。

## 官方熱線（必須記住）
{hotlines_text}

## 各類詐騙的核實方法
"""
    
    for scam_type, method in verification_methods.items():
        instruction += f"\n### {scam_type}\n{method}\n"
    
    instruction += """
## 你的職責
當你介入對話時，你必須：
1. 指出詐騙特徵
2. 提供具體的官方熱線
3. 給出可執行的核實方法

記住：你的建議必須包含具體的熱線號碼和網址。
"""
    
    return instruction
```

---

## 📊 完整統計

```python
from backend.agents.hk_organizations import HONG_KONG_ORGANIZATIONS

# 統計所有資料
total_categories = len(HONG_KONG_ORGANIZATIONS)
# 24 個類別

total_scam_types = len(SCAM_TACTICS_DETAILS)
# 8 種詐騙手法

total_banks = len(BANKS["主要銀行"])
# 6 家主要銀行

total_payment_platforms = len(PAYMENT_PLATFORMS)
# 5 個支付平台

total_ecommerce = len(ECOMMERCE_PLATFORMS)
# 5 個網購平台
```

---

## ✅ 優勢

1. **真實性**：所有機構名稱、熱線、網址都是真實的
2. **完整性**：涵蓋 8 種主要詐騙手法的所有細節
3. **實用性**：提供具體的核實方法和官方熱線
4. **靈活性**：可根據詐騙類型動態生成對話和建議
5. **可維護性**：集中管理，易於更新

---

## 📚 相關文件

- `backend/agents/hk_organizations.py` - 完整資料庫（1200+ 行）
- `HK_ORGANIZATIONS_GUIDE.md` - 基礎使用指南
- `backend/agents/system_instructions.py` - System Instructions
- `GEMINI_IMPLEMENTATION_GUIDE.md` - 實現指南

---

## 🎉 完成！

現在您擁有了最完整的香港真實機構資料庫，可以：
- ✅ 讓騙徒使用真實的機構名稱和話術
- ✅ 讓專家提供具體的官方熱線和核實方法
- ✅ 根據 8 種詐騙手法動態生成對話
- ✅ 大大增強模擬的真實性和教育效果

準備好整合到 Gemini 3 System Instructions 了嗎？
