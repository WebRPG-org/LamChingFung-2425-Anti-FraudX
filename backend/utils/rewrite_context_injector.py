"""
重寫上下文注入器
從日誌WARNING中提取失敗原因，動態注入到重寫prompt中
"""

import re
from typing import Optional, Dict, List
from datetime import datetime

from utils.logger import log


class RewriteContextInjector:
    """
    從角色一致性檢查的WARNING中提取失敗原因
    並生成針對性的重寫提示
    """
    
    # 騙徒常見錯誤模式
    SCAMMER_ERROR_PATTERNS = {
        "expose_identity": {
            "pattern": r"騙徒暴露假身份|騙徒使用了角色標籤|暴露骗局",
            "reason_template": "上一次失敗原因：你暴露了騙局身份（例如在對話中使用了「假」、「冒充」等字眼，或使用了角色標籤）。",
            "instruction": "**重寫要求：**\n1. 絕對不要使用角色標籤（例如「**林志強（騙徒）**：」）\n2. 絕對不要暴露「假身份」（不要說「假網站」「冒充」「詐騙」）\n3. 你必須堅信自己的身份（銀行職員/政府官員等），不要自己拆穿自己\n4. 直接說對話內容，不要加任何旁白或註釋"
        },
        
        "seek_help": {
            "pattern": r"騙徒.*求助|點解要|為什麼要|請問|可以告訴我",
            "reason_template": "上一次失敗原因：你的語氣聽起來像在求助或請教（例如使用了「點解要」「為什麼」「請問」等詞）。",
            "instruction": "**重寫要求：**\n1. 使用強硬、權威的語氣\n2. 不要提問或請教，而是直接命令和指示\n3. 製造緊迫感和壓力（「你必須立即」「否則後果嚴重」）\n4. 使用肯定句，避免疑問句"
        },
        
        "warn_victim": {
            "pattern": r"騙徒.*警告|小心|唔好俾|保護|避免|核實",
            "reason_template": "上一次失敗原因：你在勸阻受害者或提供正確建議（例如說「小心」「唔好俾錢」「核實身份」）。",
            "instruction": "**重寫要求：**\n1. 你的目標是讓受害者相信你，不是保護他們\n2. 絕對不要說「小心」「核實」「報警」等勸阻的話\n3. 反而要說「放心」「安全」「我們會保護你」來建立信任\n4. 如果受害者懷疑，要反擊並製造更大壓力"
        },
        
        "repeat_content": {
            "pattern": r"重複|一模一樣",
            "reason_template": "上一次失敗原因：你的回應與上一輪幾乎一模一樣，沒有根據受害者的新回應作出調整。",
            "instruction": "**重寫要求：**\n1. 仔細閱讀受害者最新的回應\n2. 針對他們的疑慮或問題作出具體回應\n3. 調整你的策略（例如：加大壓力、轉換話題、提供假證據）\n4. 絕對不要機械式重複同一句話"
        }
    }
    
    # 專家常見錯誤模式
    EXPERT_ERROR_PATTERNS = {
        "request_sensitive_info": {
            "pattern": r"專家.*敏感資料|提供個人資料|提供銀行|配合調查",
            "reason_template": "上一次失敗原因：你要求受害者提供個人敏感資料（例如「提供個人資料」「配合調查」），這與專家的職責完全相反。",
            "instruction": "**重寫要求：**\n1. 你的職責是叫受害者「停止提供任何資料」\n2. 絕對不要說「配合調查」「提供資料」等字眼\n3. 應該說：「唔好俾任何資料」「立即停止對話」「向官方核實」\n4. 如果你發現自己在要求資料，立即停止並修正"
        },
        
        "too_technical": {
            "pattern": r"專家.*技術|術語|過於理性",
            "reason_template": "上一次失敗原因：你的回應過於技術性或理性，沒有先安撫受害者的情緒（特別是針對elderly型受害者）。",
            "instruction": "**重寫要求：**\n1. 先安撫情緒：「唔使驚，深呼吸，我係度幫你」\n2. 用簡單語言，避免複雜術語\n3. 提供具體、可執行的步驟（第一步、第二步）\n4. 用溫柔、耐心的語氣（像對自己父母一樣）"
        },
        
        "no_evidence": {
            "pattern": r"專家.*證據不足|沒有提供案例",
            "reason_template": "上一次失敗原因：你只是說「這是騙案」，但沒有提供具體證據或真實案例來支持你的判斷。",
            "instruction": "**重寫要求：**\n1. 使用 get_expert_opinion 工具查詢真實案例\n2. 提供具體數字（「上個月有X宗類似案例」）\n3. 指出騙徒話術的具體破綻（「你留意佢避開咗你嘅問題」）\n4. 提供可驗證的信息（官方熱線號碼、網站）"
        },
        
        "late_intervention": {
            "pattern": r"專家.*時機太遲|介入太遲",
            "reason_template": "上一次失敗原因：你介入的時機太遲，受害者的信任度已經太高，難以扭轉。",
            "instruction": "**重寫要求：**\n1. 更早介入（在騙徒第一次製造恐慌時就要介入）\n2. 立即提供強有力的證據\n3. 預測騙徒的下一步話術，先告訴受害者\n4. 使用更強的語氣（「立即停止」而不是「建議你考慮」）"
        }
    }
    
    def __init__(self):
        self.warning_history: List[Dict] = []
    
    def extract_failure_reason(self, warning_message: str, agent_type: str) -> Optional[Dict]:
        """
        從WARNING訊息中提取失敗原因
        
        Args:
            warning_message: 日誌WARNING訊息
            agent_type: "scammer" 或 "expert"
            
        Returns:
            失敗原因字典，包含 reason 和 instruction
        """
        patterns = (
            self.SCAMMER_ERROR_PATTERNS if agent_type == "scammer" 
            else self.EXPERT_ERROR_PATTERNS
        )
        
        for error_type, config in patterns.items():
            if re.search(config["pattern"], warning_message, re.IGNORECASE):
                return {
                    "error_type": error_type,
                    "reason": config["reason_template"],
                    "instruction": config["instruction"],
                    "timestamp": datetime.now().isoformat()
                }
        
        # 如果沒有匹配到預定義模式，返回通用錯誤
        return {
            "error_type": "unknown",
            "reason": f"上一次失敗原因：{warning_message}",
            "instruction": "**重寫要求：**\n請仔細檢查你的回應，確保符合角色一致性要求。",
            "timestamp": datetime.now().isoformat()
        }
    
    def build_rewrite_prompt(
        self,
        original_prompt: str,
        warning_message: str,
        agent_type: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> str:
        """
        構建包含失敗原因的重寫prompt
        
        Args:
            original_prompt: 原始prompt
            warning_message: WARNING訊息
            agent_type: "scammer" 或 "expert"
            conversation_context: 對話上下文（可選）
            
        Returns:
            增強的重寫prompt
        """
        failure_info = self.extract_failure_reason(warning_message, agent_type)
        
        # 記錄到歷史
        self.warning_history.append(failure_info)
        
        # 構建增強prompt
        enhanced_prompt = f"""
🚨 **重寫任務說明**

{failure_info["reason"]}

{failure_info["instruction"]}

---

**原始對話上下文：**
{original_prompt}

---

**請根據以上要求，重新生成你的回應。記住：**
1. 直接輸出對話內容，不要有任何前綴說明
2. 符合角色一致性要求
3. 針對上次失敗的具體問題進行修正
"""
        
        # 如果有對話歷史，加入更多上下文
        if conversation_context:
            context_str = "\n".join([
                f"{turn.get('speaker', '未知')}：{turn.get('dialogue', '')}"
                for turn in conversation_context[-3:]  # 最後3輪
            ])
            enhanced_prompt += f"\n\n**最近3輪對話：**\n{context_str}"
        
        log.info(f"✏️ 構建重寫prompt (error_type={failure_info['error_type']})")
        
        return enhanced_prompt
    
    def get_warning_history(self) -> List[Dict]:
        """獲取WARNING歷史記錄"""
        return self.warning_history
    
    def clear_history(self):
        """清空歷史記錄"""
        self.warning_history = []


# 全局實例（用於在模擬過程中持續使用）
_global_injector = RewriteContextInjector()


def build_rewrite_prompt_with_context(
    original_prompt: str,
    warning_message: str,
    agent_type: str,
    conversation_context: Optional[List[Dict]] = None
) -> str:
    """
    便捷函數：構建包含失敗原因的重寫prompt
    """
    return _global_injector.build_rewrite_prompt(
        original_prompt,
        warning_message,
        agent_type,
        conversation_context
    )


def get_rewrite_history() -> List[Dict]:
    """獲取重寫歷史"""
    return _global_injector.get_warning_history()


def clear_rewrite_history():
    """清空重寫歷史"""
    _global_injector.clear_history()


if __name__ == "__main__":
    # 測試代碼
    injector = RewriteContextInjector()
    
    # 測試騙徒錯誤
    test_warning_scammer = "騙徒暴露骗局，需要重写"
    result = injector.extract_failure_reason(test_warning_scammer, "scammer")
    print("騙徒錯誤提取結果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 測試專家錯誤
    test_warning_expert = "專家要求提供敏感資料：「提供個人資料」"
    result = injector.extract_failure_reason(test_warning_expert, "expert")
    print("\n專家錯誤提取結果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))

