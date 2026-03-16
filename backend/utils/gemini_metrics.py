"""
Gemini API 性能監控和成本統計
追蹤 API 使用情況、響應時間和成本
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from utils.logger import log


@dataclass
class GeminiMetrics:
    """Gemini API 性能指標"""
    
    # 請求統計
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Token 統計
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_tokens: int = 0
    
    # 時間統計
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    
    # 錯誤統計
    error_count: int = 0
    timeout_count: int = 0
    retry_count: int = 0
    
    # 按 Agent 類型統計
    agent_stats: Dict[str, Dict] = field(default_factory=dict)
    
    # 請求歷史（最近 100 條）
    request_history: List[Dict] = field(default_factory=list)
    
    # 開始時間
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_request(
        self,
        agent_type: str,
        success: bool,
        response_time: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: Optional[str] = None
    ):
        """記錄一次請求"""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
            self.total_tokens_input += input_tokens
            self.total_tokens_output += output_tokens
            self.total_tokens += (input_tokens + output_tokens)
            
            # 更新響應時間統計
            self.total_response_time += response_time
            self.avg_response_time = self.total_response_time / self.successful_requests
            self.min_response_time = min(self.min_response_time, response_time)
            self.max_response_time = max(self.max_response_time, response_time)
        else:
            self.failed_requests += 1
            self.error_count += 1
        
        # 按 Agent 類型統計
        if agent_type not in self.agent_stats:
            self.agent_stats[agent_type] = {
                "requests": 0,
                "tokens_input": 0,
                "tokens_output": 0,
                "avg_response_time": 0.0,
                "errors": 0
            }
        
        stats = self.agent_stats[agent_type]
        stats["requests"] += 1
        
        if success:
            stats["tokens_input"] += input_tokens
            stats["tokens_output"] += output_tokens
            # 更新平均響應時間
            prev_avg = stats["avg_response_time"]
            prev_count = stats["requests"] - 1
            stats["avg_response_time"] = (prev_avg * prev_count + response_time) / stats["requests"]
        else:
            stats["errors"] += 1
        
        # 記錄到歷史
        self.request_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent_type": agent_type,
            "success": success,
            "response_time": response_time,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "error": error
        })
        
        # 只保留最近 100 條
        if len(self.request_history) > 100:
            self.request_history.pop(0)
    
    def record_timeout(self, agent_type: str):
        """記錄超時"""
        self.timeout_count += 1
        self.record_request(agent_type, False, 0.0, error="timeout")
    
    def record_retry(self):
        """記錄重試"""
        self.retry_count += 1
    
    def estimate_cost(self) -> Dict[str, float]:
        """
        估算成本
        
        Gemini 2.0 Flash 定價（2024）:
        - 輸入: $0.075 / 1M tokens
        - 輸出: $0.30 / 1M tokens
        
        Returns:
            dict: 成本估算（美元）
        """
        input_cost = (self.total_tokens_input / 1_000_000) * 0.075
        output_cost = (self.total_tokens_output / 1_000_000) * 0.30
        total_cost = input_cost + output_cost
        
        return {
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(total_cost, 4),
            "input_cost_hkd": round(input_cost * 7.8, 2),
            "output_cost_hkd": round(output_cost * 7.8, 2),
            "total_cost_hkd": round(total_cost * 7.8, 2)
        }
    
    def get_summary(self) -> Dict:
        """獲取統計摘要"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "runtime_seconds": round(runtime, 2),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.successful_requests / self.total_requests * 100, 2) if self.total_requests > 0 else 0,
            "tokens": {
                "input": self.total_tokens_input,
                "output": self.total_tokens_output,
                "total": self.total_tokens
            },
            "response_time": {
                "avg": round(self.avg_response_time, 3),
                "min": round(self.min_response_time, 3) if self.min_response_time != float('inf') else 0,
                "max": round(self.max_response_time, 3)
            },
            "errors": {
                "total": self.error_count,
                "timeouts": self.timeout_count,
                "retries": self.retry_count
            },
            "cost": self.estimate_cost(),
            "agent_stats": self.agent_stats
        }
    
    def save_to_file(self, filepath: str):
        """保存統計到文件"""
        summary = self.get_summary()
        summary["request_history"] = self.request_history[-20:]  # 只保存最近 20 條
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        log.info(f"[GEMINI_METRICS] 統計已保存到: {filepath}")
    
    def reset(self):
        """重置統計"""
        self.__init__()


class GeminiMetricsManager:
    """Gemini 指標管理器（單例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.metrics = GeminiMetrics()
        return cls._instance
    
    def get_metrics(self) -> GeminiMetrics:
        """獲取指標實例"""
        return self.metrics
    
    def record_generation(
        self,
        agent_type: str,
        start_time: float,
        end_time: float,
        input_tokens: int,
        output_tokens: int,
        success: bool = True,
        error: Optional[str] = None
    ):
        """記錄一次生成"""
        response_time = end_time - start_time
        
        self.metrics.record_request(
            agent_type=agent_type,
            success=success,
            response_time=response_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error=error
        )
        
        # 記錄日誌
        if success:
            log.info(
                f"[GEMINI_METRICS] {agent_type} - "
                f"響應時間: {response_time:.2f}s, "
                f"Token: {input_tokens}→{output_tokens}"
            )
        else:
            log.error(
                f"[GEMINI_METRICS] {agent_type} - "
                f"請求失敗: {error}"
            )
    
    def get_summary(self) -> Dict:
        """獲取統計摘要"""
        return self.metrics.get_summary()
    
    def save_report(self, filepath: Optional[str] = None):
        """保存報告"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"backend/logs/gemini_metrics_{timestamp}.json"
        
        self.metrics.save_to_file(filepath)
    
    def reset(self):
        """重置統計"""
        self.metrics.reset()
        log.info("[GEMINI_METRICS] 統計已重置")


# 全局實例
gemini_metrics = GeminiMetricsManager()


def track_gemini_generation(agent_type: str):
    """
    裝飾器：追蹤 Gemini 生成
    
    用法:
    @track_gemini_generation("scammer")
    async def generate_scammer_response(...):
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                end_time = time.time()
                
                # 嘗試從結果中提取 token 信息
                input_tokens = getattr(result, 'input_tokens', 0)
                output_tokens = getattr(result, 'output_tokens', 0)
                
                gemini_metrics.record_generation(
                    agent_type=agent_type,
                    start_time=start_time,
                    end_time=end_time,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    success=True
                )
                
                return result
                
            except Exception as e:
                end_time = time.time()
                
                gemini_metrics.record_generation(
                    agent_type=agent_type,
                    start_time=start_time,
                    end_time=end_time,
                    input_tokens=0,
                    output_tokens=0,
                    success=False,
                    error=str(e)
                )
                
                raise
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # 測試
    metrics = GeminiMetricsManager()
    
    # 模擬一些請求
    metrics.record_generation("scammer", 0, 1.5, 100, 200, True)
    metrics.record_generation("victim", 0, 1.2, 80, 150, True)
    metrics.record_generation("expert", 0, 2.0, 120, 250, True)
    metrics.record_generation("scammer", 0, 0.5, 50, 100, False, "timeout")
    
    # 打印摘要
    summary = metrics.get_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # 保存報告
    metrics.save_report("test_metrics.json")
