"""
RPGv2 遊戲模式管理器
支持三種遊戲模式：騙徒模式、專家模式、自動模式
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)

GameMode = Literal["victim", "expert", "scammer", "auto"]


@dataclass
class GameSession:
    """遊戲會話"""
    session_id: str
    mode: GameMode
    scam_type: str
    victim_persona: str
    conversation_history: List[Dict]
    round_count: int
    trust_in_scammer: float
    trust_in_expert: float
    alertness: float
    player_score: int
    ai_score: int
    start_time: str
    last_update: str
    game_over: bool = False  # 🔥 新增：遊戲是否結束
    winner: Optional[str] = None  # 🔥 新增：勝利者
    round_logs: List[Dict] = field(default_factory=list)  # 🔥 新增：每回合的詳細記錄


class RPGv2GameModeManager:
    """RPGv2 遊戲模式管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.sessions: Dict[str, GameSession] = {}
        self.recorder_agent = None  # 🔥 新增：Recorder Agent
        
        # 初始化 Recorder
        self._init_recorder()
        
        # 模式配置
        self.mode_configs = {
            "victim": {
                "name": "受害人模式",
                "description": "玩家扮演受害人，面對騙徒和專家的對話",
                "player_role": "victim",
                "ai_roles": ["scammer", "expert"],  # 兩個AI角色
                "win_condition": "alertness > 70 or trust_in_scammer < 30",
                "scoring": {
                    "correct_judgment": 20,
                    "follow_expert_advice": 15,
                    "resist_scam": 25,
                    "time_bonus": 5
                }
            },
            "expert": {
                "name": "專家模式",
                "description": "玩家扮演防詐專家，保護受害者免受騙徒侵害",
                "player_role": "expert",
                "ai_roles": ["scammer", "victim"],  # 兩個AI角色
                "win_condition": "alertness > 70 or trust_in_scammer < 30",
                "scoring": {
                    "alertness_gain": 10,
                    "scam_detected": 20,
                    "victim_protected": 25,
                    "time_bonus": 5
                }
            },
            "scammer": {
                "name": "騙徒模式",
                "description": "玩家扮演騙徒，嘗試騙取受害者信任並對抗專家",
                "player_role": "scammer",
                "ai_roles": ["victim", "expert"],  # 兩個AI角色
                "win_condition": "trust_in_scammer > 70",
                "scoring": {
                    "trust_gain": 10,
                    "successful_tactic": 15,
                    "victim_compliance": 20,
                    "time_bonus": 5
                }
            },
            "auto": {
                "name": "自動模式",
                "description": "觀察AI騙徒與AI受害者的對話",
                "player_role": "observer",
                "ai_roles": ["scammer", "victim"],
                "win_condition": "none",
                "scoring": {
                    "observation": 5,
                    "analysis": 10
                }
            }
        }
        
        logger.info("✅ RPGv2 遊戲模式管理器已初始化")
    
    def _init_recorder(self):
        """初始化 Recorder Agent"""
        try:
            from agents.recorder import RecorderAgent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            
            self.recorder_agent = RecorderAgent()
            self.recorder_runner = Runner(
                agent=self.recorder_agent,
                app_name="agents",
                session_service=InMemorySessionService()
            )
            logger.info("✅ Recorder Agent 已初始化")
        except Exception as e:
            logger.warning(f"⚠️ Recorder Agent 初始化失敗: {e}，將禁用評分分析功能")
            self.recorder_agent = None
    
    def create_session(
        self,
        session_id: str,
        mode: GameMode,
        scam_type: str,
        victim_persona: str
    ) -> GameSession:
        """
        創建遊戲會話
        
        Args:
            session_id: 會話ID
            mode: 遊戲模式
            scam_type: 騙案類型
            victim_persona: 受害者人設
        
        Returns:
            GameSession對象
        """
        if mode not in self.mode_configs:
            raise ValueError(f"無效的遊戲模式: {mode}")
        
        session = GameSession(
            session_id=session_id,
            mode=mode,
            scam_type=scam_type,
            victim_persona=victim_persona,
            conversation_history=[],
            round_count=0,
            trust_in_scammer=50.0,
            trust_in_expert=50.0,
            alertness=50.0,
            player_score=0,
            ai_score=0,
            start_time=datetime.now().isoformat(),
            last_update=datetime.now().isoformat()
        )
        
        self.sessions[session_id] = session
        
        logger.info(
            f"🎮 創建遊戲會話 - ID={session_id}, "
            f"模式={mode}, 騙案={scam_type}, 人設={victim_persona}"
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[GameSession]:
        """獲取遊戲會話"""
        return self.sessions.get(session_id)
    
    def update_session(
        self,
        session_id: str,
        player_message: str,
        ai_responses: List[Dict],
        trust_changes: Dict[str, float]
    ) -> Dict:
        """
        更新遊戲會話
        
        Args:
            session_id: 會話ID
            player_message: 玩家消息
            ai_responses: AI回應列表
            trust_changes: 信任度變化
        
        Returns:
            更新結果
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"會話不存在: {session_id}")
        
        # 🔥 修復：檢查遊戲是否已經結束，如果已結束則不再更新信任度
        if session.game_over:
            logger.warning(
                f"⚠️ 遊戲已結束 - 會話={session_id}, "
                f"勝者={session.winner}, 不再更新信任度"
            )
            # 返回當前狀態，不做任何更新
            return {
                "session": session,
                "score_update": {"player": 0, "ai": 0},
                "game_status": {
                    "game_over": True,
                    "winner": session.winner,
                    "reason": "遊戲已結束",
                    "final_scores": {
                        "player": session.player_score,
                        "ai": session.ai_score
                    },
                    "final_trust": {
                        "trust_in_scammer": session.trust_in_scammer,
                        "trust_in_expert": session.trust_in_expert,
                        "alertness": session.alertness
                    }
                }
            }
        
        # 根據遊戲模式確定玩家的角色
        player_role_map = {
            "victim": "victim",      # 受害人模式：玩家是受害者
            "scammer": "scammer",    # 騙徒模式：玩家是騙徒
            "expert": "expert",      # 專家模式：玩家是專家
            "auto": "observer"       # 自動模式：玩家是觀察者
        }
        
        player_role = player_role_map.get(session.mode, "player")
        
        # 記錄對話（使用正確的角色標記）
        session.conversation_history.append({
            "role": player_role,
            "content": player_message,
            "timestamp": datetime.now().isoformat()
        })
        
        for response in ai_responses:
            session.conversation_history.append({
                "role": response["role"],
                "content": response["content"],
                "timestamp": datetime.now().isoformat()
            })
        
        # 檢查是否有即時勝負判定
        instant_win = trust_changes.get("instant_win")
        if instant_win:
            # 即時勝負：直接設置遊戲結束狀態
            logger.info(
                f"⚡ 即時勝負判定 - 會話={session_id}, "
                f"勝者={instant_win['winner']}, 原因={instant_win['reason']}"
            )
            
            # 更新信任度（已經在trust_changes中大幅調整）
            session.trust_in_scammer += trust_changes.get("scammer", 0)
            session.trust_in_expert += trust_changes.get("expert", 0)
            session.alertness += trust_changes.get("alertness", 0)
            
            # 限制範圍
            session.trust_in_scammer = max(0, min(100, session.trust_in_scammer))
            session.trust_in_expert = max(0, min(100, session.trust_in_expert))
            session.alertness = max(0, min(100, session.alertness))
            
            # 更新回合數
            session.round_count += 1
            session.last_update = datetime.now().isoformat()
            
            # 計算分數（即時勝負給予額外獎勵）
            score_update = self._calculate_score_update(session, player_message, ai_responses)
            if instant_win["winner"] == "player":
                score_update["player"] += 100  # 即時勝利獎勵
            else:
                score_update["ai"] += 100
            
            session.player_score += score_update["player"]
            session.ai_score += score_update["ai"]
            
            # 🔥 修復：設置 session 的遊戲結束狀態
            session.game_over = True
            session.winner = instant_win["winner"]
            
            # 構建遊戲結束狀態
            game_status = {
                "game_over": True,
                "winner": instant_win["winner"],
                "reason": instant_win["reason"],
                "instant_win": True,
                "final_scores": {
                    "player": session.player_score,
                    "ai": session.ai_score
                },
                "final_trust": {
                    "trust_in_scammer": session.trust_in_scammer,
                    "trust_in_expert": session.trust_in_expert,
                    "alertness": session.alertness
                }
            }
            
            # 🔥 新增：保存遊戲記錄
            self._save_game_log(session)
            
            logger.info(
                f"🏁 即時勝負遊戲結束 - 會話={session_id}, "
                f"勝者={instant_win['winner']}, 原因={instant_win['reason']}"
            )
            
            return {
                "session": session,
                "score_update": score_update,
                "game_status": game_status
            }
        
        # 正常流程：更新信任度
        scammer_change = trust_changes.get("scammer", 0)
        expert_change = trust_changes.get("expert", 0)
        alertness_change = trust_changes.get("alertness", 0)
        
        logger.info(
            f"🔄 [回合{session.round_count + 1}] 信任度變化 - "
            f"騙徒: {session.trust_in_scammer:.1f} + {scammer_change:+.1f}, "
            f"專家: {session.trust_in_expert:.1f} + {expert_change:+.1f}, "
            f"警覺性: {session.alertness:.1f} + {alertness_change:+.1f}"
        )
        
        session.trust_in_scammer += scammer_change
        session.trust_in_expert += expert_change
        session.alertness += alertness_change
        
        # 限制範圍
        session.trust_in_scammer = max(0, min(100, session.trust_in_scammer))
        session.trust_in_expert = max(0, min(100, session.trust_in_expert))
        session.alertness = max(0, min(100, session.alertness))
        
        logger.info(
            f"✅ [回合{session.round_count + 1}] 更新後信任度 - "
            f"騙徒: {session.trust_in_scammer:.1f}, "
            f"專家: {session.trust_in_expert:.1f}, "
            f"警覺性: {session.alertness:.1f}"
        )
        
        # 更新回合數
        session.round_count += 1
        session.last_update = datetime.now().isoformat()
        
        # 計算分數
        score_update = self._calculate_score_update(session, player_message, ai_responses)
        session.player_score += score_update["player"]
        session.ai_score += score_update["ai"]
        
        # 檢查勝利條件
        game_status = self._check_win_condition(session)
        
        # 🔥 新增：記錄本回合的詳細數據
        round_log = {
            "round": session.round_count,
            "timestamp": datetime.now().isoformat(),
            "player_message": player_message,
            "ai_responses": ai_responses,
            "trust_changes": {
                "scammer": trust_changes.get("scammer", 0),
                "expert": trust_changes.get("expert", 0),
                "alertness": trust_changes.get("alertness", 0)
            },
            "trust_state": {
                "trust_in_scammer": session.trust_in_scammer,
                "trust_in_expert": session.trust_in_expert,
                "alertness": session.alertness
            },
            "score_update": score_update,
            "scores": {
                "player": session.player_score,
                "ai": session.ai_score
            },
            "game_status": game_status
        }
        session.round_logs.append(round_log)
        
        # 🔥 新增：使用 Recorder 進行評分分析（每回合）
        if self.recorder_agent:
            recorder_analysis = self._analyze_with_recorder(session)
            if recorder_analysis:
                round_log["recorder_analysis"] = recorder_analysis
                logger.info(f"📊 Recorder 分析完成 - 回合={session.round_count}")
        
        # 🔥 新增：如果遊戲結束，保存完整記錄
        if game_status["game_over"]:
            self._save_game_log(session)
        
        # 🔥 修復：如果遊戲結束，設置 session 的狀態
        if game_status["game_over"]:
            session.game_over = True
            session.winner = game_status["winner"]
            logger.info(
                f"🏁 遊戲結束 - 會話={session_id}, "
                f"勝者={game_status['winner']}, 原因={game_status['reason']}"
            )
        
        logger.info(
            f"🎮 更新會話 {session_id} - "
            f"回合={session.round_count}, "
            f"騙徒信任度={session.trust_in_scammer:.1f}, "
            f"警覺性={session.alertness:.1f}, "
            f"玩家分數={session.player_score}, "
            f"AI分數={session.ai_score}, "
            f"信任度變化={trust_changes}"
        )
        
        return {
            "session": session,
            "score_update": score_update,
            "game_status": game_status
        }
    
    def _calculate_score_update(
        self,
        session: GameSession,
        player_message: str,
        ai_responses: List[Dict]
    ) -> Dict[str, int]:
        """計算分數更新"""
        mode_config = self.mode_configs[session.mode]
        scoring = mode_config["scoring"]
        
        player_score = 0
        ai_score = 0
        
        if session.mode == "victim":
            # 受害人模式：玩家扮演受害人
            # 檢查是否做出正確判斷
            resist_keywords = ["不相信", "不要", "拒絕", "報警", "懷疑"]
            if any(keyword in player_message for keyword in resist_keywords):
                player_score += scoring["resist_scam"]
            
            # 檢查是否聽從專家建議
            follow_keywords = ["聽專家", "專家說得對", "謝謝專家", "明白了"]
            if any(keyword in player_message for keyword in follow_keywords):
                player_score += scoring["follow_expert_advice"]
            
            # 檢查警覺性
            if session.alertness > 60:
                player_score += scoring["correct_judgment"]
        
        elif session.mode == "scammer":
            # 騙徒模式：玩家扮演騙徒
            # 檢查是否使用了有效策略
            strategy_keywords = {
                "authority": ["警察", "銀行", "政府", "官方"],
                "urgency": ["立即", "馬上", "緊急", "快"],
                "sympathy": ["幫助", "可憐", "困難", "需要"],
                "greed": ["賺錢", "優惠", "獎金", "回報"]
            }
            
            for strategy, keywords in strategy_keywords.items():
                if any(keyword in player_message for keyword in keywords):
                    player_score += scoring["successful_tactic"]
                    break
            
            # 受害者配合度
            victim_response = next((r["content"] for r in ai_responses if r["role"] == "victim"), "")
            compliance_keywords = ["好的", "可以", "怎麼做", "明白"]
            if any(keyword in victim_response for keyword in compliance_keywords):
                player_score += scoring["victim_compliance"]
            
        elif session.mode == "expert":
            # 專家模式：玩家扮演專家
            # 檢查是否識別詐騙手法
            detection_keywords = ["詐騙", "騙局", "假的", "不要相信", "小心"]
            if any(keyword in player_message for keyword in detection_keywords):
                player_score += scoring["scam_detected"]
            
            # 檢查警覺性提升
            if session.alertness > 60:
                player_score += scoring["alertness_gain"]
        
        elif session.mode == "auto":
            # 自動模式：觀察分數
            player_score += scoring["observation"]
        
        # AI分數（基於對話質量）
        if ai_responses:
            ai_score += len(ai_responses) * 5
        
        return {
            "player": player_score,
            "ai": ai_score
        }
    
    def _check_win_condition(self, session: GameSession) -> Dict:
        """檢查勝利條件"""
        mode_config = self.mode_configs[session.mode]
        win_condition = mode_config["win_condition"]
        
        game_over = False
        winner = None
        reason = ""
        
        if session.mode == "victim":
            # 受害人模式勝利條件
            if session.alertness > 70 or session.trust_in_scammer < 30:
                game_over = True
                winner = "player"
                reason = "成功識破騙局，保護自己"
            elif session.trust_in_scammer > 70:
                game_over = True
                winner = "ai"
                reason = "被騙徒成功欺騙"
            elif session.round_count >= 15:
                game_over = True
                winner = "player" if session.alertness > 50 else "ai"
                reason = "達到最大回合數"
        
        elif session.mode == "scammer":
            # 騙徒模式勝利條件
            if session.trust_in_scammer > 70:
                game_over = True
                winner = "player"
                reason = "成功獲取受害者信任"
            elif session.alertness > 70:
                game_over = True
                winner = "ai"
                reason = "受害者在專家幫助下識破騙局"
            elif session.round_count >= 15:
                game_over = True
                winner = "player" if session.trust_in_scammer > session.alertness else "ai"
                reason = "達到最大回合數"
        
        elif session.mode == "expert":
            # 專家模式勝利條件
            if session.alertness > 70 or session.trust_in_scammer < 30:
                game_over = True
                winner = "player"
                reason = "成功保護受害者"
            elif session.trust_in_scammer > 70:
                game_over = True
                winner = "ai"
                reason = "受害者被騙"
            elif session.round_count >= 15:
                game_over = True
                winner = "player" if session.alertness > 50 else "ai"
                reason = "達到最大回合數"
        
        elif session.mode == "auto":
            # 自動模式：觀察到一定回合數結束
            if session.round_count >= 10:
                game_over = True
                winner = "none"
                reason = "觀察完成"
        
        return {
            "game_over": game_over,
            "winner": winner,
            "reason": reason,
            "final_scores": {
                "player": session.player_score,
                "ai": session.ai_score
            },
            "final_trust": {
                "trust_in_scammer": session.trust_in_scammer,
                "trust_in_expert": session.trust_in_expert,
                "alertness": session.alertness
            }
        }
    
    def get_mode_info(self, mode: GameMode) -> Dict:
        """獲取模式信息"""
        if mode not in self.mode_configs:
            raise ValueError(f"無效的遊戲模式: {mode}")
        
        return self.mode_configs[mode]
    
    def get_all_modes(self) -> List[Dict]:
        """獲取所有模式信息"""
        return [
            {
                "mode": mode,
                **config
            }
            for mode, config in self.mode_configs.items()
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """刪除會話"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️ 刪除會話 {session_id}")
            return True
        return False
    
    def _save_game_log(self, session: GameSession):
        """保存遊戲記錄到文件"""
        try:
            # 創建 logs 目錄
            log_dir = os.path.join(os.path.dirname(__file__), "..", "logs", "rpgv2")
            os.makedirs(log_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_{session.session_id}_{timestamp}.json"
            filepath = os.path.join(log_dir, filename)
            
            # 構建完整記錄
            game_log = {
                "session_id": session.session_id,
                "mode": session.mode,
                "scam_type": session.scam_type,
                "victim_persona": session.victim_persona,
                "start_time": session.start_time,
                "end_time": session.last_update,
                "game_over": session.game_over,
                "winner": session.winner,
                "final_scores": {
                    "player": session.player_score,
                    "ai": session.ai_score
                },
                "final_trust": {
                    "trust_in_scammer": session.trust_in_scammer,
                    "trust_in_expert": session.trust_in_expert,
                    "alertness": session.alertness
                },
                "total_rounds": session.round_count,
                "conversation_history": session.conversation_history,
                "round_logs": session.round_logs
            }
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(game_log, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 遊戲記錄已保存: {filepath}")
            
            # 生成摘要報告
            self._generate_summary_report(session, log_dir, timestamp)
            
        except Exception as e:
            logger.error(f"❌ 保存遊戲記錄失敗: {e}", exc_info=True)
    
    def _generate_summary_report(self, session: GameSession, log_dir: str, timestamp: str):
        """生成遊戲摘要報告"""
        try:
            filename = f"summary_{session.session_id}_{timestamp}.txt"
            filepath = os.path.join(log_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"RPGv2 遊戲記錄摘要\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"會話ID: {session.session_id}\n")
                f.write(f"遊戲模式: {session.mode}\n")
                f.write(f"騙案類型: {session.scam_type}\n")
                f.write(f"受害者類型: {session.victim_persona}\n")
                f.write(f"開始時間: {session.start_time}\n")
                f.write(f"結束時間: {session.last_update}\n")
                f.write(f"總回合數: {session.round_count}\n\n")
                
                f.write("-" * 60 + "\n")
                f.write("遊戲結果\n")
                f.write("-" * 60 + "\n")
                f.write(f"遊戲結束: {'是' if session.game_over else '否'}\n")
                f.write(f"勝利者: {session.winner or '未決定'}\n")
                f.write(f"玩家分數: {session.player_score}\n")
                f.write(f"AI分數: {session.ai_score}\n\n")
                
                f.write("-" * 60 + "\n")
                f.write("最終信任度\n")
                f.write("-" * 60 + "\n")
                f.write(f"對騙徒的信任度: {session.trust_in_scammer:.1f}/100\n")
                f.write(f"對專家的信任度: {session.trust_in_expert:.1f}/100\n")
                f.write(f"警覺性: {session.alertness:.1f}/100\n\n")
                
                f.write("-" * 60 + "\n")
                f.write("回合詳情\n")
                f.write("-" * 60 + "\n")
                for round_log in session.round_logs:
                    f.write(f"\n第 {round_log['round']} 回合:\n")
                    f.write(f"  信任度變化: 騙徒{round_log['trust_changes']['scammer']:+.1f}, ")
                    f.write(f"專家{round_log['trust_changes']['expert']:+.1f}, ")
                    f.write(f"警覺性{round_log['trust_changes']['alertness']:+.1f}\n")
                    f.write(f"  當前信任度: 騙徒{round_log['trust_state']['trust_in_scammer']:.1f}, ")
                    f.write(f"專家{round_log['trust_state']['trust_in_expert']:.1f}, ")
                    f.write(f"警覺性{round_log['trust_state']['alertness']:.1f}\n")
                    f.write(f"  分數變化: 玩家+{round_log['score_update']['player']}, ")
                    f.write(f"AI+{round_log['score_update']['ai']}\n")
                    
                    # 🔥 新增：如果有 Recorder 分析，也輸出
                    if 'recorder_analysis' in round_log:
                        analysis = round_log['recorder_analysis']
                        f.write(f"\n  📊 Recorder 評分分析:\n")
                        if 'scammer_performance' in analysis:
                            sp = analysis['scammer_performance']
                            f.write(f"    騙徒總分: {sp.get('overall_score', 0)}/100\n")
                            f.write(f"      - 說服力: {sp.get('persuasiveness', 0)}/100\n")
                            f.write(f"      - 可信度: {sp.get('credibility', 0)}/100\n")
                            f.write(f"      - 施壓效果: {sp.get('pressure_effectiveness', 0)}/100\n")
                        if 'expert_performance' in analysis:
                            ep = analysis['expert_performance']
                            f.write(f"    專家總分: {ep.get('overall_score', 0)}/100\n")
                            f.write(f"      - 干預效果: {ep.get('intervention_effectiveness', 0)}/100\n")
                            f.write(f"      - 清晰度: {ep.get('clarity', 0)}/100\n")
                            f.write(f"      - 同理心: {ep.get('empathy', 0)}/100\n")
                
                f.write("\n" + "=" * 60 + "\n")
            
            logger.info(f"📊 摘要報告已生成: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ 生成摘要報告失敗: {e}", exc_info=True)
    
    def _analyze_with_recorder(self, session: GameSession) -> Optional[Dict]:
        """使用 Recorder Agent 分析當前遊戲狀態"""
        if not self.recorder_agent:
            return None
        
        try:
            # 構建分析 prompt
            analysis_prompt = self._build_recorder_prompt(session)
            
            # 調用 Recorder
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.recorder_runner.run(
                    user_id="system",
                    session_id=f"recorder_{session.session_id}",
                    new_message=analysis_prompt
                )
            )
            
            loop.close()
            
            # 解析 JSON 結果
            response_text = result.response_parts[0].text if result.response_parts else ""
            
            # 清理可能的 markdown 標記
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # 解析 JSON
            analysis = json.loads(response_text)
            
            logger.info(f"✅ Recorder 分析成功 - 回合={session.round_count}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Recorder 返回的不是有效 JSON: {e}")
            logger.error(f"原始回應: {response_text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"❌ Recorder 分析失敗: {e}", exc_info=True)
            return None
    
    def _build_recorder_prompt(self, session: GameSession) -> str:
        """構建 Recorder 分析 prompt"""
        # 構建對話歷史
        conversation_log = []
        for i, msg in enumerate(session.conversation_history, 1):
            conversation_log.append(f"[回合{i}] {msg['role']}: {msg['content']}")
        
        conversation_text = "\n".join(conversation_log)
        
        # 構建 prompt
        prompt = f"""請分析以下 RPGv2 遊戲對話，並提供詳細的評分和建議。

遊戲模式: {session.mode}
騙案類型: {session.scam_type}
受害者類型: {session.victim_persona}
當前回合: {session.round_count}

當前信任度狀態:
- 對騙徒的信任度: {session.trust_in_scammer:.1f}/100
- 對專家的信任度: {session.trust_in_expert:.1f}/100
- 警覺性: {session.alertness:.1f}/100

對話記錄:
{conversation_text}

請根據你的 instruction 提供完整的 JSON 格式分析，包括：
1. 騙徒和專家的性能評分（scammer_performance, expert_performance）
2. 信任度變化分析（victim_trust_analysis）
3. 關鍵時刻分析（key_moment）
4. 改進建議（improvement_suggestion）

請直接輸出 JSON，不要有任何額外文字。
"""
        
        return prompt
    
    def get_session_stats(self, session_id: str) -> Dict:
        """獲取會話統計"""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"會話不存在: {session_id}")
        
        # 計算對話統計
        player_messages = [
            msg for msg in session.conversation_history
            if msg["role"] == "player"
        ]
        
        ai_messages = [
            msg for msg in session.conversation_history
            if msg["role"] != "player"
        ]
        
        # 計算平均消息長度
        avg_player_length = (
            sum(len(msg["content"]) for msg in player_messages) / len(player_messages)
            if player_messages else 0
        )
        
        avg_ai_length = (
            sum(len(msg["content"]) for msg in ai_messages) / len(ai_messages)
            if ai_messages else 0
        )
        
        return {
            "session_id": session_id,
            "mode": session.mode,
            "round_count": session.round_count,
            "player_score": session.player_score,
            "ai_score": session.ai_score,
            "trust_data": {
                "trust_in_scammer": session.trust_in_scammer,
                "trust_in_expert": session.trust_in_expert,
                "alertness": session.alertness
            },
            "message_stats": {
                "total_messages": len(session.conversation_history),
                "player_messages": len(player_messages),
                "ai_messages": len(ai_messages),
                "avg_player_length": round(avg_player_length, 2),
                "avg_ai_length": round(avg_ai_length, 2)
            },
            "duration": {
                "start_time": session.start_time,
                "last_update": session.last_update
            }
        }


# 全局實例
game_mode_manager = RPGv2GameModeManager()


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = RPGv2GameModeManager()
    
    # 創建騙徒模式會話
    session = manager.create_session(
        session_id="test_001",
        mode="scammer",
        scam_type="假冒銀行",
        victim_persona="elderly"
    )
    
    print(f"會話創建: {session.session_id}")
    print(f"模式: {session.mode}")
    
    # 獲取模式信息
    mode_info = manager.get_mode_info("scammer")
    print(f"\n模式信息: {mode_info['name']}")
    print(f"描述: {mode_info['description']}")
    
    # 獲取所有模式
    all_modes = manager.get_all_modes()
    print(f"\n可用模式數: {len(all_modes)}")
