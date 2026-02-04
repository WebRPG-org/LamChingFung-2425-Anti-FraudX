"""
Chain-of-Thought (CoT) 提示模板
為騙徒 Agent 添加策略思考過程，提升騙術質量
"""

from typing import Dict, Optional


class ChainOfThoughtBuilder:
    """
    Chain-of-Thought 建構器
    為騙徒 Agent 生成結構化的思考過程
    """
    
    @staticmethod
    def build_scammer_cot(
        victim_persona: str,
        trust_level: int,
        conversation_history: list,
        scam_tactic: str
    ) -> str:
        """
        為騙徒建構 CoT Prompt
        
        Args:
            victim_persona: 受害者類型
            trust_level: 當前信任度
            conversation_history: 對話歷史
            scam_tactic: 詐騙手法
            
        Returns:
            包含思考過程的 Prompt
        """
        # 分析受害者弱點
        weakness = ChainOfThoughtBuilder._analyze_weakness(
            victim_persona, 
            conversation_history
        )
        
        # 生成策略選項
        strategy_options = ChainOfThoughtBuilder._generate_strategy_options(
            victim_persona,
            trust_level,
            scam_tactic
        )
        
        # 預測專家反駁
        expert_prediction = ChainOfThoughtBuilder._predict_expert_response(
            conversation_history
        )
        
        # 構建 CoT Prompt
        cot_prompt = f"""
## 內心思考過程（不要說出來）

**步驟 1：分析目標**
- 目標類型：{victim_persona}
- 當前信任度：{trust_level}/100
- 主要弱點：{weakness}

**步驟 2：選擇策略**
{strategy_options}

**步驟 3：預判反駁**
- 專家可能會說：{expert_prediction}
- 我的應對：{ChainOfThoughtBuilder._generate_counter_strategy(expert_prediction)}

**步驟 4：構建話術**
- 目標：{ChainOfThoughtBuilder._get_current_goal(trust_level)}
- 語氣：{ChainOfThoughtBuilder._get_tone(victim_persona)}
- 長度：不超過 50 字

---

**現在，根據以上思考，說出你的話（只說對話內容，不要暴露思考過程）：**
"""
        
        return cot_prompt
    
    @staticmethod
    def _analyze_weakness(victim_persona: str, history: list) -> str:
        """分析受害者弱點"""
        weakness_map = {
            "elderly": "對權威的信任、對科技的恐懼、害怕損失",
            "average": "對專業包裝的信任、對錯過機會的恐懼（FOMO）",
            "overconfident": "過度自信、好勝心、想證明自己",
            "student": "對高薪的渴望、社會經驗不足、容易衝動"
        }
        
        base_weakness = weakness_map.get(victim_persona, "未知")
        
        # 從對話歷史中分析額外弱點
        if history:
            victim_turns = [t for t in history if t.get("speaker") == "受騙者"]
            if victim_turns:
                last_response = victim_turns[-1].get("dialogue", "")
                
                if any(word in last_response for word in ["驚", "怕", "點算"]):
                    base_weakness += "、當前處於恐慌狀態"
                elif any(word in last_response for word in ["好", "明白", "係"]):
                    base_weakness += "、已經開始相信"
                elif any(word in last_response for word in ["懷疑", "唔信"]):
                    base_weakness += "、正在懷疑（需要加強說服）"
        
        return base_weakness
    
    @staticmethod
    def _generate_strategy_options(
        victim_persona: str,
        trust_level: int,
        scam_tactic: str
    ) -> str:
        """生成策略選項"""
        strategies = []
        
        # 根據信任度選擇策略
        if trust_level < 40:
            strategies.append("• 策略 A：建立信任 - 展示權威身份、提供證據")
        elif trust_level < 70:
            strategies.append("• 策略 B：製造壓力 - 強調緊急性、後果嚴重")
        else:
            strategies.append("• 策略 C：收網 - 要求行動、提供具體指示")
        
        # 根據 persona 調整策略
        if victim_persona == "elderly":
            strategies.append("• 針對長者：用簡單語言、展示關心、避免複雜術語")
        elif victim_persona == "average":
            strategies.append("• 針對普通人：用專業術語、展示證據、製造 FOMO")
        elif victim_persona == "overconfident":
            strategies.append("• 針對自信者：用激將法、技術挑戰、證明實力")
        elif victim_persona == "student":
            strategies.append("• 針對學生：強調高薪、彈性工作、簡單易做")
        
        # 根據詐騙手法添加特定策略
        if "銀行" in scam_tactic:
            strategies.append("• 手法重點：強調帳戶安全、法律責任、立即處理")
        elif "投資" in scam_tactic:
            strategies.append("• 手法重點：展示高回報、限時優惠、成功案例")
        elif "刷單" in scam_tactic:
            strategies.append("• 手法重點：先給甜頭、簡單易做、快速賺錢")
        
        return "\n".join(strategies)
    
    @staticmethod
    def _predict_expert_response(history: list) -> str:
        """預測專家可能的反駁"""
        if not history:
            return "「呢個係詐騙，唔好信」"
        
        expert_turns = [t for t in history if t.get("speaker") == "防騙專家"]
        
        if not expert_turns:
            return "「小心詐騙，唔好俾資料」"
        
        # 分析專家的常用策略
        last_expert = expert_turns[-1].get("dialogue", "")
        
        if "詐騙" in last_expert or "騙案" in last_expert:
            return "「呢個係典型嘅詐騙手法」"
        elif "唔好" in last_expert or "停止" in last_expert:
            return "「立即停止，唔好繼續」"
        elif "報警" in last_expert or "熱線" in last_expert:
            return "「打去官方熱線核實」"
        else:
            return "「小心處理，唔好衝動」"
    
    @staticmethod
    def _generate_counter_strategy(expert_prediction: str) -> str:
        """生成應對專家的策略"""
        counter_strategies = {
            "詐騙": "分化：「你信一個外人，都唔信我哋官方？」",
            "停止": "施壓：「你唔處理，後果更嚴重」",
            "報警": "反客為主：「我哋就係官方，你打去都係搵返我哋」",
            "核實": "製造急迫：「而家冇時間核實，必須立即處理」"
        }
        
        for keyword, strategy in counter_strategies.items():
            if keyword in expert_prediction:
                return strategy
        
        return "淡化：「唔好聽啲唔相關嘅人講嘢」"
    
    @staticmethod
    def _get_current_goal(trust_level: int) -> str:
        """根據信任度確定當前目標"""
        if trust_level < 40:
            return "建立信任和權威"
        elif trust_level < 70:
            return "製造恐慌和壓力"
        else:
            return "要求具體行動（轉賬/提供資料）"
    
    @staticmethod
    def _get_tone(victim_persona: str) -> str:
        """根據 persona 確定語氣"""
        tone_map = {
            "elderly": "親切、關心、權威",
            "average": "專業、理性、可信",
            "overconfident": "挑戰、技術、平等",
            "student": "友善、機會、簡單"
        }
        return tone_map.get(victim_persona, "自然、可信")


class AdaptiveStrategySelector:
    """
    自適應策略選擇器
    根據實時狀態動態調整專家策略
    """
    
    def __init__(self):
        self.strategy_history = []
        self.effectiveness = {}
    
    def select_strategy(
        self,
        victim_persona: str,
        trust_in_expert: int,
        trust_in_scammer: int,
        emotional_state: str,
        conversation_history: list
    ) -> Dict[str, any]:
        """
        根據當前狀態選擇最佳策略
        
        Args:
            victim_persona: 受害者類型
            trust_in_expert: 對專家的信任度
            trust_in_scammer: 對騙徒的信任度
            emotional_state: 情緒狀態
            conversation_history: 對話歷史
            
        Returns:
            策略字典（包含策略名稱、戰術、語氣）
        """
        # 情況 1：信任度極低，需要強證據
        if trust_in_expert < 30:
            return {
                "strategy": "strong_evidence",
                "tactics": [
                    "引用 3 個真實案例",
                    "提供官方數據",
                    "展示騙徒的具體破綻"
                ],
                "tone": "專業、權威",
                "priority": "high"
            }
        
        # 情況 2：情緒恐慌，優先安撫
        if emotional_state == "恐慌":
            return {
                "strategy": "emotional_support",
                "tactics": [
                    "先說「唔使驚」",
                    "用簡單語言解釋",
                    "提供具體行動步驟"
                ],
                "tone": "溫和、耐心",
                "priority": "urgent"
            }
        
        # 情況 3：對騙徒信任度很高，需要強力干預
        if trust_in_scammer > 80:
            return {
                "strategy": "strong_intervention",
                "tactics": [
                    "直接指出騙局特徵",
                    "提供多個證據",
                    "強調嚴重後果"
                ],
                "tone": "堅定、緊急",
                "priority": "critical"
            }
        
        # 情況 4：之前的策略失效，嘗試新方法
        if self._last_strategy_failed():
            return self._try_alternative_strategy(victim_persona)
        
        # 情況 5：標準策略
        return self._get_standard_strategy(victim_persona)
    
    def record_result(self, strategy: str, trust_change: int):
        """記錄策略效果"""
        if strategy not in self.effectiveness:
            self.effectiveness[strategy] = []
        
        self.effectiveness[strategy].append(trust_change)
        
        self.strategy_history.append({
            "strategy": strategy,
            "trust_change": trust_change,
            "timestamp": datetime.now()
        })
    
    def _last_strategy_failed(self) -> bool:
        """判斷上一個策略是否失效"""
        if len(self.strategy_history) < 2:
            return False
        
        last_strategy = self.strategy_history[-1]
        # 如果信任度沒有提升，視為失效
        return last_strategy["trust_change"] <= 0
    
    def _try_alternative_strategy(self, victim_persona: str) -> Dict:
        """嘗試替代策略"""
        # 如果標準策略失效，嘗試情感訴求
        return {
            "strategy": "emotional_appeal",
            "tactics": [
                "訴諸情感（「我見過太多人被騙」）",
                "建立同理心",
                "提供個人化建議"
            ],
            "tone": "真誠、關心",
            "priority": "medium"
        }
    
    def _get_standard_strategy(self, victim_persona: str) -> Dict:
        """獲取標準策略"""
        standard_strategies = {
            "elderly": {
                "strategy": "simple_and_clear",
                "tactics": [
                    "用簡單語言",
                    "提供具體步驟",
                    "安撫情緒"
                ],
                "tone": "溫和、耐心"
            },
            "average": {
                "strategy": "evidence_based",
                "tactics": [
                    "提供具體證據",
                    "邏輯分析",
                    "類似案例"
                ],
                "tone": "專業、理性"
            },
            "overconfident": {
                "strategy": "technical_analysis",
                "tactics": [
                    "技術角度分析",
                    "平等討論",
                    "不說教"
                ],
                "tone": "同行對話"
            },
            "student": {
                "strategy": "friendly_guidance",
                "tactics": [
                    "友善建議",
                    "提供資源",
                    "不說教"
                ],
                "tone": "友善、理解"
            }
        }
        
        return standard_strategies.get(victim_persona, standard_strategies["average"])


# 導入 datetime
from datetime import datetime
