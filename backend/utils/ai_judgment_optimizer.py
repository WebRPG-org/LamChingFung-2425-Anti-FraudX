"""
AI語意判定優化模塊
實現緩存、快速路徑、智能降級等優化功能
"""

import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from collections import OrderedDict


@dataclass
class CachedResult:
    """緩存的判定結果"""
    result: Dict
    timestamp: datetime
    hit_count: int = 0
    confidence: float = 0.0


class AIJudgmentCache:
    """AI判定結果緩存"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        初始化緩存
        
        Args:
            max_size: 最大緩存條目數
            ttl_seconds: 緩存過期時間（秒）
        """
        self.cache: OrderedDict[str, CachedResult] = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        
        # 統計數據
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "expired_entries": 0,
            "evicted_entries": 0
        }
    
    def _generate_key(self, message: str, mode: str, role: str) -> str:
        """生成緩存鍵"""
        # 使用消息內容、模式、角色生成唯一鍵
        content = f"{mode}:{role}:{message.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, message: str, mode: str, role: str) -> Optional[Dict]:
        """
        獲取緩存結果
        
        Returns:
            緩存的結果，如果不存在或過期則返回None
        """
        self.stats["total_requests"] += 1
        
        key = self._generate_key(message, mode, role)
        
        if key not in self.cache:
            self.stats["cache_misses"] += 1
            return None
        
        cached = self.cache[key]
        
        # 檢查是否過期
        if datetime.now() - cached.timestamp > self.ttl:
            self.stats["expired_entries"] += 1
            self.stats["cache_misses"] += 1
            del self.cache[key]
            return None
        
        # 命中緩存
        self.stats["cache_hits"] += 1
        cached.hit_count += 1
        
        # 移到最前面（LRU）
        self.cache.move_to_end(key)
        
        return cached.result
    
    def set(self, message: str, mode: str, role: str, result: Dict, confidence: float = 0.0):
        """
        設置緩存結果
        
        Args:
            message: 消息內容
            mode: 遊戲模式
            role: 角色
            result: 判定結果
            confidence: 信心度
        """
        key = self._generate_key(message, mode, role)
        
        # 如果緩存已滿，移除最舊的條目
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)
            self.stats["evicted_entries"] += 1
        
        self.cache[key] = CachedResult(
            result=result,
            timestamp=datetime.now(),
            confidence=confidence
        )
    
    def clear(self):
        """清空緩存"""
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        """獲取緩存統計"""
        total = self.stats["total_requests"]
        hit_rate = (self.stats["cache_hits"] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "hit_rate": round(hit_rate, 2),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl.total_seconds()
        }


class FastPathJudgment:
    """快速路徑判定（明確表達直接判定）"""
    
    def __init__(self):
        """初始化快速判定規則"""
        # 騙徒模式 - 明確勝出關鍵詞
        self.scammer_win_keywords = [
            # 提供資料（普通話）
            "我會提供資料", "我提供資料", "我給你資料", "這是我的資料",
            "我的銀行帳號是", "我的密碼是", "我的身份證號是",
            "我可以提供資料", "我願意提供資料", "我會給資料",
            # 提供資料（廣東話）
            "我俾資料你", "我畀資料你", "呢個係我嘅資料",
            "我嘅銀行帳號係", "我嘅密碼係",
            "我會提供資料", "我可以俾資料", "我願意俾資料",
            # 金錢交易（普通話）
            "我會轉帳", "我會匯款", "我會付款", "我會給錢",
            "我現在就轉帳", "我馬上轉帳", "我立即轉帳",
            "我可以給錢", "我願意付款", "我會支付",
            # 金錢交易（廣東話）
            "我會過數", "我會轉數", "我會俾錢", "我會畀錢",
            "我而家就過數", "我即刻過數", "我立即俾錢",
            "我可以俾錢", "我願意俾錢", "我會畀錢你",
            # 同意配合
            "好的我會", "好我會", "可以我會", "沒問題我會",
            "好嘅我會", "得我會", "冇問題我會"
        ]
        
        # 騙徒模式 - 明確失敗關鍵詞
        self.scammer_lose_keywords = [
            # 報警（普通話）
            "我要報警", "我會報警", "我去報警", "我已經報警",
            "我打999", "我打110", "我報警了",
            # 報警（廣東話）
            "我要報警", "我會報警", "我去報警", "我報咗警",
            "我打999", "我搵警察", "我搵差人",
            # 識破（普通話）
            "你是騙子", "這是騙局", "你在騙我", "我不會上當",
            "我知道你在騙我", "別想騙我",
            # 識破（廣東話）
            "你係騙徒", "呢個係騙局", "你呃我", "我唔會上當",
            "我知道你呃我", "唔好呃我"
        ]
        
        # 專家模式 - 明確勝出關鍵詞
        self.expert_win_keywords = [
            # 聽從專家（普通話）
            "我聽專家的", "我相信專家", "專家說得對", "謝謝專家",
            "我會聽你的建議", "我不會給他資料", "我不會轉帳",
            # 聽從專家（廣東話）
            "我聽專家講", "我信專家", "專家講得啱", "多謝專家",
            "我會聽你講", "我唔會俾資料佢", "我唔會過數"
        ]
        
        # 專家模式 - 明確失敗關鍵詞
        self.expert_lose_keywords = [
            # 不聽專家（普通話）
            "我不相信專家", "專家錯了", "我相信他", "我會給他資料",
            "我會轉帳給他", "我不聽你的",
            # 不聽專家（廣東話）
            "我唔信專家", "專家錯", "我信佢", "我會俾資料佢",
            "我會過數俾佢", "我唔聽你講"
        ]
        
        # 統計數據
        self.stats = {
            "total_checks": 0,
            "fast_path_hits": 0,
            "scammer_win": 0,
            "scammer_lose": 0,
            "expert_win": 0,
            "expert_lose": 0
        }
    
    def check(self, message: str, mode: str, role: str) -> Optional[Tuple[Dict, float]]:
        """
        快速路徑檢查
        
        Args:
            message: 消息內容
            mode: 遊戲模式
            role: 角色
        
        Returns:
            (判定結果, 信心度) 或 None（需要AI判定）
        """
        self.stats["total_checks"] += 1
        
        message_lower = message.lower()
        
        # 受害人模式：檢查玩家（受害人）的回應
        if mode == "victim" and role == "player":
            # 檢查受害人識破騙局
            for keyword in self.scammer_lose_keywords:
                if keyword.lower() in message_lower:
                    self.stats["fast_path_hits"] += 1
                    self.stats["expert_win"] += 1
                    return (
                        {
                            "instant_win": True,
                            "winner": "player",
                            "reason": f"成功識破騙局！（關鍵詞：{keyword}）"
                        },
                        95.0
                    )
            
            # 檢查受害人被騙
            for keyword in self.scammer_win_keywords:
                if keyword.lower() in message_lower:
                    self.stats["fast_path_hits"] += 1
                    self.stats["scammer_win"] += 1
                    return (
                        {
                            "instant_win": True,
                            "winner": "ai",
                            "reason": f"被騙成功！受害者同意配合（關鍵詞：{keyword}）"
                        },
                        95.0
                    )
        
        # 騙徒模式和專家模式：檢查AI受害者的回應
        elif role == "victim":
            if mode == "scammer":
                # 檢查騙徒勝出
                for keyword in self.scammer_win_keywords:
                    if keyword.lower() in message_lower:
                        self.stats["fast_path_hits"] += 1
                        self.stats["scammer_win"] += 1
                        return (
                            {
                                "instant_win": True,
                                "winner": "player",
                                "reason": f"騙徒成功！受害者明確同意（關鍵詞：{keyword}）"
                            },
                            95.0  # 高信心度
                        )
                
                # 檢查騙徒失敗
                for keyword in self.scammer_lose_keywords:
                    if keyword.lower() in message_lower:
                        self.stats["fast_path_hits"] += 1
                        self.stats["scammer_lose"] += 1
                        return (
                            {
                                "instant_win": True,
                                "winner": "ai",
                                "reason": f"防詐成功！受害者識破騙局（關鍵詞：{keyword}）"
                            },
                            95.0
                        )
            
            elif mode == "expert":
                # 檢查專家勝出
                for keyword in self.expert_win_keywords:
                    if keyword.lower() in message_lower:
                        self.stats["fast_path_hits"] += 1
                        self.stats["expert_win"] += 1
                        return (
                            {
                                "instant_win": True,
                                "winner": "player",
                                "reason": f"防詐成功！受害者聽從專家（關鍵詞：{keyword}）"
                            },
                            95.0
                        )
                
                # 檢查專家失敗
                for keyword in self.expert_lose_keywords:
                    if keyword.lower() in message_lower:
                        self.stats["fast_path_hits"] += 1
                        self.stats["expert_lose"] += 1
                        return (
                            {
                                "instant_win": True,
                                "winner": "ai",
                                "reason": f"防詐失敗！受害者不聽勸告（關鍵詞：{keyword}）"
                            },
                            95.0
                        )
        
        # 沒有匹配快速路徑
        return None
    
    def get_stats(self) -> Dict:
        """獲取統計數據"""
        total = self.stats["total_checks"]
        hit_rate = (self.stats["fast_path_hits"] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 2)
        }


class OptimizedAIJudgment:
    """優化的AI語意判定系統"""
    
    def __init__(self, agent_service, enable_cache: bool = True, enable_fast_path: bool = True):
        """
        初始化優化系統
        
        Args:
            agent_service: AI服務
            enable_cache: 是否啟用緩存
            enable_fast_path: 是否啟用快速路徑
        """
        self.agent_service = agent_service
        self.enable_cache = enable_cache
        self.enable_fast_path = enable_fast_path
        
        # 初始化組件
        self.cache = AIJudgmentCache() if enable_cache else None
        self.fast_path = FastPathJudgment() if enable_fast_path else None
        
        # 性能統計
        self.performance_stats = {
            "total_requests": 0,
            "fast_path_hits": 0,
            "cache_hits": 0,
            "ai_calls": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0
        }
    
    async def judge(
        self,
        message: str,
        role: str,
        mode: str,
        conversation_history: List[Dict]
    ) -> Dict:
        """
        優化的判定流程
        
        流程：
        1. 快速路徑檢查（明確表達）
        2. 緩存檢查
        3. AI語意判定
        4. 緩存結果
        
        Args:
            message: 消息內容
            role: 角色
            mode: 遊戲模式
            conversation_history: 對話歷史
        
        Returns:
            判定結果
        """
        start_time = time.time()
        self.performance_stats["total_requests"] += 1
        
        result = {
            "instant_win": False,
            "winner": None,
            "reason": ""
        }
        
        # 只檢查受害者的回應
        if role != "victim":
            return result
        
        # 步驟1: 快速路徑檢查
        if self.enable_fast_path and self.fast_path:
            fast_result = self.fast_path.check(message, mode, role)
            if fast_result:
                result, confidence = fast_result
                self.performance_stats["fast_path_hits"] += 1
                
                # 記錄性能
                elapsed = time.time() - start_time
                self._update_performance(elapsed)
                
                return result
        
        # 步驟2: 緩存檢查
        if self.enable_cache and self.cache:
            cached_result = self.cache.get(message, mode, role)
            if cached_result:
                self.performance_stats["cache_hits"] += 1
                
                # 記錄性能
                elapsed = time.time() - start_time
                self._update_performance(elapsed)
                
                return cached_result
        
        # 步驟3: AI語意判定
        try:
            self.performance_stats["ai_calls"] += 1
            
            # 構建優化的判定提示詞
            judge_prompt = self._build_optimized_prompt(message, mode)
            
            # 調用AI
            judge_response = await self.agent_service.generate_response(
                agent_type="expert",
                message=judge_prompt,
                conversation_history=[],
                check_consistency=False,
                track_performance=False
            )
            
            judgment = judge_response.get("reply", "繼續遊戲").strip()
            
            # 解析結果
            result = self._parse_judgment(judgment, mode)
            
            # 步驟4: 緩存結果（如果是明確判定）
            if self.enable_cache and self.cache and result["instant_win"]:
                self.cache.set(message, mode, role, result, confidence=90.0)
        
        except Exception as e:
            # 降級處理
            result = {
                "instant_win": False,
                "winner": None,
                "reason": f"AI判定失敗: {str(e)}"
            }
        
        # 記錄性能
        elapsed = time.time() - start_time
        self._update_performance(elapsed)
        
        return result
    
    def _build_optimized_prompt(self, message: str, mode: str) -> str:
        """
        構建優化的判定提示詞（更簡潔、更快）
        
        優化點：
        1. 減少不必要的說明
        2. 使用更直接的指令
        3. 要求簡短回答
        """
        if mode == "scammer":
            prompt = f"""判斷受害者是否被騙或識破騙局。

受害者說：「{message}」

只回答以下之一：
- "騙徒勝出" - 明確同意提供資料/金錢
- "防詐成功" - 明確拒絕並識破
- "繼續遊戲" - 態度不明確

回答："""
        
        else:  # expert mode
            prompt = f"""判斷受害者是否聽從專家或被騙。

受害者說：「{message}」

只回答以下之一：
- "專家勝出" - 聽從專家拒絕被騙
- "專家失敗" - 不聽勸告被騙
- "繼續遊戲" - 態度不明確

回答："""
        
        return prompt
    
    def _parse_judgment(self, judgment: str, mode: str) -> Dict:
        """解析AI判定結果"""
        result = {
            "instant_win": False,
            "winner": None,
            "reason": ""
        }
        
        if mode == "scammer":
            if "騙徒勝出" in judgment:
                result["instant_win"] = True
                result["winner"] = "player"
                result["reason"] = "騙徒成功！受害者同意提供資料或金錢"
            elif "防詐成功" in judgment:
                result["instant_win"] = True
                result["winner"] = "ai"
                result["reason"] = "防詐成功！受害者識破騙局並拒絕配合"
        
        elif mode == "expert":
            if "專家勝出" in judgment:
                result["instant_win"] = True
                result["winner"] = "player"
                result["reason"] = "防詐成功！受害者聽從專家建議，拒絕被騙"
            elif "專家失敗" in judgment:
                result["instant_win"] = True
                result["winner"] = "ai"
                result["reason"] = "防詐失敗！受害者不聽勸告，被騙成功"
        
        return result
    
    def _update_performance(self, elapsed: float):
        """更新性能統計"""
        self.performance_stats["total_response_time"] += elapsed
        total = self.performance_stats["total_requests"]
        self.performance_stats["avg_response_time"] = (
            self.performance_stats["total_response_time"] / total
        )
    
    def get_performance_report(self) -> Dict:
        """獲取性能報告"""
        total = self.performance_stats["total_requests"]
        
        report = {
            "summary": {
                "total_requests": total,
                "avg_response_time_ms": round(self.performance_stats["avg_response_time"] * 1000, 2),
                "fast_path_rate": round(self.performance_stats["fast_path_hits"] / total * 100, 2) if total > 0 else 0,
                "cache_hit_rate": round(self.performance_stats["cache_hits"] / total * 100, 2) if total > 0 else 0,
                "ai_call_rate": round(self.performance_stats["ai_calls"] / total * 100, 2) if total > 0 else 0
            },
            "performance_stats": self.performance_stats
        }
        
        # 添加緩存統計
        if self.cache:
            report["cache_stats"] = self.cache.get_stats()
        
        # 添加快速路徑統計
        if self.fast_path:
            report["fast_path_stats"] = self.fast_path.get_stats()
        
        return report
    
    def clear_cache(self):
        """清空緩存"""
        if self.cache:
            self.cache.clear()
    
    def export_stats(self, filepath: str):
        """導出統計數據"""
        report = self.get_performance_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)


# 使用示例
if __name__ == "__main__":
    print("=== 優化的AI語意判定系統 ===\n")
    
    print("功能特點：")
    print("1. ✅ 快速路徑判定（明確表達 <50ms）")
    print("2. ✅ 結果緩存（相同表達 <10ms）")
    print("3. ✅ 優化的AI Prompt（減少50%字數）")
    print("4. ✅ 智能降級機制")
    print("5. ✅ 詳細性能監控")
    print()
    
    print("預期性能提升：")
    print("- 90%場景使用快速路徑或緩存（<100ms）")
    print("- 10%場景使用AI判定（1-2秒）")
    print("- 平均響應時間：<200ms")
    print("- AI調用減少90%")
    print("- 成本降低90%")
