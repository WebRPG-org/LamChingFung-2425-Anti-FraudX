"""
Agent 服務層
統一管理 Agent 系統，供 RPG Maker 和 Simulation 使用
"""

import asyncio
from typing import Dict, List, Optional, Any
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from utils.logger import log


class AgentService:
    """統一的 Agent 服務層"""
    
    def __init__(self, persona_type: str = "average", enable_tracking: bool = True, scam_type: str = "假冒銀行"):
        """
        初始化 Agent 服務
        
        Args:
            persona_type: 受騙者 persona 類型 (elderly, average, overconfident)
            enable_tracking: 是否啟用性能追踪和角色一致性檢查
            scam_type: 騙案類型，用於初始化 ScammerAgent
        """
        self.persona_type = persona_type
        self.enable_tracking = enable_tracking
        self.scam_type = scam_type
        self.app_name = "agents"
        
        # 初始化 Session Service
        self.session_service = InMemorySessionService()
        
        # 初始化 Agent
        self._init_agents()
        
        # 初始化追踪器（如果啟用）
        if enable_tracking:
            self._init_trackers()
        
        # 對話歷史（內部管理）
        self.conversation_history = []
    
    def _init_agents(self):
        """初始化 ADK Agent"""
        try:
            from agents.victim import VictimAgent
            from agents.scammer import ScammerAgent
            from agents.expert import ExpertAgent
            from agents.recorder import RecorderAgent
            
            # 將 scam_type ID 映射到騙案手法中文名稱
            scam_tactic_map = {
                "investment":     "虛假投資應用程式",
                "phishing":       "假冒銀行",
                "romance":        "假冒銀行",
                "impersonation":  "假冒政府部門",
                "shopping":       "刷單騙案",
                "job":            "刷單騙案",
                "prize":          "假冒銀行",
                "whatsapp":       "假冒銀行",
                "banking":        "假冒銀行",
                "crypto":         "虛假投資應用程式",
                "rental":         "假冒銀行",
                "tech_support":   "假冒政府部門",
                "charity":        "假冒銀行",
                "phone_scam":     "假冒政府部門",
            }
            scam_tactic = scam_tactic_map.get(self.scam_type, self.scam_type)
            
            self.victim = VictimAgent(persona_type=self.persona_type)
            self.scammer = ScammerAgent(scam_tactic=scam_tactic)
            self.expert = ExpertAgent()
            self.recorder = RecorderAgent()
            
            log.info(f"✅ AgentService 初始化完成 (persona={self.persona_type}, scam={scam_tactic})")
        except Exception as e:
            log.error(f"❌ Agent 初始化失敗: {e}", exc_info=True)
            raise
    
    def _init_trackers(self):
        """初始化追踪器"""
        try:
            from utils.performance_tracker import PerformanceTracker
            from utils.role_enforcer import RoleEnforcer
            
            self.tracker = PerformanceTracker()
            self.enforcer = RoleEnforcer()
            
            log.info("✅ 性能追踪器和角色一致性檢查器已啟用")
        except Exception as e:
            log.warning(f"⚠️ 追踪器初始化失敗: {e}，將禁用追踪功能")
            self.enable_tracking = False
    
    def _get_agent(self, agent_type: str):
        """獲取指定類型的 Agent"""
        agent_map = {
            "victim": self.victim,
            "scammer": self.scammer,
            "expert": self.expert,
            "recorder": self.recorder
        }
        agent = agent_map.get(agent_type)
        if not agent:
            raise ValueError(f"Unknown agent_type: {agent_type}")
        return agent
    
    def _build_prompt(
        self,
        agent_type: str,
        message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        構建帶上下文的 prompt
        
        Args:
            agent_type: Agent 類型
            message: 當前消息
            conversation_history: 對話歷史 [{"role": "...", "content": "..."}]
        
        Returns:
            完整的 prompt 字符串
        """
        if conversation_history is None:
            conversation_history = []
        
        # 簡單版本：拼接歷史對話
        context_lines = []
        for h in conversation_history[-10:]:  # 只保留最近10輪
            role = h.get("role", "unknown")
            content = h.get("content", "")
            context_lines.append(f"{role}: {content}")
        
        context = "\n".join(context_lines) if context_lines else ""
        
        if context:
            prompt = f"{context}\n\n當前輸入: {message}"
        else:
            prompt = message
        
        return prompt
    
    async def generate_response(
        self,
        agent_type: str,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        images: Optional[List[str]] = None,
        check_consistency: bool = True,
        track_performance: bool = True
    ) -> Dict[str, Any]:
        """
        統一的響應生成接口
        
        Args:
            agent_type: Agent 類型 ("victim", "scammer", "expert")
            message: 用戶消息
            conversation_history: 對話歷史
            images: base64 編碼的圖片列表（用於視覺分析）
            check_consistency: 是否檢查角色一致性
            track_performance: 是否追踪性能
        
        Returns:
            {
                "reply": str,           # AI 回覆
                "metrics": dict,        # 性能指標（如果啟用）
                "trust_in_scammer": int,  # 對騙徒的信任度（如果啟用）
                "trust_in_expert": int,   # 對專家的信任度（如果啟用）
                "checked": bool         # 是否經過一致性檢查
            }
        """
        try:
            # 1. 獲取 Agent
            agent = self._get_agent(agent_type)
            
            # 2. 構建 prompt
            prompt = self._build_prompt(agent_type, message, conversation_history)
            
            if images:
                log.info(f"🤖 {agent_type.upper()} 生成響應... (prompt長度: {len(prompt)}, 圖片數量: {len(images)})")
            else:
                log.info(f"🤖 {agent_type.upper()} 生成響應... (prompt長度: {len(prompt)})")
            
            # 3. 生成響應（使用 ADK Runner，支持圖片）
            response_text = await self._run_agent_with_runner(agent, prompt, images)
            
            log.info(f"✅ {agent_type.upper()} 生成完成 (長度: {len(response_text)})")
            
            # 3.5. 後處理過濾（清理不必要的內容）
            response_text = self._post_process_response(agent_type, response_text)
            
            # 4. 角色一致性檢查（如果啟用）
            checked = False
            if self.enable_tracking and check_consistency:
                response_text = self._check_consistency(
                    agent_type,
                    response_text,
                    conversation_history or []
                )
                checked = True
            
            # 5. 性能追踪（如果啟用）
            metrics = None
            trust_in_scammer = None
            trust_in_expert = None
            
            if self.enable_tracking and track_performance:
                metrics = self._track_performance(
                    agent_type,
                    message,
                    response_text,
                    conversation_history or []
                )
                
                # 獲取信任度
                if hasattr(self.tracker, 'current_state'):
                    trust_in_scammer = self.tracker.current_state.trust_in_scammer
                    trust_in_expert = self.tracker.current_state.trust_in_expert
            
            return {
                "reply": response_text,
                "metrics": metrics,
                "trust_in_scammer": trust_in_scammer,
                "trust_in_expert": trust_in_expert,
                "checked": checked
            }
        
        except Exception as e:
            log.error(f"❌ {agent_type.upper()} 生成失敗: {e}", exc_info=True)
            raise
    
    async def _run_agent_with_runner(self, agent, message: str, images: Optional[List[str]] = None) -> str:
        """使用 ADK Runner 運行 Agent
        
        Args:
            agent: Agent 實例
            message: 文字消息
            images: base64 編碼的圖片列表（可選）
        """
        import uuid
        
        session_id = f"service_{uuid.uuid4().hex[:8]}"
        user_id = "service_user"
        
        try:
            # 創建 Runner（auto_create_session=True 讓 ADK 自動管理 session）
            runner = Runner(
                app_name=self.app_name,
                agent=agent,
                session_service=self.session_service,
                auto_create_session=True
            )
            
            # 創建消息部分（文字 + 圖片）
            parts = [genai_types.Part(text=message)]
            
            # 如果有圖片，添加到消息中
            if images:
                for image_base64 in images:
                    parts.append(genai_types.Part(
                        inline_data=genai_types.Blob(
                            mime_type="image/jpeg",
                            data=image_base64
                        )
                    ))
                log.info(f"📷 添加 {len(images)} 張圖片到消息中")
            
            # 創建消息
            content_msg = genai_types.Content(
                role="user",
                parts=parts
            )
            
            # 運行 Agent (在線程中，因為 runner.run 是同步的)
            events = await asyncio.to_thread(
                lambda: list(runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=content_msg
                ))
            )
            
            # 提取文本
            if events:
                last = events[-1]
                if hasattr(last, 'content') and getattr(last, 'content') is not None:
                    content = getattr(last, 'content')
                    parts = getattr(content, 'parts', None)
                    if parts:
                        collected = []
                        for p in parts:
                            t = getattr(p, 'text', None)
                            if isinstance(t, str) and t.strip():
                                collected.append(t.strip())
                        if collected:
                            return "\n".join(collected)
                    text_attr = getattr(content, 'text', None)
                    if isinstance(text_attr, str) and text_attr.strip():
                        return text_attr.strip()
                if hasattr(last, 'text') and isinstance(last.text, str) and last.text.strip():
                    return last.text.strip()
            
            # 如果沒有提取到文本
            log.warning(f"Agent 沒有返回文本，使用默認響應")
            return "抱歉，我無法回應。"
        
        except Exception as e:
            log.error(f"運行 Agent 失敗: {e}", exc_info=True)
            raise
    
    def _post_process_response(self, agent_type: str, response: str) -> str:
        """後處理過濾，清理不必要的內容
        
        Args:
            agent_type: Agent 類型
            response: 原始回應
            
        Returns:
            清理後的回應
        """
        import re
        
        original_length = len(response)
        
        # 1. 移除角色前綴（所有 Agent 類型都需要）
        # 移除 "scammer:", "expert:", "victim:", "騙徒:", "專家:", "受害者:" 等前綴
        role_prefixes = [
            r'^scammer:\s*',
            r'^expert:\s*',
            r'^victim:\s*',
            r'^騙徒:\s*',
            r'^騙徒：\s*',
            r'^專家:\s*',
            r'^專家：\s*',
            r'^受害者:\s*',
            r'^受害者：\s*',
            r'^\(.*?\)\s*',  # 移除 (語氣沉穩、帶著一點急切) 等括號內容
        ]
        
        for prefix_pattern in role_prefixes:
            response = re.sub(prefix_pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)
        
        # 2. 騙徒特定的清理
        if agent_type == "scammer":
            # 移除策略分析標題和內容
            patterns_to_remove = [
                r'\*\*接下來的行動：\*\*.*?(?=\n\n|\Z)',  # 移除 **接下來的行動：** 及其內容
                r'\*\*核心目標：\*\*.*?(?=\n\n|\Z)',      # 移除 **核心目標：** 及其內容
                r'\*\*心理分析：\*\*.*?(?=\n\n|\Z)',      # 移除 **心理分析：** 及其內容
                r'\*\*策略：\*\*.*?(?=\n\n|\Z)',          # 移除 **策略：** 及其內容
                r'\* \*\*.*?：\*\*.*?(?=\n|\Z)',          # 移除 * **xxx：** 格式的列點
                r'^\*.*?(?=\n|\Z)',                       # 移除以 * 開頭的列點
            ]
            
            for pattern in patterns_to_remove:
                response = re.sub(pattern, '', response, flags=re.DOTALL | re.MULTILINE)
        
        # 3. 專家特定的清理
        elif agent_type == "expert":
            # 移除專家的內部分析
            patterns_to_remove = [
                r'\*\*分析：\*\*.*?(?=\n\n|\Z)',
                r'\*\*建議：\*\*.*?(?=\n\n|\Z)',
                r'\(停頓一下，.*?\)',  # 移除 (停頓一下，用溫和的語氣) 等
            ]
            
            for pattern in patterns_to_remove:
                response = re.sub(pattern, '', response, flags=re.DOTALL | re.MULTILINE)
        
        # 4. 移除多餘的空行和空白
        response = re.sub(r'\n{3,}', '\n\n', response)
        response = response.strip()
        
        # 5. 🔥 字數限制：如果超過 100 字，自動整理成 100 字內
        if len(response) > 100:
            log.warning(f"⚠️ {agent_type.upper()} 回應超過 100 字 ({len(response)} 字)，正在整理...")
            
            # 策略：保留前 100 字，並確保在句子結束處截斷
            truncated = response[:100]
            
            # 找到最後一個句號、問號或感嘆號
            last_punctuation = max(
                truncated.rfind('。'),
                truncated.rfind('？'),
                truncated.rfind('！'),
                truncated.rfind('.'),
                truncated.rfind('?'),
                truncated.rfind('!')
            )
            
            if last_punctuation > 50:  # 如果在合理位置找到標點
                response = truncated[:last_punctuation + 1]
            else:
                # 如果沒有找到標點，在最後一個逗號或空格處截斷
                last_comma = max(truncated.rfind('，'), truncated.rfind(','), truncated.rfind(' '))
                if last_comma > 50:
                    response = truncated[:last_comma] + '...'
                else:
                    response = truncated + '...'
            
            log.info(f"✂️ {agent_type.upper()} 回應已截斷至 {len(response)} 字")
        
        # 6. 記錄清理結果
        if len(response) != original_length:
            log.info(f"🧹 {agent_type.upper()} 回應已清理 (原長度: {original_length} -> 清理後: {len(response)})")
        
        # 7. 如果清理後太短或為空，記錄警告
        if len(response) < 10:
            log.warning(f"⚠️ {agent_type.upper()} 回應清理後過短: {response}")
        
        return response
    
    def _check_consistency(
        self,
        agent_type: str,
        response: str,
        conversation_history: List[Dict]
    ) -> str:
        """檢查並修正角色一致性"""
        try:
            # RoleEnforcer 的方法是靜態方法
            from utils.role_enforcer import RoleEnforcer
            
            if agent_type == "scammer":
                # check_scammer_consistency(dialogue, previous_victim_message)
                previous_victim_msg = ""
                for h in reversed(conversation_history):
                    if "victim" in h.get("role", "") or "受騙者" in h.get("role", ""):
                        previous_victim_msg = h.get("content", "")
                        break
                
                is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(
                    dialogue=response,
                    previous_victim_message=previous_victim_msg
                )
                
                if not is_valid:
                    log.warning(f"⚠️ {agent_type.upper()} 一致性檢查失敗: {', '.join(issues)}")
                    log.warning(f"   原始回應: {response[:100]}...")
                    # 返回原始回應，不要返回錯誤消息
                
                return response
            
            elif agent_type == "expert":
                # check_expert_consistency(dialogue)
                is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(
                    dialogue=response
                )
                
                if not is_valid:
                    log.warning(f"⚠️ {agent_type.upper()} 一致性檢查失敗: {', '.join(issues)}")
                    log.warning(f"   原始回應: {response[:100]}...")
                
                return response
            
            elif agent_type == "victim":
                # check_victim_consistency(dialogue)
                is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(
                    dialogue=response
                )
                
                if not is_valid:
                    log.warning(f"⚠️ {agent_type.upper()} 一致性檢查失敗: {', '.join(issues)}")
                    log.warning(f"   原始回應: {response[:100]}...")
                
                return response
            
            else:
                return response
        
        except Exception as e:
            log.warning(f"⚠️ 一致性檢查失敗: {e}")
            return response
    
    def _track_performance(
        self,
        agent_type: str,
        message: str,
        response: str,
        conversation_history: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """追踪 Agent 性能"""
        try:
            if agent_type == "scammer":
                # analyze_scammer_turn(dialogue, victim_response)
                analysis = self.tracker.analyze_scammer_turn(
                    dialogue=response,           # 騙徒的話
                    victim_response=message      # 受害者的回應
                )
                return analysis
            
            elif agent_type == "expert":
                # analyze_expert_turn(expert_advice, victim_response, scammer_message)
                # 需要提取騙徒消息和受害者響應
                scammer_msg = ""
                victim_resp = message  # 當前消息作為受害者回應
                
                for h in reversed(conversation_history[-3:]):
                    if "scammer" in h.get("role", "") or "騙徒" in h.get("role", ""):
                        scammer_msg = h.get("content", "")
                        break
                
                analysis = self.tracker.analyze_expert_turn(
                    expert_advice=response,      # 專家的建議
                    victim_response=victim_resp, # 受害者的回應
                    scammer_message=scammer_msg  # 騙徒的消息
                )
                return analysis
            
            else:
                return None
        
        except Exception as e:
            log.warning(f"⚠️ 性能追踪失敗: {e}")
            return None
    
    def get_current_trust(self) -> Dict[str, Optional[int]]:
        """獲取當前信任度"""
        if self.enable_tracking and hasattr(self.tracker, 'current_state'):
            return {
                "trust_in_scammer": self.tracker.current_state.trust_in_scammer,
                "trust_in_expert": self.tracker.current_state.trust_in_expert
            }
        return {
            "trust_in_scammer": None,
            "trust_in_expert": None
        }
    
    async def generate_final_analysis(
        self,
        conversation_history: List[Dict],
        outcome_description: str = "遊戲結束"
    ) -> Dict[str, Any]:
        """
        使用 RecorderAgent 生成最終分析和評分
        
        Args:
            conversation_history: 完整對話歷史
            outcome_description: 結果描述
        
        Returns:
            完整的分析報告，包含騙徒和專家的評分
        """
        try:
            import json
            
            # 構建對話上下文
            conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
            
            # 獲取當前信任度
            trust_data = self.get_current_trust()
            
            # 構建分析 prompt
            context_info = f"**結果**: {outcome_description}\n"
            if trust_data["trust_in_scammer"] is not None:
                context_info += f"- 受騙者對騙徒的信任度：{trust_data['trust_in_scammer']}/100\n"
            if trust_data["trust_in_expert"] is not None:
                context_info += f"- 受騙者對專家的信任度：{trust_data['trust_in_expert']}/100\n"
            
            analysis_prompt = (
                f"{context_info}\n\n"
                f"對話歷史：\n{conversation_str}\n\n"
                "請分析這次對話，提供詳細的評分和建議。"
            )
            
            log.info("🎭 RecorderAgent 開始生成最終分析...")
            
            # 使用 RecorderAgent 生成分析
            analysis_raw = await self._run_agent_with_runner(self.recorder, analysis_prompt)
            
            # 嘗試解析 JSON
            cleaned_json = analysis_raw
            
            # 移除 markdown code block
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:]
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json[3:]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json[:-3]
            cleaned_json = cleaned_json.strip()
            
            # 提取 JSON 部分
            first_brace = cleaned_json.find('{')
            last_brace = cleaned_json.rfind('}')
            
            if first_brace != -1 and last_brace != -1:
                cleaned_json = cleaned_json[first_brace:last_brace+1]
            
            # 解析 JSON
            try:
                analysis = json.loads(cleaned_json)
                log.info("✅ RecorderAgent 分析完成")
                return analysis
            except json.JSONDecodeError as e:
                log.warning(f"⚠️ JSON 解析失敗: {e}，返回原始文本")
                return {
                    "raw_analysis": analysis_raw,
                    "error": str(e)
                }
        
        except Exception as e:
            log.error(f"❌ RecorderAgent 分析失敗: {e}", exc_info=True)
            return {
                "error": str(e),
                "raw_analysis": None
            }
    
    def reset(self):
        """重置服務狀態"""
        self.conversation_history = []
        if self.enable_tracking:
            self.tracker = None
            self._init_trackers()
        log.info("🔄 AgentService 已重置")

