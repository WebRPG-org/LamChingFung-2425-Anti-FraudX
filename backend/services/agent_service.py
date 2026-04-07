"""
Agent 服務層 - 無 ADK 版本
統一管理 Agent 系統，供 RPG Maker 和 Simulation 使用
支持 Session 管理、對話記憶、角色隔離
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import log
from utils.scam_scoring import ScamScoring

# 全局 session 存儲（跨實例共享）
_GLOBAL_SESSIONS: Dict[str, 'ConversationSession'] = {}


class ConversationSession:
    """單個遊戲 session 的對話記憶"""
    
    def __init__(self, session_id: str, persona_type: str):
        self.session_id = session_id
        self.persona_type = persona_type
        self.created_at = datetime.now()
        self.conversation_history: List[Dict[str, str]] = []
        self.trust_in_scammer = 50  # 初始信任度
        self.trust_in_expert = 50
        self.turn_count = 0
        
        # 集成評分系統
        self.scoring = ScamScoring()
    
    def add_message(self, role: str, content: str):
        """添加消息到對話歷史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history(self, limit: int = None) -> List[Dict[str, str]]:
        """獲取對話歷史（可選限制條數）"""
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history
    
    def get_context_for_agent(self, agent_type: str, limit: int = 10) -> str:
        """為特定 Agent 構建上下文"""
        recent = self.get_history(limit)
        if not recent:
            return ""
        
        lines = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def update_scoring(self, agent_type: str, message: str, tactics_or_defenses: List[str]) -> Optional[str]:
        """
        更新評分系統
        
        Args:
            agent_type: Agent 類型 (scammer, expert, victim)
            message: 消息內容
            tactics_or_defenses: 騙術/防騙方法列表
        
        Returns:
            遊戲狀態 (None=繼續, "expert_win"=專家贏, "scammer_win"=騙徒贏)
        """
        game_status = None
        message_lower = message.lower()
        
        # 即時勝負關鍵詞
        INSTANT_SCAMMER_WIN = ["銀行密碼", "銀行戶口", "密碼", "驗證碼", "轉賬", "提供資料"]
        INSTANT_EXPERT_WIN = ["報警", "警察", "18222", "銀行號碼", "銀行帳號"]
        
        if agent_type == "scammer":
            score_increase, game_status = self.scoring.add_scammer_message(message, tactics_or_defenses)
            # 每次最高增加10分（受害者信任度）
            # 如果檢測到多個騙術，只計算最高分的那個
            if isinstance(tactics_or_defenses, list) and len(tactics_or_defenses) > 0:
                max_score = max(self.scoring.SCAMMER_TACTICS_SCORE.get(t, 0) for t in tactics_or_defenses)
                score_increase = min(10, max_score)
            else:
                score_increase = min(10, score_increase)
            
            self.trust_in_scammer = min(100, self.trust_in_scammer + score_increase)
            log.info(f"📊 騙徒信任度增加: +{score_increase}, 當前: {self.trust_in_scammer}")
            
            # 檢查騙徒是否贏了
            if self.trust_in_scammer >= 100:
                game_status = "scammer_win"
                log.warning(f"🎉 騙徒贏了！信任度達到 {self.trust_in_scammer}")
        
        elif agent_type == "expert":
            score_increase, game_status = self.scoring.add_expert_message(message, tactics_or_defenses)
            # 每次最高增加10分（專家信任度）
            # 如果檢測到多個防騙方法，只計算最高分的那個
            if isinstance(tactics_or_defenses, list) and len(tactics_or_defenses) > 0:
                max_score = max(self.scoring.EXPERT_DEFENSE_SCORE.get(d, 0) for d in tactics_or_defenses)
                score_increase = min(10, max_score)
            else:
                score_increase = min(10, score_increase)
            
            self.trust_in_expert = min(100, self.trust_in_expert + score_increase)
            # 同時降低對騙徒的信任度
            self.trust_in_scammer = max(0, self.trust_in_scammer - score_increase)
            log.info(f"📊 專家信任度增加: +{score_increase}, 當前: {self.trust_in_expert}; 騙徒信任度降低: {self.trust_in_scammer}")
            
            # 檢查專家是否贏了
            if game_status == "expert_win" or self.trust_in_expert >= 100:
                game_status = "expert_win"
                log.warning(f"🎉 專家贏了！信任度達到 {self.trust_in_expert}")
        
        elif agent_type == "victim":
            # 🔥 檢查受害者是否說出關鍵詞
            for keyword in INSTANT_SCAMMER_WIN:
                if keyword in message_lower:
                    log.warning(f"✅ 受害者說出關鍵詞 '{keyword}'，騙徒立即贏！")
                    self.trust_in_scammer = 100
                    return "scammer_win"
            
            for keyword in INSTANT_EXPERT_WIN:
                if keyword in message_lower:
                    log.warning(f"✅ 受害者說出關鍵詞 '{keyword}'，專家立即贏！")
                    self.trust_in_expert = 100
                    return "expert_win"
            
            response_type = self._infer_response_type(message)
            self.scoring.add_victim_response(message, response_type)
            # 受害者反應也最高10分
            trust_change = self.scoring.VICTIM_RESPONSE_SCORE.get(response_type, 0)
            trust_change = max(-10, min(10, trust_change))
            self.trust_in_scammer = max(0, min(100, self.trust_in_scammer + trust_change))
            log.info(f"📊 受害者反應信任度變化: {trust_change:+d}, 當前: {self.trust_in_scammer}")
        
        return game_status
    
    def _infer_response_type(self, message: str) -> str:
        """推斷受害者的反應類型"""
        message_lower = message.lower()
        
        # 完全相信
        if any(word in message_lower for word in ["好的", "馬上", "立即", "我同意", "我信"]):
            return "完全相信"
        # 有點相信
        elif any(word in message_lower for word in ["咁啊", "係咪", "真㗎", "可能"]):
            return "有點相信"
        # 猶豫
        elif any(word in message_lower for word in ["但係", "我需要", "考慮", "等等"]):
            return "猶豫"
        # 懷疑
        elif any(word in message_lower for word in ["點解", "憑咩", "唔信", "奇怪"]):
            return "懷疑"
        # 拒絕
        elif any(word in message_lower for word in ["唔好", "拒絕", "唔做", "報警"]):
            return "拒絕"
        else:
            return "猶豫"
    
    def get_game_outcome(self) -> Dict[str, Any]:
        """獲取遊戲結果"""
        return self.scoring.get_game_outcome()
    
    def get_detailed_analysis(self) -> Dict[str, Any]:
        """獲取詳細分析"""
        return self.scoring.get_detailed_analysis()


class AgentService:
    """統一的 Agent 服務層 - 無 ADK 依賴"""
    
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
        
        # 初始化 Agent
        self._init_agents()
        
        # 初始化追踪器（如果啟用）
        if enable_tracking:
            self._init_trackers()
        
        # 當前 session（會在 generate_response 時設置）
        self.current_session: Optional[ConversationSession] = None
        
        log.info(f"✅ AgentService 初始化完成 (persona={persona_type})")
    
    def _init_agents(self):
        """初始化 4 個 Agent"""
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
            self.expert = ExpertAgent(victim_persona=self.persona_type)
            self.recorder = RecorderAgent()
            
            log.info(f"✅ 4 個 Agent 初始化完成 (victim, scammer, expert, recorder)")
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
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        創建新的 session
        
        Args:
            session_id: 可選的 session ID，如果不提供則自動生成
        
        Returns:
            session_id
        """
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        session = ConversationSession(session_id, self.persona_type)
        _GLOBAL_SESSIONS[session_id] = session
        self.current_session = session
        
        log.info(f"✅ 創建新 Session: {session_id} (persona={self.persona_type})")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """獲取指定 session"""
        return _GLOBAL_SESSIONS.get(session_id)
    
    def set_current_session(self, session_id: str):
        """設置當前 session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        self.current_session = session
        log.info(f"🔄 切換到 Session: {session_id}")
    
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
    
    def _extract_tactics_from_response(self, agent_type: str, message: str) -> List[str]:
        """從回應中提取騙術或防騙方法"""
        message_lower = message.lower()
        tactics = []
        
        # 如果消息太短（少於3個字），不提取任何騙術
        if len(message) < 3:
            log.info(f"⚠️ 消息太短 ({len(message)} 字)，不提取騙術")
            return []
        
        if agent_type == "scammer":
            # 騙術特徵 - 使用更寬鬆的匹配
            scammer_tactics = {
                "製造恐慌": ["戶口", "問題", "凍結", "盜用", "危險", "緊急", "風險", "警告"],
                "權威身份": ["銀行", "警察", "政府", "官方", "職員", "部門", "機構"],
                "要求資料": ["提供", "密碼", "驗證", "帳號", "身份", "銀行卡", "資料"],
                "催促行動": ["立即", "馬上", "趕快", "現在", "時間", "急", "快"],
                "虛假收益": ["賺", "收入", "利潤", "回報", "月", "年", "投資"],
                "限時優惠": ["只有", "今天", "明天", "限時", "截止", "過期", "機會"],
                "製造信任": ["幫", "放心", "安全", "保護", "信任", "相信"],
                "反擊專家": ["騙子", "不信", "別聽", "他們"],
            }
            
            for tactic, keywords in scammer_tactics.items():
                if any(kw in message_lower for kw in keywords):
                    tactics.append(tactic)
                    log.info(f"✅ 檢測到騙術: {tactic}")
        
        elif agent_type == "expert":
            # 防騙方法 - 使用更寬鬆的匹配
            expert_defenses = {
                "識別騙局": ["詐騙", "騙局", "假", "不真實", "騙"],
                "提供證據": ["案例", "類似", "統計", "數據", "證據"],
                "官方渠道": ["電話", "官方", "正式", "官網", "渠道"],
                "停止對話": ["停止", "不要", "別", "立即", "馬上"],
                "報警建議": ["報警", "警察", "求助", "舉報"],
                "具體建議": ["不要", "別提供", "別轉", "別點", "別下載"],
            }
            
            for defense, keywords in expert_defenses.items():
                if any(kw in message_lower for kw in keywords):
                    tactics.append(defense)
                    log.info(f"✅ 檢測到防騙方法: {defense}")
        
        if not tactics:
            log.warning(f"⚠️ 未檢測到任何騙術/防騙方法 (agent={agent_type}, message_len={len(message)})")
        
        return list(set(tactics))  # 去重
    
    async def generate_response(
        self,
        agent_type: str,
        message: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        check_consistency: bool = True,
        track_performance: bool = True
    ) -> Dict[str, Any]:
        """
        統一的響應生成接口
        
        Args:
            agent_type: Agent 類型 ("victim", "scammer", "expert", "recorder")
            message: 用戶消息
            session_id: session ID（如果不提供則使用當前 session）
            check_consistency: 是否檢查角色一致性
            track_performance: 是否追踪性能
        
        Returns:
            {
                "reply": str,           # AI 回覆
                "agent": str,           # Agent 類型
                "session_id": str,      # Session ID
                "turn": int,            # 對話輪數
                "metrics": dict,        # 性能指標（如果啟用）
                "trust_in_scammer": int,  # 對騙徒的信任度
                "trust_in_expert": int,   # 對專家的信任度
            }
        """
        try:
            # 1. 確保有 session
            if session_id:
                # 如果 session 不存在，自動創建
                if session_id not in _GLOBAL_SESSIONS:
                    log.info(f"🔄 Session {session_id} 不存在，自動創建")
                    session = ConversationSession(session_id, self.persona_type)
                    _GLOBAL_SESSIONS[session_id] = session
                self.set_current_session(session_id)
            elif not self.current_session:
                session_id = self.create_session()
            else:
                session_id = self.current_session.session_id
            
            session = self.current_session
            
            # 2. 獲取 Agent
            agent = self._get_agent(agent_type)
            
            # 3. 構建帶上下文的 prompt
            context = session.get_context_for_agent(agent_type, limit=10)
            if context:
                full_prompt = f"{context}\n\n當前輸入: {message}"
            else:
                full_prompt = message
            
            # 提取語言指令（從 message 首行）並追加到 system instruction
            lang_extra = ''
            first_line = message.split('\n')[0].strip()
            if any(k in first_line for k in ['必ず日本語', 'MUST reply in English', 'reply in English', '请使用简体中文', '請使用繁體中文']):
                lang_extra = first_line
            
            log.info(f"🤖 {agent_type.upper()} 生成響應... (session={session_id}, turn={session.turn_count})")
            
            # 4. 調用 Agent 的 LLM 生成響應
            response_text = await self._call_agent_llm(agent, full_prompt, extra_system=lang_extra)
            
            log.info(f"✅ {agent_type.upper()} 生成完成 (長度: {len(response_text)})")
            
            # 5. 後處理過濾
            response_text = self._post_process_response(agent_type, response_text)
            
            log.info(f"🔍 回應內容 ({agent_type}): {response_text[:100]}...")
            
            # 6. 提取騙術/防騙方法並更新評分
            tactics = self._extract_tactics_from_response(agent_type, response_text)
            log.info(f"🎯 提取結果 ({agent_type}): {tactics}")
            
            game_status = None
            
            # 對於受害者消息，直接檢查關鍵詞（不需要提取騙術）
            if agent_type == "victim":
                game_status = session.update_scoring(agent_type, response_text, [])
            elif tactics:
                game_status = session.update_scoring(agent_type, response_text, tactics)
                log.info(f"📊 {agent_type.upper()} 評分已更新 - 騙術/防騙: {tactics}")
                log.info(f"💯 當前信任度 - 騙徒: {session.trust_in_scammer}, 專家: {session.trust_in_expert}")
                
                if game_status:
                    log.warning(f"🏁 遊戲結束！狀態: {game_status}")
            else:
                log.warning(f"⚠️ {agent_type.upper()} 未檢測到騙術/防騙方法，信任度不變")
            
            # 7. 保存到 session 記憶
            session.add_message(agent_type, response_text)
            session.turn_count += 1
            
            # 8. 角色一致性檢查（如果啟用）
            if self.enable_tracking and check_consistency:
                self._check_consistency(agent_type, response_text, session)
            
            # 9. 性能追踪（如果啟用）
            metrics = None
            if self.enable_tracking and track_performance:
                metrics = self._track_performance(agent_type, message, response_text, session)
            
            return {
                "reply": response_text,
                "agent": agent_type,
                "session_id": session_id,
                "turn": session.turn_count,
                "metrics": metrics,
                "trust_in_scammer": session.trust_in_scammer,
                "trust_in_expert": session.trust_in_expert,
                "game_status": game_status,  # 新增：遊戲狀態
            }
        
        except Exception as e:
            log.error(f"❌ {agent_type.upper()} 生成失敗: {e}", exc_info=True)
            raise
    
    async def _call_agent_llm(self, agent, prompt: str, extra_system: str = '') -> str:
        """直接調用 Agent 的 LLM
        
        Args:
            agent: Agent 實例
            prompt: 完整的 prompt（包含上下文）
            extra_system: 額外追加到 system instruction 的文字（例如語言指令）
        
        Returns:
            LLM 生成的文本
        """
        try:
            # Agent 有 model 屬性，是 VertexAILLM 實例
            if hasattr(agent, 'model') and agent.model:
                llm = agent.model
                
                # 構建完整的 system + user prompt
                system_instruction = getattr(agent, 'instruction', '')
                
                # 追加語言指令到 system instruction
                if extra_system:
                    system_instruction = system_instruction + '\n\n' + extra_system
                
                # VertexAILLM.generate() 是同步方法，用 asyncio.to_thread 包裝
                # 正確的參數順序：prompt, system_instruction, temperature, max_tokens
                response = await asyncio.to_thread(
                    llm.generate,
                    prompt,
                    system_instruction
                )
                return response if isinstance(response, str) else str(response)
            else:
                log.warning(f"Agent 沒有 model 屬性")
                return "抱歉，我無法回應。"
        
        except Exception as e:
            log.error(f"調用 LLM 失敗: {e}", exc_info=True)
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
        
        # 1. 移除角色前綴
        role_prefixes = [
            r'^scammer:\s*',
            r'^expert:\s*',
            r'^victim:\s*',
            r'^recorder:\s*',
            r'^騙徒:\s*',
            r'^騙徒：\s*',
            r'^專家:\s*',
            r'^專家：\s*',
            r'^受害者:\s*',
            r'^受害者：\s*',
            r'^\(.*?\)\s*',
        ]
        
        for prefix_pattern in role_prefixes:
            response = re.sub(prefix_pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)
        
        # 2. 騙徒特定的清理
        if agent_type == "scammer":
            patterns_to_remove = [
                r'\*\*接下來的行動：\*\*.*?(?=\n\n|\Z)',
                r'\*\*核心目標：\*\*.*?(?=\n\n|\Z)',
                r'\*\*心理分析：\*\*.*?(?=\n\n|\Z)',
                r'\*\*策略：\*\*.*?(?=\n\n|\Z)',
                r'\* \*\*.*?：\*\*.*?(?=\n|\Z)',
                r'^\*.*?(?=\n|\Z)',
            ]
            
            for pattern in patterns_to_remove:
                response = re.sub(pattern, '', response, flags=re.DOTALL | re.MULTILINE)
        
        # 3. 專家特定的清理
        elif agent_type == "expert":
            patterns_to_remove = [
                r'\*\*分析：\*\*.*?(?=\n\n|\Z)',
                r'\*\*建議：\*\*.*?(?=\n\n|\Z)',
                r'\(停頓一下，.*?\)',
            ]
            
            for pattern in patterns_to_remove:
                response = re.sub(pattern, '', response, flags=re.DOTALL | re.MULTILINE)
        
        # 4. 移除多餘的空行
        response = re.sub(r'\n{3,}', '\n\n', response)
        response = response.strip()
        
        # 5. 字數限制：超過 80 字自動截斷
        if len(response) > 80:
            log.warning(f"⚠️ {agent_type.upper()} 回應超過 80 字 ({len(response)} 字)，正在整理...")
            
            truncated = response[:80]
            
            # 找到最後一個句號
            last_punctuation = max(
                truncated.rfind('。'),
                truncated.rfind('？'),
                truncated.rfind('！'),
                truncated.rfind('.'),
                truncated.rfind('?'),
                truncated.rfind('!')
            )
            
            if last_punctuation > 40:
                response = truncated[:last_punctuation + 1]
            else:
                last_comma = max(truncated.rfind('，'), truncated.rfind(','), truncated.rfind(' '))
                if last_comma > 40:
                    response = truncated[:last_comma] + '...'
                else:
                    response = truncated + '...'
            
            log.info(f"✂️ {agent_type.upper()} 回應已截斷至 {len(response)} 字")
        
        if len(response) != original_length:
            log.info(f"🧹 {agent_type.upper()} 回應已清理 (原長度: {original_length} -> 清理後: {len(response)})")
        
        return response
    
    def _check_consistency(self, agent_type: str, response: str, session: ConversationSession):
        """檢查角色一致性"""
        try:
            from utils.role_enforcer import RoleEnforcer
            
            if agent_type == "scammer":
                is_valid, error_msg, issues = RoleEnforcer.check_scammer_consistency(
                    dialogue=response,
                    previous_victim_message=""
                )
                if not is_valid:
                    log.warning(f"⚠️ Scammer 一致性檢查失敗: {', '.join(issues)}")
            
            elif agent_type == "expert":
                is_valid, error_msg, issues = RoleEnforcer.check_expert_consistency(
                    dialogue=response
                )
                if not is_valid:
                    log.warning(f"⚠️ Expert 一致性檢查失敗: {', '.join(issues)}")
            
            elif agent_type == "victim":
                is_valid, error_msg, issues = RoleEnforcer.check_victim_consistency(
                    dialogue=response
                )
                if not is_valid:
                    log.warning(f"⚠️ Victim 一致性檢查失敗: {', '.join(issues)}")
        
        except Exception as e:
            log.warning(f"⚠️ 一致性檢查失敗: {e}")
    
    def _track_performance(self, agent_type: str, message: str, response: str, session: ConversationSession) -> Optional[Dict[str, Any]]:
        """追踪 Agent 性能"""
        try:
            if agent_type == "scammer":
                analysis = self.tracker.analyze_scammer_turn(
                    dialogue=response,
                    victim_response=message
                )
                return analysis
            
            elif agent_type == "expert":
                analysis = self.tracker.analyze_expert_turn(
                    expert_advice=response,
                    victim_response=message,
                    scammer_message=""
                )
                return analysis
            
            else:
                return None
        
        except Exception as e:
            log.warning(f"⚠️ 性能追踪失敗: {e}")
            return None
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """獲取 session 的完整對話歷史"""
        session = self.get_session(session_id)
        if not session:
            return []
        return session.get_history()
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """獲取 session 的統計信息"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "persona_type": session.persona_type,
            "created_at": session.created_at.isoformat(),
            "turn_count": session.turn_count,
            "message_count": len(session.conversation_history),
            "trust_in_scammer": session.trust_in_scammer,
            "trust_in_expert": session.trust_in_expert,
        }
    
    def reset(self):
        """重置服務狀態"""
        self.current_session = None
        if self.enable_tracking:
            self.tracker = None
            self._init_trackers()
        log.info("🔄 AgentService 已重置")
    
    async def generate_parallel_responses(
        self,
        victim_message: str,
        session_id: Optional[str] = None,
        mode: str = "full"
    ) -> Dict[str, Any]:
        """
        🔥 並行生成三個 Agent 的回應
        
        Args:
            victim_message: 受害者的消息
            session_id: session ID
            mode: 生成模式
                - "full": 生成所有三個 Agent 的回應（騙徒、專家、受害者）
                - "expert_only": 只生成專家回應
                - "scammer_only": 只生成騙徒回應
        
        Returns:
            {
                "scammer_response": {...},
                "expert_response": {...},
                "victim_response": {...},
                "timestamp": "...",
                "execution_time_ms": 123
            }
        """
        import time
        start_time = time.time()
        
        try:
            # 確保有 session
            if session_id:
                if session_id not in _GLOBAL_SESSIONS:
                    session = ConversationSession(session_id, self.persona_type)
                    _GLOBAL_SESSIONS[session_id] = session
                self.set_current_session(session_id)
            elif not self.current_session:
                session_id = self.create_session()
            else:
                session_id = self.current_session.session_id
            
            log.info(f"🚀 開始並行生成回應 (mode={mode}, session={session_id})")
            
            # 根據模式決定要生成的 Agent
            tasks = []
            agent_types = []
            
            if mode in ["full", "scammer_only"]:
                tasks.append(self.generate_response("scammer", victim_message, session_id))
                agent_types.append("scammer")
            
            if mode in ["full", "expert_only"]:
                tasks.append(self.generate_response("expert", victim_message, session_id))
                agent_types.append("expert")
            
            if mode == "full":
                tasks.append(self.generate_response("victim", victim_message, session_id))
                agent_types.append("victim")
            
            # 🔥 並行執行所有任務
            log.info(f"⚡ 並行執行 {len(tasks)} 個任務...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            response_dict = {}
            for agent_type, result in zip(agent_types, results):
                if isinstance(result, Exception):
                    log.error(f"❌ {agent_type.upper()} 生成失敗: {result}")
                    response_dict[f"{agent_type}_response"] = {
                        "error": str(result),
                        "agent": agent_type
                    }
                else:
                    response_dict[f"{agent_type}_response"] = result
            
            execution_time = (time.time() - start_time) * 1000
            
            log.info(f"✅ 並行生成完成 (耗時: {execution_time:.1f}ms)")
            
            return {
                **response_dict,
                "timestamp": datetime.now().isoformat(),
                "execution_time_ms": round(execution_time, 1),
                "session_id": session_id,
                "mode": mode
            }
        
        except Exception as e:
            log.error(f"❌ 並行生成失敗: {e}", exc_info=True)
            raise
    
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
            完整的分析報告
        """
        try:
            import json
            
            # 構建對話上下文
            conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
            
            # 構建分析 prompt
            analysis_prompt = (
                f"**結果**: {outcome_description}\n\n"
                f"對話歷史：\n{conversation_str}\n\n"
                "請分析這次對話，提供詳細的評分和建議。"
            )
            
            log.info("🎭 RecorderAgent 開始生成最終分析...")
            
            # 使用 RecorderAgent 生成分析
            analysis_raw = await self._call_agent_llm(self.recorder, analysis_prompt)
            
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

