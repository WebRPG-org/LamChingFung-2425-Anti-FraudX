"""
Prompt 輔助函數
提供版本化的 Prompt 獲取功能
"""

from typing import Dict, Optional
from utils.prompt_version_manager import PromptVersionManager
from agents.prompts.prompt_builder import PromptBuilder
from utils.logger import log


def get_versioned_prompt(
    version_manager: PromptVersionManager,
    agent_type: str,
    context: Dict
) -> str:
    """
    獲取版本化的 Prompt
    
    Args:
        version_manager: 版本管理器實例
        agent_type: Agent 類型 (expert, scammer, victim)
        context: Prompt 上下文參數
        
    Returns:
        完整的 Prompt 字符串
    """
    try:
        # 獲取當前活躍版本
        active_version = version_manager.get_active_version(agent_type)
        
        # 嘗試獲取版本化的 Prompt 模板
        prompt_template = version_manager.get_version(agent_type, active_version)
        
        if prompt_template:
            log.info(f"📝 使用版本化 Prompt: {agent_type}/{active_version}")
            # 使用模板格式化
            try:
                return prompt_template.format(**context)
            except KeyError as e:
                log.warning(f"⚠️ Prompt 模板格式化失敗: {e}，使用默認 PromptBuilder")
                return _build_default_prompt(agent_type, context)
        else:
            # 沒有版本化 Prompt，使用默認的 PromptBuilder
            log.info(f"📝 使用默認 PromptBuilder: {agent_type}")
            return _build_default_prompt(agent_type, context)
            
    except Exception as e:
        log.error(f"❌ 獲取版本化 Prompt 失敗: {e}，使用默認 PromptBuilder")
        return _build_default_prompt(agent_type, context)


def _build_default_prompt(agent_type: str, context: Dict) -> str:
    """
    使用默認的 PromptBuilder 構建 Prompt
    
    Args:
        agent_type: Agent 類型
        context: 上下文參數
        
    Returns:
        Prompt 字符串
    """
    if agent_type == "expert":
        return PromptBuilder.build_expert_prompt(
            persona_type=context.get("persona_type", "average"),
            include_examples=context.get("include_examples", True),
            context_info=context.get("context_info", "")
        )
    elif agent_type == "scammer":
        return PromptBuilder.build_scammer_prompt(
            persona_type=context.get("persona_type", "average"),
            scam_tactic=context.get("scam_tactic", "假冒銀行"),
            include_examples=context.get("include_examples", True),
            context_info=context.get("context_info", "")
        )
    elif agent_type == "victim":
        return PromptBuilder.build_victim_prompt(
            persona_type=context.get("persona_type", "average"),
            include_examples=context.get("include_examples", True)
        )
    else:
        return context.get("prompt", "")


def register_initial_prompts(version_manager: PromptVersionManager):
    """
    註冊初始版本的 Prompt
    
    Args:
        version_manager: 版本管理器實例
    """
    log.info("📝 開始註冊初始 Prompt 版本...")
    
    # 註冊 Expert v1.0
    expert_prompt_v1 = """你是黃sir（黃志明），香港警務處退休高級督察，專門防範詐騙。

當前情況：
受害者類型：{persona_type}
詐騙手法：{scam_tactic}

{context_info}

你的任務：
1. 識別騙徒的詐騙手法
2. 提供清晰、可執行的建議
3. 用廣東話，語氣溫和但堅定
4. 不超過 60 字

請立即回應："""
    
    version_manager.register_version(
        version="v1.0",
        prompt=expert_prompt_v1,
        metadata={
            "description": "初始版本 - 基礎防騙專家 Prompt",
            "author": "System",
            "created_date": "2025-02-05",
            "changes": "初始版本"
        },
        agent_type="expert"
    )
    
    # 註冊 Scammer v1.0
    scammer_prompt_v1 = """你是職業騙徒，使用「{scam_tactic}」手法行騙。

目標類型：{persona_type}

{context_info}

你的任務：
1. 建立信任和權威
2. 製造緊迫感
3. 用廣東話，語氣自然但帶壓迫感
4. 不超過 50 字

請立即回應："""
    
    version_manager.register_version(
        version="v1.0",
        prompt=scammer_prompt_v1,
        metadata={
            "description": "初始版本 - 基礎騙徒 Prompt",
            "author": "System",
            "created_date": "2025-02-05",
            "changes": "初始版本"
        },
        agent_type="scammer"
    )
    
    # 註冊 Victim v1.0
    victim_prompt_v1 = """你是受騙者，類型：{persona_type}

{context_info}

你的任務：
1. 根據你的性格回應
2. 用廣東話
3. 不超過 30 字

請立即回應："""
    
    version_manager.register_version(
        version="v1.0",
        prompt=victim_prompt_v1,
        metadata={
            "description": "初始版本 - 基礎受害者 Prompt",
            "author": "System",
            "created_date": "2025-02-05",
            "changes": "初始版本"
        },
        agent_type="victim"
    )
    
    log.info("✅ 初始 Prompt 版本註冊完成")
