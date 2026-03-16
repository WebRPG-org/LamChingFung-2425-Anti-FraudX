"""
Prompt 性能監控系統
追蹤和分析 Prompt 的性能指標
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import json
import os


class PromptPerformanceMonitor:
    """
    Prompt 性能監控器
    
    功能：
    1. 追蹤響應時間
    2. 追蹤 Token 使用量
    3. 追蹤輸出質量
    4. 追蹤角色一致性
    5. 生成性能報告
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = defaultdict(list)
        self.start_times: Dict[str, float] = {}
    
    def start_tracking(self, agent_type: str, request_id: str):
        """
        開始追蹤一個請求
        
        Args:
            agent_type: Agent 類型
            request_id: 請求 ID
        """
        self.start_times[request_id] = time.time()
    
    def end_tracking(
        self,
        agent_type: str,
        request_id: str,
        token_usage: int,
        output_quality: float,
        role_consistency: float,
        success: bool = True
    ):
        """
        結束追蹤並記錄指標
        
        Args:
            agent_type: Agent 類型
            request_id: 請求 ID
            token_usage: Token 使用量
            output_quality: 輸出質量（0-1）
            role_consistency: 角色一致性（0-1）
            success: 是否成功
        """
        if request_id not in self.start_times:
            return
        
        response_time = time.time() - self.start_times[request_id]
        del self.start_times[request_id]
        
        self.metrics[agent_type].append({
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "response_time": response_time,
            "token_usage": token_usage,
            "output_quality": output_quality,
            "role_consistency": role_consistency,
            "success": success
        })
    
    def track_metrics(self, agent_type: str, metrics: Dict):
        """
        直接追蹤指標（不需要 start/end）
        
        Args:
            agent_type: Agent 類型
            metrics: 指標字典
        """
        self.metrics[agent_type].append({
            "timestamp": datetime.now().isoformat(),
            **metrics
        })
    
    def get_summary(self, agent_type: str, last_n: int = None) -> Dict:
        """
        獲取性能摘要
        
        Args:
            agent_type: Agent 類型
            last_n: 只統計最近 N 條記錄
            
        Returns:
            性能摘要
        """
        if agent_type not in self.metrics or not self.metrics[agent_type]:
            return {
                "agent_type": agent_type,
                "total_requests": 0,
                "message": "無數據"
            }
        
        data = self.metrics[agent_type]
        if last_n:
            data = data[-last_n:]
        
        # 計算統計
        total = len(data)
        success_count = sum(1 for m in data if m.get("success", True))
        
        response_times = [m["response_time"] for m in data if "response_time" in m]
        token_usages = [m["token_usage"] for m in data if "token_usage" in m]
        output_qualities = [m["output_quality"] for m in data if "output_quality" in m]
        role_consistencies = [m["role_consistency"] for m in data if "role_consistency" in m]
        
        return {
            "agent_type": agent_type,
            "total_requests": total,
            "success_rate": f"{(success_count / total * 100):.1f}%" if total > 0 else "N/A",
            "avg_response_time": f"{sum(response_times) / len(response_times):.2f}s" if response_times else "N/A",
            "avg_token_usage": int(sum(token_usages) / len(token_usages)) if token_usages else "N/A",
            "avg_output_quality": f"{sum(output_qualities) / len(output_qualities):.2f}" if output_qualities else "N/A",
            "avg_role_consistency": f"{sum(role_consistencies) / len(role_consistencies):.2f}" if role_consistencies else "N/A",
            "token_efficiency": self._calculate_token_efficiency(agent_type, data)
        }
    
    def generate_report(self, output_path: str = None) -> Dict:
        """
        生成完整的性能報告
        
        Args:
            output_path: 輸出文件路徑（可選）
            
        Returns:
            完整報告
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "agents": {}
        }
        
        for agent_type in self.metrics.keys():
            report["agents"][agent_type] = self.get_summary(agent_type)
        
        # 如果指定了輸出路徑，保存到文件
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                print(f"[PromptPerformanceMonitor] 報告已保存: {output_path}")
            except Exception as e:
                print(f"[PromptPerformanceMonitor] 保存報告失敗: {e}")
        
        return report
    
    def clear_metrics(self, agent_type: str = None):
        """
        清空指標
        
        Args:
            agent_type: Agent 類型（如果為 None 則清空所有）
        """
        if agent_type:
            if agent_type in self.metrics:
                self.metrics[agent_type] = []
        else:
            self.metrics.clear()
    
    def _calculate_token_efficiency(self, agent_type: str, data: List[Dict]) -> str:
        """
        計算 Token 效率
        
        Token 效率 = 輸出質量 / Token 使用量
        """
        valid_data = [
            m for m in data 
            if "token_usage" in m and "output_quality" in m and m["token_usage"] > 0
        ]
        
        if not valid_data:
            return "N/A"
        
        efficiencies = [
            m["output_quality"] / m["token_usage"] * 1000  # 乘以 1000 使數字更易讀
            for m in valid_data
        ]
        
        avg_efficiency = sum(efficiencies) / len(efficiencies)
        return f"{avg_efficiency:.2f}"
    
    def _calculate_avg(self, agent_type: str, field: str) -> float:
        """計算平均值"""
        if agent_type not in self.metrics:
            return 0.0
        
        values = [m[field] for m in self.metrics[agent_type] if field in m]
        return sum(values) / len(values) if values else 0.0
    
    def _calculate_success_rate(self, agent_type: str) -> float:
        """計算成功率"""
        if agent_type not in self.metrics or not self.metrics[agent_type]:
            return 0.0
        
        total = len(self.metrics[agent_type])
        success = sum(1 for m in self.metrics[agent_type] if m.get("success", True))
        
        return success / total if total > 0 else 0.0


# 全局監控實例
global_monitor = PromptPerformanceMonitor()
