"""
騙徒動態策略調整系統
根據受害者反應自動調整詐騙策略
"""

from typing import Dict, List, Optional
from enum import Enum

from utils.logger import log


class ScamStrategy(Enum):
    """詐騙策略類型"""
    AUTHORITY = "authority"  # 權威施壓
    URGENCY = "urgency"      # 製造緊迫感
    GREED = "greed"          # 利誘貪念
    FEAR = "fear"            # 恐嚇威脅
    SYMPATHY = "sympathy"    # 裝可憐博同情
    SOCIAL_PROOF = "social_proof"  # 社會證明（別人都做了）
    CONFUSION = "confusion"  # 混淆視聽
    FLATTERY = "flattery"    # 恭維奉承


class StrategyManager:
    """
    策略管理器
    
    功能：
    1. 根據受害者信任度變化調整策略
    2. 根據受害者類型選擇最有效的策略
    3. 提供策略切換的具體話術指導
    """
    
    # 策略對應的話術模板
    STRATEGY_TEMPLATES = {
        ScamStrategy.AUTHORITY: {
            "prompt_addition": """
**當前策略：權威施壓**

你必須：
1. 使用權威語氣：「我係政府部門」「你必須配合」
2. 引用法律條文或規定（假的也可以）
3. 展示專業術語和程序
4. 強調不配合的嚴重後果

範例：
「根據《XX條例》，你嘅戶口涉及可疑交易，必須立即配合調查。如果唔配合，根據第23條，你會被列為涉案人士，後果非常嚴重！」
""",
            "keywords": ["法律", "條例", "規定", "必須", "配合", "否則"]
        },
        
        ScamStrategy.URGENCY: {
            "prompt_addition": """
**當前策略：製造緊迫感**

你必須：
1. 強調時間緊迫：「只剩X分鐘」「馬上就過期」
2. 製造即將失去的恐懼：「錯過就冇機會」
3. 倒數計時壓力
4. 阻止對方冷靜思考

範例：
「你嘅戶口而家立即就會被凍結，只剩5分鐘處理！過咗時間系統就會自動鎖定，到時我都幫唔到你！你而家唔即刻轉賬，損失全部責任自負！」
""",
            "keywords": ["立即", "馬上", "只剩", "倒數", "過期", "來不及"]
        },
        
        ScamStrategy.GREED: {
            "prompt_addition": """
**當前策略：利誘貪念**

你必須：
1. 強調高回報、低風險
2. 製造「獨家機會」「內部消息」的感覺
3. 先給小甜頭建立信任
4. 暗示「別人都賺到了」

範例：
「呢個投資機會係內部人士先知，保證月回報20%！你睇下，我哋已經幫咗好多客戶賺到錢。你第一次投入1000蚊試下，我哋會即刻俾你200蚊回報，你就知我哋係真嘅！」
""",
            "keywords": ["回報", "賺錢", "機會", "獨家", "保證", "內部"]
        },
        
        ScamStrategy.FEAR: {
            "prompt_addition": """
**當前策略：恐嚇威脅**

你必須：
1. 製造具體的恐懼：「你會被捕」「全部錢冇晒」
2. 引用假的法律後果
3. 暗示調查、監控、檔案記錄
4. 讓對方感到無路可退

範例：
「你嘅身份已經被盜用做咗洗黑錢活動，警方正在調查緊！如果你唔立即配合清白，你會被列為疑犯，到時會有拘捕令！你嘅所有銀行戶口都會被凍結，仲會影響你家人！」
""",
            "keywords": ["警察", "拘捕", "凍結", "調查", "檔案", "後果"]
        },
        
        ScamStrategy.SYMPATHY: {
            "prompt_addition": """
**當前策略：裝可憐博同情**

你必須：
1. 展現脆弱或困難處境
2. 請求幫助而不是命令
3. 建立情感連結
4. 讓對方覺得「幫你就係做好事」

範例：
「我真係好需要你幫忙...我媽媽入咗醫院，急需醫藥費。我試過問銀行借錢，但佢哋話要幾日先批到。你可唔可以暫時借我5000蚊？我保證下星期一定還俾你，我會寫借據俾你！」
""",
            "keywords": ["幫忙", "困難", "家人", "醫院", "求你", "拜託"]
        },
        
        ScamStrategy.SOCIAL_PROOF: {
            "prompt_addition": """
**當前策略：社會證明**

你必須：
1. 強調「好多人都做咗」
2. 引用假的成功案例
3. 製造從眾壓力
4. 讓對方覺得「唔做就蝕底」

範例：
「我哋呢個投資計劃已經有超過1000個客戶參加，每個都賺到錢！你嘅鄰居張太上個月都投資咗，而家每個月收息5000蚊。你唔試下就太蝕底啦！名額有限，而家仲有最後3個位！」
""",
            "keywords": ["好多人", "大家", "鄰居", "成功", "名額", "限量"]
        },
        
        ScamStrategy.CONFUSION: {
            "prompt_addition": """
**當前策略：混淆視聽**

你必須：
1. 用複雜的術語和程序
2. 快速轉移話題
3. 製造信息過載
4. 讓對方放棄思考，直接聽從指示

範例：
「你嘅情況涉及跨境交易監管條例第45(b)款，需要進行KYC認證同AML審查，同時要啟動FATCA申報程序。呢個程序比較複雜，你聽我講就得，我會一步步教你填表...」
""",
            "keywords": ["條例", "程序", "認證", "審查", "專業術語"]
        },
        
        ScamStrategy.FLATTERY: {
            "prompt_addition": """
**當前策略：恭維奉承**

你必須：
1. 恭維對方聰明、有眼光
2. 讓對方覺得自己是「特選的」
3. 滿足對方的虛榮心
4. 建立「我們是同類人」的感覺

範例：
「我一睇就知你係有眼光、識投資嘅人！唔係個個都有資格參加我哋呢個VIP計劃，只有高淨值客戶先會被邀請。你咁聰明，一定明白呢個機會嘅價值！」
""",
            "keywords": ["聰明", "有眼光", "VIP", "特選", "精英", "高端"]
        }
    }
    
    def __init__(self):
        self.current_strategy = ScamStrategy.AUTHORITY  # 默認策略
        self.strategy_history: List[Dict] = []
        self.switch_count = 0
    
    def recommend_strategy(
        self,
        victim_trust_scammer: int,
        victim_trust_expert: int,
        victim_persona: str,
        previous_strategy: Optional[ScamStrategy] = None,
        trust_change_trend: str = "stable"  # "increasing", "decreasing", "stable"
    ) -> ScamStrategy:
        """
        根據當前情況推薦最佳策略
        
        Args:
            victim_trust_scammer: 受害者對騙徒的信任度 (0-100)
            victim_trust_expert: 受害者對專家的信任度 (0-100)
            victim_persona: 受害者類型 ("elderly", "average", "overconfident", "skeptical", "greedy")
            previous_strategy: 上一次使用的策略
            trust_change_trend: 信任度變化趨勢
            
        Returns:
            推薦的策略
        """
        # 策略選擇邏輯
        
        # 1. 如果信任度很高且穩定，保持當前策略
        if victim_trust_scammer >= 80 and trust_change_trend != "decreasing":
            if previous_strategy:
                log.info(f"✅ 信任度高且穩定 ({victim_trust_scammer}/100)，保持策略: {previous_strategy.value}")
                return previous_strategy
        
        # 2. 如果信任度下降，需要切換策略
        if trust_change_trend == "decreasing" or victim_trust_expert > victim_trust_scammer:
            log.warning(f"⚠️ 信任度下降或專家佔上風，需要切換策略")
            
            # 根據受害者類型選擇反擊策略
            if victim_persona == "elderly":
                # 老年人：加大恐嚇或權威壓力
                return ScamStrategy.FEAR if previous_strategy != ScamStrategy.FEAR else ScamStrategy.AUTHORITY
            
            elif victim_persona == "overconfident":
                # 過度自信者：用恭維或利誘
                return ScamStrategy.FLATTERY if previous_strategy != ScamStrategy.FLATTERY else ScamStrategy.GREED
            
            elif victim_persona == "greedy":
                # 貪婪型：強化利誘
                return ScamStrategy.GREED
            
            elif victim_persona == "skeptical":
                # 多疑型：用社會證明或權威
                return ScamStrategy.SOCIAL_PROOF if previous_strategy != ScamStrategy.SOCIAL_PROOF else ScamStrategy.AUTHORITY
            
            else:  # average
                # 普通人：混合使用
                return ScamStrategy.URGENCY if previous_strategy != ScamStrategy.URGENCY else ScamStrategy.FEAR
        
        # 3. 根據受害者類型選擇初始策略
        if previous_strategy is None:
            if victim_persona == "elderly":
                return ScamStrategy.AUTHORITY  # 老年人容易被權威唬住
            elif victim_persona == "greedy":
                return ScamStrategy.GREED  # 貪婪型用利誘
            elif victim_persona == "overconfident":
                return ScamStrategy.FLATTERY  # 過度自信者用恭維
            elif victim_persona == "skeptical":
                return ScamStrategy.AUTHORITY  # 多疑型用權威壓制
            else:
                return ScamStrategy.URGENCY  # 普通人用緊迫感
        
        # 4. 默認：保持當前策略
        return previous_strategy or ScamStrategy.AUTHORITY
    
    def build_strategy_prompt(
        self,
        base_prompt: str,
        strategy: ScamStrategy,
        victim_context: Optional[Dict] = None
    ) -> str:
        """
        構建包含策略指導的prompt
        
        Args:
            base_prompt: 基礎prompt
            strategy: 要使用的策略
            victim_context: 受害者上下文信息
            
        Returns:
            增強的prompt
        """
        template = self.STRATEGY_TEMPLATES.get(strategy, {})
        strategy_addition = template.get("prompt_addition", "")
        
        enhanced_prompt = f"""
{strategy_addition}

---

{base_prompt}

---

**重要提醒：**
請使用以上策略來構建你的回應。記住你的目標是讓受害者相信你並配合你的要求。
"""
        
        # 記錄策略使用
        self.strategy_history.append({
            "strategy": strategy.value,
            "victim_context": victim_context
        })
        
        log.info(f"🎯 應用策略：{strategy.value} (第{len(self.strategy_history)}次切換)")
        
        return enhanced_prompt
    
    def should_switch_strategy(
        self,
        victim_trust_scammer: int,
        previous_trust: int,
        rounds_since_switch: int
    ) -> bool:
        """
        判斷是否應該切換策略
        
        Args:
            victim_trust_scammer: 當前信任度
            previous_trust: 上一輪信任度
            rounds_since_switch: 距離上次切換的輪數
            
        Returns:
            是否應該切換
        """
        # 1. 信任度持續下降
        if victim_trust_scammer < previous_trust - 10:
            log.info(f"📉 信任度顯著下降 ({previous_trust} -> {victim_trust_scammer})，建議切換策略")
            return True
        
        # 2. 同一策略使用太久沒效果
        if rounds_since_switch >= 3 and victim_trust_scammer < 60:
            log.info(f"⏰ 同一策略使用{rounds_since_switch}輪效果不佳，建議切換")
            return True
        
        # 3. 信任度過低，需要改變策略
        if victim_trust_scammer < 40:
            log.info(f"🚨 信任度過低 ({victim_trust_scammer}/100)，需要切換策略")
            return True
        
        return False
    
    def get_strategy_history(self) -> List[Dict]:
        """獲取策略使用歷史"""
        return self.strategy_history


# 全局實例
_global_strategy_manager = StrategyManager()


def recommend_scammer_strategy(
    victim_trust_scammer: int,
    victim_trust_expert: int,
    victim_persona: str,
    previous_strategy: Optional[str] = None,
    trust_change_trend: str = "stable"
) -> str:
    """
    便捷函數：推薦騙徒策略
    
    Returns:
        策略名稱（字符串）
    """
    prev_strategy_enum = None
    if previous_strategy:
        try:
            prev_strategy_enum = ScamStrategy(previous_strategy)
        except ValueError:
            pass
    
    recommended = _global_strategy_manager.recommend_strategy(
        victim_trust_scammer,
        victim_trust_expert,
        victim_persona,
        prev_strategy_enum,
        trust_change_trend
    )
    
    return recommended.value


def build_strategy_enhanced_prompt(
    base_prompt: str,
    strategy: str,
    victim_context: Optional[Dict] = None
) -> str:
    """
    便捷函數：構建包含策略的prompt
    """
    try:
        strategy_enum = ScamStrategy(strategy)
    except ValueError:
        strategy_enum = ScamStrategy.AUTHORITY
    
    return _global_strategy_manager.build_strategy_prompt(
        base_prompt,
        strategy_enum,
        victim_context
    )


if __name__ == "__main__":
    # 測試代碼
    print("騙徒策略管理器測試\n")
    
    manager = StrategyManager()
    
    # 測試情景1：老年受害者，信任度高
    print("情景1：老年受害者，信任度高")
    strategy = manager.recommend_strategy(
        victim_trust_scammer=85,
        victim_trust_expert=30,
        victim_persona="elderly",
        trust_change_trend="stable"
    )
    print(f"推薦策略：{strategy.value}\n")
    
    # 測試情景2：信任度下降
    print("情景2：信任度下降")
    strategy = manager.recommend_strategy(
        victim_trust_scammer=55,
        victim_trust_expert=70,
        victim_persona="average",
        previous_strategy=ScamStrategy.AUTHORITY,
        trust_change_trend="decreasing"
    )
    print(f"推薦策略：{strategy.value}\n")
    
    # 測試情景3：過度自信者
    print("情景3：過度自信者")
    strategy = manager.recommend_strategy(
        victim_trust_scammer=40,
        victim_trust_expert=50,
        victim_persona="overconfident",
        trust_change_trend="decreasing"
    )
    print(f"推薦策略：{strategy.value}\n")

