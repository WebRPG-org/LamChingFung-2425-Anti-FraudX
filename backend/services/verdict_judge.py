"""
勝負判定器 - Phase 2.2 實現
LLM 分析是否達到勝利條件，判定遊戲勝負
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from utils.logger import log


class VerdictJudge:
    """勝負判定器 - 判定遊戲勝負"""
    
    def __init__(self):
        """初始化勝負判定器"""
        self.verdicts: Dict[str, Dict[str, Any]] = {}  # session_id -> verdict
        self.verdict_history: List[Dict[str, Any]] = []
        
        log.info("✅ 勝負判定器已初始化")
    
    async def judge_scammer_win(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        判定騙徒是否贏了 (嚴格判定)
        
        Args:
            message: 受害者消息
            session_id: 可選的 session ID
        
        Returns:
            判定結果
        """
        try:
            # 騙徒勝利條件 (需要真實提供敏感信息)
            scammer_win_conditions = {
                "銀行密碼": {
                    "keywords": ["密碼", "password"],
                    "patterns": [r"\d{4,}", r"[a-zA-Z]{4,}"],  # 4位以上數字或字母
                    "negative": ["如果", "假設", "想", "可能", "朋友", "聽說"]
                },
                "銀行帳號": {
                    "keywords": ["帳號", "account", "卡號"],
                    "patterns": [r"\d{10,}"],  # 10位以上數字
                    "negative": ["如果", "假設", "想", "可能", "朋友", "聽說"]
                },
                "驗證碼": {
                    "keywords": ["驗證碼", "verification code", "otp"],
                    "patterns": [r"\d{4,6}"],  # 4-6位數字
                    "negative": ["如果", "假設", "想", "可能", "朋友", "聽說"]
                },
                "轉賬": {
                    "keywords": ["已經轉", "已轉", "轉了", "轉完", "已完成"],  # 完成時態
                    "patterns": [r"\d+"],  # 金額
                    "negative": ["想轉", "如果轉", "假設轉", "可能轉"]
                },
                "身份證": {
                    "keywords": ["身份證", "id card"],
                    "patterns": [r"[A-Z]\d{8}", r"\d{10,}"],  # 身份證格式
                    "negative": ["如果", "假設", "想", "可能", "朋友", "聽說"]
                }
            }
            
            # 檢查勝利條件 (需要同時滿足關鍵字和模式)
            detected_conditions = []
            confidence_scores = []
            
            import re
            message_lower = message.lower()
            
            for condition, rules in scammer_win_conditions.items():
                # 檢查是否包含負面指示詞 (假設、朋友等)
                has_negative = any(neg in message_lower for neg in rules["negative"])
                if has_negative:
                    continue
                
                # 檢查是否包含關鍵字 (完整詞匹配，支持中英文)
                has_keyword = False
                for kw in rules["keywords"]:
                    kw_lower = kw.lower()
                    # 對於中文，直接檢查包含；對於英文，使用詞邊界
                    if any(ord(c) > 127 for c in kw):  # 中文字符
                        if kw_lower in message_lower:
                            has_keyword = True
                            break
                    else:  # 英文
                        if re.search(r'\b' + re.escape(kw_lower) + r'\b', message_lower):
                            has_keyword = True
                            break
                
                if not has_keyword:
                    continue
                
                # 檢查是否匹配模式 (實際提供了數據)
                has_pattern = any(re.search(pattern, message) for pattern in rules["patterns"])
                if not has_pattern:
                    continue
                
                # 同時滿足所有條件才算勝利
                detected_conditions.append(condition)
                confidence_scores.append(self._calculate_confidence(message, condition))
            
            # 判定是否勝利 (需要高信心度)
            is_win = len(detected_conditions) > 0 and (sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0) >= 0.8
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            result = {
                "verdict": "scammer_win" if is_win else "ongoing",
                "is_win": is_win,
                "detected_conditions": detected_conditions,
                "confidence": round(avg_confidence, 2),
                "reasoning": self._generate_reasoning(detected_conditions, is_win, "scammer"),
                "timestamp": datetime.now().isoformat()
            }
            
            # 記錄判定
            self.verdict_history.append(result)
            
            if session_id:
                self.verdicts[session_id] = result
            
            log.info(f"✅ 騙徒勝負已判定: {result['verdict']} (信心度: {avg_confidence})")
            return result
        
        except Exception as e:
            log.error(f"❌ 判定騙徒勝負失敗: {e}")
            return {"error": str(e)}
    
    async def judge_expert_win(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        判定專家是否贏了 (嚴格判定)
        
        Args:
            message: 受害者消息
            session_id: 可選的 session ID
        
        Returns:
            判定結果
        """
        try:
            # 專家勝利條件 (需要真實行動)
            expert_win_conditions = {
                "報警": {
                    "keywords": ["報警", "報案", "警察", "18222", "police"],
                    "completion_keywords": ["已經", "已", "完成", "done", "正在", "現在", "打", "撥"],
                    "negative": ["如果", "假設", "想", "可能"]
                },
                "停止對話": {
                    "keywords": ["停止", "掛斷", "不再", "hang up", "唔再", "唔同"],
                    "completion_keywords": ["已經", "已", "完成", "done", "正在", "現在"],
                    "negative": ["如果", "假設", "想", "可能"]
                },
                "官方確認": {
                    "keywords": ["銀行", "官方", "確認", "official", "打去", "致電"],
                    "completion_keywords": ["已經", "已", "完成", "done", "正在", "現在", "打", "撥"],
                    "negative": ["如果", "假設", "想", "可能"]
                },
                "求助": {
                    "keywords": ["求助", "幫助", "家人", "朋友", "help", "爸爸", "媽媽", "老公", "老婆", "告訴"],
                    "completion_keywords": ["已經", "已", "完成", "done", "正在", "現在", "會"],
                    "negative": ["如果", "假設", "想", "可能"]
                },
                "懷疑": {
                    "keywords": ["懷疑", "唔信", "唔相信", "假", "騙", "詐騙", "唔係"],
                    "completion_keywords": [],  # 懷疑不需要完成時態
                    "negative": []
                }
            }
            
            # 檢查勝利條件 (需要同時滿足關鍵字和完成指示)
            detected_conditions = []
            confidence_scores = []
            
            import re
            message_lower = message.lower()
            
            for condition, rules in expert_win_conditions.items():
                # 檢查是否包含負面指示詞
                has_negative = any(neg in message_lower for neg in rules["negative"])
                if has_negative:
                    continue
                
                # 檢查是否包含關鍵字 (完整詞匹配，支持中英文)
                has_keyword = False
                for kw in rules["keywords"]:
                    kw_lower = kw.lower()
                    # 對於中文，直接檢查包含；對於英文，使用詞邊界
                    if any(ord(c) > 127 for c in kw):  # 中文字符
                        if kw_lower in message_lower:
                            has_keyword = True
                            break
                    else:  # 英文
                        if re.search(r'\b' + re.escape(kw_lower) + r'\b', message_lower):
                            has_keyword = True
                            break
                
                if not has_keyword:
                    continue
                
                # 檢查是否包含完成指示詞 (如果有的話)
                if rules["completion_keywords"]:
                    has_completion = any(ck in message_lower for ck in rules["completion_keywords"])
                    if not has_completion:
                        continue
                
                # 同時滿足所有條件才算勝利
                detected_conditions.append(condition)
                confidence_scores.append(0.85)  # 專家勝利信心度
            
            # 判定是否勝利 (需要高信心度)
            is_win = len(detected_conditions) > 0 and (sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0) >= 0.8
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            result = {
                "verdict": "expert_win" if is_win else "ongoing",
                "is_win": is_win,
                "detected_conditions": detected_conditions,
                "confidence": round(avg_confidence, 2),
                "reasoning": self._generate_reasoning(detected_conditions, is_win, "expert"),
                "timestamp": datetime.now().isoformat()
            }
            
            # 記錄判定
            self.verdict_history.append(result)
            
            if session_id:
                self.verdicts[session_id] = result
            
            log.info(f"✅ 專家勝負已判定: {result['verdict']} (信心度: {avg_confidence})")
            return result
        
        except Exception as e:
            log.error(f"❌ 判定專家勝負失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_confidence(self, message: str, condition: str) -> float:
        """
        計算信心度
        
        Args:
            message: 消息文本
            condition: 勝利條件
        
        Returns:
            信心度 (0-1)
        """
        try:
            # 基於消息長度和關鍵詞匹配度計算信心度
            message_lower = message.lower()
            
            # 檢查是否是真實行動（不是假設、不是別人的經歷）
            negative_indicators = ["如果", "假設", "朋友", "聽說", "據說", "好像"]
            for indicator in negative_indicators:
                if indicator in message_lower:
                    return 0.5  # 降低信心度
            
            # 檢查是否是完成時態
            completion_indicators = ["已經", "已", "完成", "done", "已經"]
            for indicator in completion_indicators:
                if indicator in message_lower:
                    return 0.95  # 提高信心度
            
            # 默認信心度
            return 0.8
        
        except Exception as e:
            log.error(f"❌ 計算信心度失敗: {e}")
            return 0.5
    
    def _generate_reasoning(self, conditions: List[str], is_win: bool, role: str) -> str:
        """
        生成判定理由
        
        Args:
            conditions: 檢測到的條件
            is_win: 是否勝利
            role: 角色 (scammer/expert)
        
        Returns:
            判定理由
        """
        try:
            if not is_win:
                return f"未檢測到 {role} 的勝利條件"
            
            if role == "scammer":
                return f"受害者提供了敏感資料: {', '.join(conditions)}"
            else:
                return f"受害者採取了防騙行動: {', '.join(conditions)}"
        
        except Exception as e:
            log.error(f"❌ 生成判定理由失敗: {e}")
            return "判定理由生成失敗"
    
    async def judge_round_winner(
        self,
        scammer_message: str,
        expert_message: str,
        victim_response: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        判定一輪的贏家
        
        Args:
            scammer_message: 騙徒消息
            expert_message: 專家消息
            victim_response: 受害者反應
            session_id: 可選的 session ID
        
        Returns:
            判定結果
        """
        try:
            # 判定騙徒是否贏
            scammer_verdict = await self.judge_scammer_win(victim_response, session_id)
            
            # 判定專家是否贏
            expert_verdict = await self.judge_expert_win(victim_response, session_id)
            
            # 判定贏家
            if scammer_verdict["is_win"] and not expert_verdict["is_win"]:
                winner = "scammer"
            elif expert_verdict["is_win"] and not scammer_verdict["is_win"]:
                winner = "expert"
            elif scammer_verdict["is_win"] and expert_verdict["is_win"]:
                # 都贏了，比較信心度
                winner = "scammer" if scammer_verdict["confidence"] > expert_verdict["confidence"] else "expert"
            else:
                winner = "ongoing"
            
            result = {
                "winner": winner,
                "scammer_verdict": scammer_verdict,
                "expert_verdict": expert_verdict,
                "round_summary": f"本輪 {winner} 獲勝" if winner != "ongoing" else "遊戲繼續",
                "timestamp": datetime.now().isoformat()
            }
            
            log.info(f"✅ 一輪判定完成: {winner} 獲勝")
            return result
        
        except Exception as e:
            log.error(f"❌ 判定一輪失敗: {e}")
            return {"error": str(e)}
    
    async def get_verdict_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取判定報告
        
        Args:
            session_id: 可選的 session ID
        
        Returns:
            判定報告
        """
        try:
            if session_id:
                verdict = self.verdicts.get(session_id)
                return {
                    "session_id": session_id,
                    "verdict": verdict,
                    "total_verdicts": len(self.verdict_history)
                }
            
            return {
                "total_verdicts": len(self.verdict_history),
                "scammer_wins": sum(1 for v in self.verdict_history if v.get("verdict") == "scammer_win"),
                "expert_wins": sum(1 for v in self.verdict_history if v.get("verdict") == "expert_win"),
                "ongoing": sum(1 for v in self.verdict_history if v.get("verdict") == "ongoing")
            }
        
        except Exception as e:
            log.error(f"❌ 獲取判定報告失敗: {e}")
            return {"error": str(e)}


class VerdictValidator:
    """勝負驗證器 - 驗證判定的準確性"""
    
    def __init__(self):
        """初始化勝負驗證器"""
        log.info("✅ 勝負驗證器已初始化")
    
    async def validate_verdict(
        self,
        verdict: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        驗證判定的準確性
        
        Args:
            verdict: 判定結果
            context: 上下文信息
        
        Returns:
            驗證結果
        """
        try:
            # 檢查判定的一致性
            is_consistent = self._check_consistency(verdict, context)
            
            # 檢查信心度
            confidence_valid = verdict.get("confidence", 0) >= 0.7
            
            # 檢查理由
            reasoning_valid = len(verdict.get("reasoning", "")) > 0
            
            # 綜合判定
            is_valid = is_consistent and confidence_valid and reasoning_valid
            
            result = {
                "is_valid": is_valid,
                "consistency": is_consistent,
                "confidence_valid": confidence_valid,
                "reasoning_valid": reasoning_valid,
                "validation_score": self._calculate_validation_score(is_consistent, confidence_valid, reasoning_valid)
            }
            
            log.info(f"✅ 判定已驗證: {'有效' if is_valid else '無效'}")
            return result
        
        except Exception as e:
            log.error(f"❌ 驗證判定失敗: {e}")
            return {"error": str(e)}
    
    def _check_consistency(self, verdict: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        檢查判定的一致性
        
        Args:
            verdict: 判定結果
            context: 上下文信息
        
        Returns:
            是否一致
        """
        try:
            # 檢查判定是否與檢測到的條件一致
            detected_conditions = verdict.get("detected_conditions", [])
            is_win = verdict.get("is_win", False)
            
            # 如果檢測到條件，應該是勝利
            if detected_conditions and not is_win:
                return False
            
            # 如果沒有檢測到條件，應該不是勝利
            if not detected_conditions and is_win:
                return False
            
            return True
        
        except Exception as e:
            log.error(f"❌ 檢查一致性失敗: {e}")
            return False
    
    def _calculate_validation_score(self, consistency: bool, confidence: bool, reasoning: bool) -> float:
        """
        計算驗證評分
        
        Args:
            consistency: 一致性
            confidence: 信心度
            reasoning: 理由
        
        Returns:
            驗證評分 (0-1)
        """
        try:
            score = 0.0
            if consistency:
                score += 0.4
            if confidence:
                score += 0.3
            if reasoning:
                score += 0.3
            
            return round(score, 2)
        
        except Exception as e:
            log.error(f"❌ 計算驗證評分失敗: {e}")
            return 0.0


# 全局勝負判定器實例
_verdict_judge: Optional[VerdictJudge] = None
_verdict_validator: Optional[VerdictValidator] = None

def get_verdict_judge() -> VerdictJudge:
    """獲取勝負判定器實例"""
    global _verdict_judge
    if _verdict_judge is None:
        _verdict_judge = VerdictJudge()
    return _verdict_judge

def get_verdict_validator() -> VerdictValidator:
    """獲取勝負驗證器實例"""
    global _verdict_validator
    if _verdict_validator is None:
        _verdict_validator = VerdictValidator()
    return _verdict_validator

