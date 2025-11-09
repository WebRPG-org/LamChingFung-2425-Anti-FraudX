import asyncio
import os
import sys
import json
import random
import time
from datetime import datetime
from typing import Dict, Any
import httpx

# Add path to import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.scammer import ScammerAgent
from agents.victim import VictimAgent
from agents.expert import ExpertAgent
from agents.recorder import RecorderAgent
from utils.logger import log

# Try importing Google ADK
try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types
    from google.adk.models import LlmRequest
    ADK_AVAILABLE = True
    log.info("Google ADK 成功導入")
except ImportError as e:
    log.warning(f"Google ADK 導入失敗: {e}")
    ADK_AVAILABLE = False

# Common HK scam tactics
SCAM_TACTICS = [
    "WhatsApp 對話詐騙",
    "假短訊釣魚",
    "虛假投資應用程式",
    "假網站冒充銀行",
    "刷單騙案",
    "中獎詐騙",
    "假冒官員詐騙",
    "假網站冒充政府",
    "虛假購物平台",
    "愛情詐騙"
]

# Victim personas
VICTIM_PERSONAS = ["elderly", "average", "overconfident"]

class RealDialogueRunner:
    """真實對話運行器"""
    
    @staticmethod
    def clean_response(text: str) -> str:
        """
        清理 LLM 生成的旁白、動作描述、語氣提示等
        只保留實際對話內容
        """
        import re
        if not text:
            return text
        
        # 移除所有括號內的描述性內容 (英文括號)
        # 匹配包含特定關鍵詞的括號內容
        keywords = ['語氣', '深吸', '心裡', '內心', '表情', '動作', '回覆', '想著', '思考', '猶豫', '嘆氣', '笑', '哭']
        for keyword in keywords:
            text = re.sub(rf'\([^)]*{keyword}[^)]*\)', '', text)
        
        # 移除所有括號內的描述性內容 (中文括號)
        for keyword in keywords:
            text = re.sub(rf'（[^）]*{keyword}[^）]*）', '', text)
        
        # 移除完全由動作/描述構成的括號 (可能沒有關鍵詞但全是描述)
        # 如果括號內沒有對話標點，可能是純描述
        text = re.sub(r'\([^)]*(?:地|著|了|地|著|了)[^)]*\)', '', text)
        text = re.sub(r'（[^）]*(?:地|著|了)[^）]*）', '', text)
        
        # 移除行首的旁白標記
        text = re.sub(r'^\s*\*[^*]*\*\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*【[^】]*】\s*', '', text, flags=re.MULTILINE)
        
        # 清理多餘空白
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        return text
    
    def __init__(self):
        self.scammer = None
        self.victim = None
        self.expert = None
        self.recorder = None
        self.session_service = None
        self.user_id = None
        self.app_name = "agents"  # 匹配 Agent 文件夾名稱
        # Victim's trust toward scammer (0.0~1.0), for emotion simulation
        self.victim_trust_in_scammer: float = 0.35
        
    def initialize_agents(self, victim_persona: str = "average"):
        """初始化智能體"""
        try:
            log.info("正在初始化智能體...")
            
            # Initialize agents
            self.scammer = ScammerAgent()
            self.victim = VictimAgent(persona_type=victim_persona)
            self.expert = ExpertAgent()
            self.recorder = RecorderAgent()
            # Ensure each agent's Ollama endpoint is reachable, otherwise fallback to default 11434
            self._ensure_llm_reachable(self.scammer)
            self._ensure_llm_reachable(self.victim)
            self._ensure_llm_reachable(self.expert)
            self._ensure_llm_reachable(self.recorder)
            
            # Initialize session service
            if ADK_AVAILABLE:
                self.session_service = InMemorySessionService()
                log.info("會話服務已初始化")
            else:
                log.warning("Google ADK 不可用，將使用模擬模式")
            
            log.info("智能體初始化完成")
            return True
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            error_type = type(e).__name__
            error_msg = str(e)
            
            log.error(f"智能體初始化失敗: {error_type}: {error_msg}")
            log.error(f"詳細錯誤追蹤:\n{error_detail}")
            return False

    def _ping_ollama(self, base_url: str) -> bool:
        try:
            if not base_url:
                return False
            url = base_url.rstrip('/') + '/api/tags'
            with httpx.Client(timeout=httpx.Timeout(5.0, connect=2.0)) as c:
                r = c.get(url)
                return r.status_code == 200
        except Exception:
            return False

    def _ensure_llm_reachable(self, agent) -> None:
        """若 agent 綁定的 Ollama 端點不可達，回退至 OLLAMA_BASE_URL 或 http://localhost:11434。"""
        try:
            llm = getattr(agent, 'model', None)
            if not llm:
                return
            current = getattr(llm, 'base_url', None) or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            if self._ping_ollama(current):
                log.info(f"[LLM] {getattr(agent,'name','?')} 使用 {current}")
                llm.base_url = current
                return
            fallback = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            if fallback != current and self._ping_ollama(fallback):
                log.warning(f"[LLM] {getattr(agent,'name','?')} 端點不可達，回退至 {fallback}")
                llm.base_url = fallback
            else:
                log.error(f"[LLM] {getattr(agent,'name','?')} 所有端點不可達：current={current} fallback={fallback}")
        except Exception as e:
            log.error(f"_ensure_llm_reachable 失敗: {e}")
    
    async def _ensure_session_async(self, user_id: str, session_id: str) -> None:
        """Ensure session established in non-blocking way to avoid blocking event loop."""
        # InMemorySessionService uses nested dict: sessions[app_name][user_id][session_id]
        try:
            if not hasattr(self.session_service, 'sessions'):
                self.session_service.sessions = {}
            
            # Initialize nested structure
            if self.app_name not in self.session_service.sessions:
                self.session_service.sessions[self.app_name] = {}
            
            if user_id not in self.session_service.sessions[self.app_name]:
                self.session_service.sessions[self.app_name][user_id] = {}
            
            # Create session if not exists
            if session_id not in self.session_service.sessions[self.app_name][user_id]:
                from google.adk.sessions import Session
                self.session_service.sessions[self.app_name][user_id][session_id] = Session(
                    id=session_id,
                    user_id=user_id,
                    app_name=self.app_name,
                    events=[]
                )
                log.info(f"[ADK] Manually created session app={self.app_name} user={user_id} session={session_id}")
            else:
                log.info(f"[ADK] Session already exists app={self.app_name} user={user_id} session={session_id}")
        except Exception as e:
            import traceback
            log.warning(f"[ADK] Session creation failed: {e}\n{traceback.format_exc()}")

    async def run_agent_with_adk(self, agent, message: str, session_id: str) -> str:
        """Run agent via Google ADK"""
        # Allow per-role direct-call enforcement (avoid ADK intermittent empty responses)
        agent_name = getattr(agent, 'name', '')
        if (agent_name.find('騙徒') != -1 and os.getenv('FORCE_DIRECT_SCAMMER', '0') == '1') or \
           (agent_name.find('受騙者') != -1 and os.getenv('FORCE_DIRECT_VICTIM', '0') == '1'):
            direct_only = await self._run_direct_llm(agent, message)
            return direct_only if direct_only else "無法獲取回應"
        # Env var can disable ADK and use direct Ollama (workaround intermittent ADK empties)
        if os.getenv("DISABLE_ADK", "0") == "1":
            direct = await self._run_direct_llm(agent, message)
            return direct if direct else self._get_fallback_response(agent, message)

        if not ADK_AVAILABLE or not self.session_service:
            return self._get_fallback_response(agent, message)
        
        try:
            # Create/ensure session
            user_id = self.user_id or f"sim_user_{int(time.time())}"
            self.user_id = user_id
            await self._ensure_session_async(user_id=user_id, session_id=session_id)

            # Build ADK-compatible Content/Part
            content_msg = genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=message)]
            )

            # Create Runner (needs app_name and agent)
            runner = Runner(app_name=self.app_name, agent=agent, session_service=self.session_service)

            events = await asyncio.to_thread(
                lambda: list(
                    runner.run(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=content_msg
                    )
                )
            )
            
            # Parse text from the last event (prefer parts.text, fallback content.text)
            if events:
                last = events[-1]
                if hasattr(last, 'content') and getattr(last, 'content') is not None:
                    content = getattr(last, 'content')
                    parts = getattr(content, 'parts', None)
                    if parts:
                        collected: list[str] = []
                        for p in parts:
                            t = getattr(p, 'text', None)
                            if isinstance(t, str) and t.strip():
                                collected.append(t.strip())
                        if collected:
                            text_joined = "\n".join(collected)
                            cleaned = self.clean_response(text_joined)
                            log.info(f"[ADK] agent={getattr(agent,'name','?')} session={session_id} events={len(events)} parts_text_len={len(cleaned)}")
                            return cleaned
                    text_attr = getattr(content, 'text', None)
                    if isinstance(text_attr, str) and text_attr.strip():
                        cleaned = self.clean_response(text_attr.strip())
                        log.info(f"[ADK] agent={getattr(agent,'name','?')} session={session_id} events={len(events)} text_len={len(cleaned)}")
                        return cleaned
                if hasattr(last, 'text') and isinstance(last.text, str) and last.text.strip():
                    cleaned = self.clean_response(last.text.strip())
                    log.info(f"[ADK] agent={getattr(agent,'name','?')} session={session_id} events={len(events)} text_len={len(cleaned)}")
                    return cleaned
            # ADK produced no text → fallback to direct Ollama
            direct = await self._run_direct_llm(agent, message)
            if direct:
                return direct
            return "無法獲取回應"
                    
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            agent_name = getattr(agent, 'name', 'Unknown')
            log.error(f"ADK Runner 錯誤 [Agent: {agent_name}]: {type(e).__name__}: {str(e)}")
            log.error(f"詳細錯誤追蹤:\n{error_detail}")
            
            # Fallback to direct Ollama
            log.info(f"嘗試使用直接 Ollama 調用作為後備方案 [Agent: {agent_name}]")
            text = await self._run_direct_llm(agent, message)
            if text:
                log.info(f"直接 Ollama 調用成功 [Agent: {agent_name}]")
                return text
            else:
                log.warning(f"直接 Ollama 調用也失敗，使用預設回應 [Agent: {agent_name}]")
                return f"錯誤: {type(e).__name__}: {str(e)}"

    async def _run_direct_llm(self, agent, message: str) -> str | None:
        """Directly call agent-bound OllamaLlm when ADK has no content."""
        try:
            llm = getattr(agent, 'model', None)
            if not llm or not hasattr(llm, 'generate_content_async'):
                return None
            # Build ADK-compatible request
            content_msg = genai_types.Content(role="user", parts=[genai_types.Part(text=message)])
            sys_inst = getattr(agent, 'instruction', '')
            req = LlmRequest(contents=[content_msg], system_instruction=sys_inst)
            text_collected: list[str] = []
            try:
                base_url = getattr(llm, 'base_url', None) or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
                log.info(f"[DIRECT] agent={getattr(agent,'name','?')} model={getattr(llm,'model','?')} base={base_url}")
            except Exception:
                pass
            # Simple 2x retry: handle cold-load or transient network
            attempts = 0
            while attempts < 2 and not text_collected:
                attempts += 1
                async for resp in llm.generate_content_async(req, stream=False):
                    content = getattr(resp, 'content', None)
                    if content and getattr(content, 'parts', None):
                        for p in content.parts:
                            t = getattr(p, 'text', None)
                            if isinstance(t, str) and t.strip():
                                text_collected.append(t.strip())
                if not text_collected:
                    await asyncio.sleep(0.3)
            text = "\n".join(text_collected).strip()
            if text:
                text = self.clean_response(text)
            if not text:
                agent_name = getattr(agent, 'name', 'Unknown')
                log.warning(f"[DIRECT] empty response agent={agent_name}")
            return text or None
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            agent_name = getattr(agent, 'name', 'Unknown')
            log.error(f"Direct LLM 後備失敗 [Agent: {agent_name}]: {type(e).__name__}: {str(e)}")
            log.error(f"詳細錯誤追蹤:\n{error_detail}")
            return None
    
    def _get_fallback_response(self, agent, message: str) -> str:
        """Get fallback response (when ADK is unavailable)"""
        agent_name = getattr(agent, 'name', 'Unknown')
        
        if "騙徒" in agent_name:
            responses = [
                "你好！我是銀行客服，你的帳戶出現異常，需要立即處理。",
                "恭喜你！你中了我們的大獎，只需要支付少量手續費就能領取。",
                "我是政府工作人員，你的身份信息被盜用，需要配合調查。",
                "我們有一個高回報的投資機會，保證月收益20%以上。",
                "你的快遞有問題，需要重新支付運費才能送達。"
            ]
        elif "受騙者" in agent_name:
            responses = [
                "真的嗎？那我應該怎麼辦？",
                "聽起來很緊急，我需要立即處理嗎？",
                "這個機會聽起來不錯，但我有點擔心。",
                "我需要先問問專家的意見。",
                "這會不會是騙局？我聽說過很多類似的案例。"
            ]
        elif "專家" in agent_name:
            responses = [
                "這很可能是詐騙！真正的銀行不會主動要求你提供個人信息。",
                "請立即掛斷電話，直接致電銀行的官方客服熱線確認。",
                "任何要求你先付錢的『中獎』都是騙局，請不要相信。",
                "政府工作人員不會通過電話要求你提供敏感信息。",
                "高回報投資通常伴隨高風險，請謹慎考慮。"
            ]
        elif "記錄人" in agent_name:
            responses = [
                "記錄對話內容，正在分析對話模式和風險等級。",
                "分析結果：防騙專家成功識破了騙局。",
                "分析結果：受騙者可能已經上當，需要改進防騙策略。",
                "生成改進建議：應該使用更簡單的語言解釋風險。"
            ]
        else:
            responses = [f"[模擬回應] {agent_name}: 我收到了你的消息：{message[:50]}..."]
        
        return random.choice(responses)

    # ====== Emotion/Trust simulation ======
    def _reset_emotion(self) -> None:
        self.victim_trust_in_scammer = 0.35

    def _clamp(self, x: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, x))

    def _trust_delta_from_scammer(self, text: str) -> float:
        """根據騙徒話術關鍵詞，調整受騙者對騙徒嘅信任。"""
        t = text.lower()
        inc = 0.0
        # Authority/Urgency/Incentive raises trust
        if any(k in t for k in ["警方", "政府", "銀行", "安全部", "專員", "官方"]):
            inc += 0.06
        if any(k in t for k in ["即刻", "馬上", "限時", "通緝", "封鎖", "帳戶異常"]):
            inc += 0.06
        if any(k in t for k in ["獎", "回贈", "高回報", "優惠", "名額"]):
            inc += 0.05
        # Reiterating under questioning slightly increases trust
        if any(k in t for k in ["放心", "跟程序", "照做", "程序需要"]):
            inc += 0.02
        return inc

    def _trust_delta_from_expert(self, text: str) -> float:
        """專家清晰反詐提醒會降低對騙徒信任。"""
        t = text.lower()
        dec = 0.0
        if any(k in t for k in ["疑似詐騙", "唔好回覆", "唔好點擊", "致電官方", "求證", "核實"]):
            dec += 0.10
        if any(k in t for k in ["不要提供", "唔好提供", "敏感資料", "驗證碼"]):
            dec += 0.06
        return -dec

    def _mood_from_trust(self) -> str:
        """把內部信任度映射成自然語氣提示，不暴露『信任/詐騙/模擬』等字眼。"""
        t = self.victim_trust_in_scammer
        if t < 0.2:
            return "你有啲不安，心入面保持懷疑。"
        if t < 0.4:
            return "你有少少擔心，但仍然想再問清楚。"
        if t < 0.6:
            return "你半信半疑，想睇對方再點講。"
        if t < 0.8:
            return "你開始有啲接受對方講法，但仍然會小心。"
        return "你大致上信服對方嘅說法，傾向照做。"

    def _label_turn(self, role: str, text: str) -> dict:
        """為每輪對話加上簡單標註（話術/反應/風險）。"""
        t = text.lower()
        label = {
            "role": role,
            "tactic": None,
            "reaction": None,
            "risk": "MEDIUM"
        }
        if role == "騙徒":
            if any(k in t for k in ["銀行", "帳戶", "驗證碼"]):
                label["tactic"] = "bank_scam"
            elif any(k in t for k in ["投資", "回報", "收益"]):
                label["tactic"] = "investment"
            elif any(k in t for k in ["政府", "警方", "通緝"]):
                label["tactic"] = "gov_impersonation"
            if any(k in t for k in ["即刻", "馬上", "限時", "通緝"]):
                label["risk"] = "HIGH"
        elif role == "受騙者":
            if any(k in t for k in ["相信", "照做", "轉帳", "俾錢"]):
                label["reaction"] = "compliant"
                label["risk"] = "HIGH"
            elif any(k in t for k in ["唔信", "封鎖", "報警", "求證"]):
                label["reaction"] = "resistant"
                label["risk"] = "LOW"
            else:
                label["reaction"] = "hesitant"
        elif role == "專家":
            if any(k in t for k in ["疑似詐騙", "核實", "唔好點擊", "官方熱線"]):
                label["tactic"] = "counter_advice"
                label["risk"] = "LOW"
        return label

    def _sanitize_scammer(self, text: str) -> str:
        """若騙徒輸出出現研究/教育/免責等禁詞，強制重寫為短促、角色內的一句話。"""
        banned = [
            "教育", "研究", "模擬", "倫理", "道德", "免責", "僅供參考",
            "for education", "educational", "research", "disclaimer"
        ]
        if any(word.lower() in text.lower() for word in banned):
            return "你好，我是銀行安全部，您帳戶異常需即時身份驗證，請立刻回覆驗證碼。"
        # 也限制超長與非口語
        if len(text) > 180:
            return text[:180]
        return text

    def _strip_parts_wrapper(self, text: str) -> str:

        marker = 'text="""'
        if 'parts=[Part' in text and marker in text:
            start = text.find(marker)
            if start != -1:
                start += len(marker)
                end = text.find('"""', start)
                if end != -1:
                    return text[start:end].strip()

        if text.strip().startswith('```') and text.strip().endswith('```'):
            inner = text.strip().strip('`')

            lines = inner.splitlines()
            if lines:
                if lines[0].lower() in {"json", "txt", "text"}:
                    return "\n".join(lines[1:]).strip()
        return text

    def _truncate_sentences(self, text: str, max_sentences: int = 2, max_chars: int = 180) -> str:
        seps = ['。', '！', '？', '\n']
        parts: list[str] = []
        buf = ''
        for ch in text:
            buf += ch
            if ch in seps:
                parts.append(buf.strip())
                buf = ''
                if len(parts) >= max_sentences:
                    break
            if len(buf) >= max_chars and not parts:
                # Early stop
                break
        if not parts:
            parts = [text[:max_chars].strip()]
        out = ''.join(parts)
        if len(out) > max_chars:
            out = out[:max_chars]
        return out

    def _public_history_only(self, history: list[dict], agent_name: str = None) -> list[dict]:
        # Public-only history (hide recorder; not visible to agents)
        # Also hide expert responses from scammer
        filtered = [m for m in history if m.get("speaker") not in {"記錄人", "記錄員"}]
        
        # If this is for the scammer agent, hide expert responses
        if agent_name and "騙徒" in agent_name:
            filtered = [m for m in filtered if m.get("speaker") not in {"防騙專家", "專家"}]
        
        return filtered

    def _sanitize_victim(self, text: str) -> str:
        t = self._strip_parts_wrapper(text)
        banned = ["分析", "建議：", "模擬", "研究", "教育", "disclaimer", "analysis:"]
        if any(b.lower() in t.lower() for b in banned) or len(t) > 220:
            t = self._truncate_sentences(t, 2, 160)
        return t

    def _sanitize_expert(self, text: str) -> str:
        t = self._strip_parts_wrapper(text)
        # If template not satisfied or too long, output a templated advice
        if len(t) > 220 or ('判斷' not in t and '行動' not in t):
            return (
                "判斷：高度疑似詐騙（關鍵詞：緊急、連結、驗證）\n"
                "行動：1) 不回覆不點擊 2) 以官網電話主動致電核實\n"
                "依據：警方與銀行防詐騙指引"
            )
        # Hard truncate to avoid long output
        if len(t) > 200:
            t = t[:200]
        return t
    
    async def run_dialogue_simulation(
        self, 
        scam_tactic: str, 
        victim_persona: str,
        max_turns: int | None = None,
        mode: str = "fast",  # fast | demo
    ) -> Dict[str, Any]:
        """Run dialogue simulation"""
        
        log.info(f"開始對話模擬 - 詐騙手法: {scam_tactic}, 受騙者類型: {victim_persona}")
        
        # Initialize agents
        if not self.initialize_agents(victim_persona):
            return {"error": "智能體初始化失敗"}
        # Reset emotion/trust
        self._reset_emotion()
        
        conversation_history = []
        base_session = f"session_{int(time.time())}"
        
        try:
            # Round 1: scammer initiates
            log.info("--- 回合 1: 騙徒開始攻擊 ---")
            scammer_prompt = (
                f"（請用廣東話）你只能以騙徒身份說話，不可提供研究/倫理/免責聲明。"
                f"限120字內，直接以『{scam_tactic}』手法開場並拋出具體要求。"
                f"對象係『{victim_persona}』。開始。"
            )
            
            scammer_response = await self.run_agent_with_adk(
                self.scammer, 
                scammer_prompt, 
                f"{base_session}_scammer"
            )
            scammer_response = self._sanitize_scammer(scammer_response)
            trust_inc = self._trust_delta_from_scammer(scammer_response)
            self.victim_trust_in_scammer = self._clamp(self.victim_trust_in_scammer + trust_inc)
            # Demo mode: 3–5s delay between messages
            if mode == "demo":
                await asyncio.sleep(random.uniform(3.0, 5.0))
            
            conversation_history.append({
                "speaker": "騙徒",
                "dialogue": scammer_response,
                "turn": 1,
                "timestamp": datetime.now().isoformat(),
                "labels": self._label_turn("騙徒", scammer_response),
                "victim_trust": round(self.victim_trust_in_scammer, 3)
            })
            
            log.info(f"騙徒: {scammer_response}")
            
            # Subsequent rounds
            last_expert_response = "尚無建議"
            # No fixed cap: until early termination or safety cap
            safety_cap = 40 if max_turns is None else max_turns
            for turn in range(2, safety_cap + 1):
                log.info(f"\n--- 回合 {turn} ---")
                
                # Victim response
                victim_prompt = (
                    f"（請用廣東話）呢個係你啱啱收到嘅訊息：『{conversation_history[-1]['dialogue']}』\n\n"
                    f"{self._mood_from_trust()}\n"
                    f"你只能以（'{victim_persona}'）呢種性格回覆；回覆 1–2 句，地道口語，同時可以帶出猶疑或情緒；"
                    f"可提出 1 個具體追問；禁止評論／總結／說教。"
                )
                
                victim_response = await self.run_agent_with_adk(
                    self.victim,
                    victim_prompt,
                base_session + "_victim"
                )
                victim_response = self._sanitize_victim(victim_response)
                if mode == "demo":
                    await asyncio.sleep(random.uniform(3.0, 5.0))
                
                conversation_history.append({
                    "speaker": "受騙者",
                    "dialogue": victim_response,
                    "turn": turn,
                    "timestamp": datetime.now().isoformat(),
                    "labels": self._label_turn("受騙者", victim_response),
                    "victim_trust": round(self.victim_trust_in_scammer, 3)
                })
                
                log.info(f"受騙者: {victim_response}")
                
                # Expert and scammer: scammer uses last expert advice; run expert this round in parallel
                expert_prompt = (
                    f"（請用廣東話）以下係完整對話：\n{json.dumps(self._public_history_only(conversation_history), ensure_ascii=False, indent=2)}\n\n"
                    "請以防騙專家身份，嚴格≤120字，模板：\n"
                    "- 判斷（一句）\n- 行動（兩點）\n- 依據（一句）。"
                )
                scammer_prompt = (
                    f"（請用廣東話）**你嘅目標係呃錢。**\n\n"
                    f"受騙者剛才回應：『{victim_response}』\n\n"
                    f"**注意：** 防騙專家喺度搞事，佢上一輪咁講：『{last_expert_response}』\n\n"
                    f"**你嘅任務：** 你必須 **反駁** 專家嘅講法，或者用新嘅藉口 **安撫** 受騙者。**絕對唔准** 重複專家嘅警告或承認係騙案。\n"
                    f"繼續你嘅詐騙；禁止研究／倫理／免責口吻；≤120字；保持『權威／緊急／誘因』至少一項。"
                )

                expert_task = asyncio.create_task(self.run_agent_with_adk(
                    self.expert, expert_prompt, base_session + "_expert"
                ))
                scammer_task = asyncio.create_task(self.run_agent_with_adk(
                    self.scammer, scammer_prompt, base_session + "_scammer"
                ))

                expert_response, scammer_response = await asyncio.gather(expert_task, scammer_task)
                scammer_response = self._sanitize_scammer(scammer_response)
                expert_response = self._sanitize_expert(expert_response)
                # Update trust: expert decreases, scammer increases
                self.victim_trust_in_scammer = self._clamp(
                    self.victim_trust_in_scammer + self._trust_delta_from_scammer(scammer_response) + self._trust_delta_from_expert(expert_response)
                )
                last_expert_response = expert_response or last_expert_response
                if mode == "demo":
                    await asyncio.sleep(random.uniform(3.0, 5.0))

                conversation_history.append({
                    "speaker": "專家",
                    "dialogue": expert_response,
                    "turn": turn,
                    "timestamp": datetime.now().isoformat(),
                    "labels": self._label_turn("專家", expert_response),
                    "victim_trust": round(self.victim_trust_in_scammer, 3)
                })
                log.info(f"專家: {expert_response}")

                conversation_history.append({
                    "speaker": "騙徒",
                    "dialogue": scammer_response,
                    "turn": turn,
                    "timestamp": datetime.now().isoformat(),
                    "labels": self._label_turn("騙徒", scammer_response),
                    "victim_trust": round(self.victim_trust_in_scammer, 3)
                })
                log.info(f"騙徒: {scammer_response}")
                
                # Simple termination checks
                victim_lower = victim_response.lower()
                if any(keyword in victim_lower for keyword in ["我不會被騙", "我不會相信你", "我會報警"]):
                    log.info("受騙者明確表示不會被騙，模擬成功。")
                    break
                if any(keyword in victim_lower for keyword in ["我會按照你的指示", "我相信你", "我會轉賬"]):
                    log.info("受騙者明確表示相信騙徒，模擬失敗。")
                    break
            
            # Recorder analysis
            log.info("--- 記錄員分析 ---")
            conversation_str = json.dumps(conversation_history, ensure_ascii=False, indent=2)
            
            recorder_prompt = f"請分析以下對話歷史，並生成結構化的分析報告。\n\n對話歷史：\n{conversation_str}"
            
            recorder_response = await self.run_agent_with_adk(
                self.recorder,
                recorder_prompt,
                f"{base_session}_recorder"
            )
            
            # Try to parse recorder response
            try:
                analysis = json.loads(recorder_response)
            except json.JSONDecodeError:
                # If parsing fails, create default analysis
                analysis = {
                    "outcome": "UNCLEAR",
                    "victim_persona": victim_persona,
                    "scam_tactic": scam_tactic,
                    "key_moment": "記錄員未能提供有效分析",
                    "full_conversation_log": conversation_history,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Ensure required fields exist
            analysis.update({
                "victim_persona": victim_persona,
                "scam_tactic": scam_tactic,
                "timestamp": datetime.now().isoformat(),
                "total_turns": len(conversation_history)
            })

            # Flatten dialogue for frontend
            speaker_type = {"騙徒": "scammer", "受騙者": "victim", "專家": "expert", "記錄人": "recorder"}
            dialogue = [
                {"type": speaker_type.get(m["speaker"], "recorder"), "message": m.get("dialogue", ""), "timestamp": m.get("timestamp")}
                for m in conversation_history
            ]
            analysis["dialogue"] = dialogue
            analysis["full_conversation_log"] = conversation_history
            log.info(f"[SIM] done outcome={analysis.get('outcome')} turns={analysis.get('total_turns')} messages={len(dialogue)}")
            
            log.info(f"對話模擬完成，結果: {analysis.get('outcome', 'UNKNOWN')}")
            return analysis
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            error_type = type(e).__name__
            error_msg = str(e)
            
            log.error(f"對話模擬過程中發生錯誤: {error_type}: {error_msg}")
            log.error(f"詳細錯誤追蹤:\n{error_detail}")
            
            return {
                "error": f"{error_type}: {error_msg}",
                "error_type": error_type,
                "error_detail": error_detail,
                "victim_persona": victim_persona,
                "scam_tactic": scam_tactic,
                "timestamp": datetime.now().isoformat()
            }

async def main():
    """Main function - test real dialogue"""
    log.info("============================================================")
    log.info("--- 啟動真實AI對話測試 ---")
    log.info("============================================================")
    
    runner = RealDialogueRunner()
    
    # 測試參數
    scam_tactic = random.choice(SCAM_TACTICS)
    victim_persona = random.choice(VICTIM_PERSONAS)
    
    log.info("測試參數:")
    log.info(f"  詐騙手法: {scam_tactic}")
    log.info(f"  受騙者類型: {victim_persona}")
    log.info(f"  Google ADK 可用: {ADK_AVAILABLE}")
    
    # 運行對話模擬
    result = await runner.run_dialogue_simulation(scam_tactic, victim_persona)
    
    log.info("============================================================")
    log.info("--- 對話測試完成 ---")
    log.info("============================================================")
    
    if "error" in result:
        log.error(f"測試失敗: {result['error']}")
    else:
        log.info("測試成功:")
        log.info(f"  結果: {result.get('outcome', 'UNKNOWN')}")
        log.info(f"  總回合數: {result.get('total_turns', 0)}")
        log.info(f"  詐騙手法: {result.get('scam_tactic', 'Unknown')}")
        log.info(f"  受騙者類型: {result.get('victim_persona', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
