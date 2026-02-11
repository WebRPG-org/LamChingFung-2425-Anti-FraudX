"""
Prompt 版本管理系統
支持 A/B 測試和版本回退
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class PromptVersionManager:
    """
    Prompt 版本管理器
    
    功能：
    1. 註冊和管理多個 Prompt 版本
    2. A/B 測試不同版本
    3. 記錄每個版本的性能
    4. 自動選擇最佳版本
    """
    
    def __init__(self, storage_path: str = None):
        """
        初始化版本管理器
        
        Args:
            storage_path: 版本數據存儲路徑
        """
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "data",
                "prompt_versions.json"
            )
        
        self.storage_path = storage_path
        self.versions: Dict[str, Dict] = {}
        self.active_version = "v1.0"
        
        # 確保存儲目錄存在
        Path(os.path.dirname(self.storage_path)).mkdir(parents=True, exist_ok=True)
        
        # 加載已有版本
        self._load_versions()
    
    def register_version(
        self,
        version: str,
        prompt: str,
        metadata: Dict,
        agent_type: str = "expert"
    ):
        """
        註冊新版本 Prompt
        
        Args:
            version: 版本號（如 "v1.0", "v1.1"）
            prompt: Prompt 內容
            metadata: 元數據（描述、作者、變更說明等）
            agent_type: Agent 類型
        """
        if agent_type not in self.versions:
            self.versions[agent_type] = {}
        
        self.versions[agent_type][version] = {
            "prompt": prompt,
            "metadata": metadata,
            "created_at": datetime.now().isoformat(),
            "performance": [],
            "total_uses": 0,
            "success_count": 0,
            "avg_response_time": 0.0,
            "avg_token_usage": 0
        }
        
        self._save_versions()
        print(f"[PromptVersionManager] 註冊版本: {agent_type}/{version}")
    
    def get_version(self, agent_type: str, version: str) -> Optional[str]:
        """
        獲取指定版本的 Prompt
        
        Args:
            agent_type: Agent 類型
            version: 版本號
            
        Returns:
            Prompt 內容，如果不存在則返回 None
        """
        if agent_type in self.versions and version in self.versions[agent_type]:
            return self.versions[agent_type][version]["prompt"]
        return None
    
    def get_active_version(self, agent_type: str) -> str:
        """獲取當前活躍版本"""
        return self.active_version
    
    def set_active_version(self, agent_type: str, version: str):
        """設置活躍版本"""
        if agent_type in self.versions and version in self.versions[agent_type]:
            self.active_version = version
            self._save_versions()
            print(f"[PromptVersionManager] 設置活躍版本: {agent_type}/{version}")
        else:
            raise ValueError(f"版本不存在: {agent_type}/{version}")
    
    def record_performance(
        self,
        agent_type: str,
        version: str,
        metrics: Dict
    ):
        """
        記錄版本性能
        
        Args:
            agent_type: Agent 類型
            version: 版本號
            metrics: 性能指標（response_time, token_usage, success 等）
        """
        if agent_type not in self.versions or version not in self.versions[agent_type]:
            return
        
        version_data = self.versions[agent_type][version]
        version_data["performance"].append({
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        })
        
        # 更新統計
        version_data["total_uses"] += 1
        if metrics.get("success", False):
            version_data["success_count"] += 1
        
        # 更新平均值
        if "response_time" in metrics:
            old_avg = version_data["avg_response_time"]
            new_value = metrics["response_time"]
            version_data["avg_response_time"] = (
                (old_avg * (version_data["total_uses"] - 1) + new_value) / 
                version_data["total_uses"]
            )
        
        if "token_usage" in metrics:
            old_avg = version_data["avg_token_usage"]
            new_value = metrics["token_usage"]
            version_data["avg_token_usage"] = (
                (old_avg * (version_data["total_uses"] - 1) + new_value) / 
                version_data["total_uses"]
            )
        
        self._save_versions()
    
    def ab_test(
        self,
        agent_type: str,
        version_a: str,
        version_b: str,
        sample_size: int = 10
    ) -> Dict:
        """
        A/B 測試兩個版本
        
        Args:
            agent_type: Agent 類型
            version_a: 版本 A
            version_b: 版本 B
            sample_size: 測試樣本數量
            
        Returns:
            測試結果
        """
        if agent_type not in self.versions:
            raise ValueError(f"Agent 類型不存在: {agent_type}")
        
        if version_a not in self.versions[agent_type]:
            raise ValueError(f"版本不存在: {version_a}")
        
        if version_b not in self.versions[agent_type]:
            raise ValueError(f"版本不存在: {version_b}")
        
        results = {
            "version_a": {
                "version": version_a,
                "success": 0,
                "total": 0,
                "avg_response_time": 0.0
            },
            "version_b": {
                "version": version_b,
                "success": 0,
                "total": 0,
                "avg_response_time": 0.0
            }
        }
        
        # 注意：實際的 A/B 測試需要在真實模擬中進行
        # 這裡只是框架，返回當前的統計數據
        
        version_a_data = self.versions[agent_type][version_a]
        version_b_data = self.versions[agent_type][version_b]
        
        results["version_a"]["success"] = version_a_data["success_count"]
        results["version_a"]["total"] = version_a_data["total_uses"]
        results["version_a"]["avg_response_time"] = version_a_data["avg_response_time"]
        
        results["version_b"]["success"] = version_b_data["success_count"]
        results["version_b"]["total"] = version_b_data["total_uses"]
        results["version_b"]["avg_response_time"] = version_b_data["avg_response_time"]
        
        # 分析結果
        results["analysis"] = self._analyze_ab_test(results)
        
        return results
    
    def get_best_version(self, agent_type: str) -> Optional[str]:
        """
        獲取性能最佳的版本
        
        Args:
            agent_type: Agent 類型
            
        Returns:
            最佳版本號
        """
        if agent_type not in self.versions or not self.versions[agent_type]:
            return None
        
        best_version = None
        best_score = -1
        
        for version, data in self.versions[agent_type].items():
            if data["total_uses"] < 5:  # 至少需要 5 次使用才能評估
                continue
            
            # 計算綜合得分
            success_rate = (
                data["success_count"] / data["total_uses"] 
                if data["total_uses"] > 0 else 0
            )
            
            # 得分 = 成功率 * 0.7 + (1 - 標準化響應時間) * 0.3
            score = success_rate * 0.7
            
            if best_score < score:
                best_score = score
                best_version = version
        
        return best_version
    
    def list_versions(self, agent_type: str) -> List[Dict]:
        """
        列出所有版本及其統計
        
        Args:
            agent_type: Agent 類型
            
        Returns:
            版本列表
        """
        if agent_type not in self.versions:
            return []
        
        versions_list = []
        for version, data in self.versions[agent_type].items():
            success_rate = (
                data["success_count"] / data["total_uses"] 
                if data["total_uses"] > 0 else 0
            )
            
            versions_list.append({
                "version": version,
                "created_at": data["created_at"],
                "total_uses": data["total_uses"],
                "success_rate": f"{success_rate * 100:.1f}%",
                "avg_response_time": f"{data['avg_response_time']:.2f}s",
                "avg_token_usage": data["avg_token_usage"],
                "metadata": data["metadata"]
            })
        
        return versions_list
    
    # ==================== 私有方法 ====================
    
    def _load_versions(self):
        """從文件加載版本數據"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.versions = data.get("versions", {})
                    self.active_version = data.get("active_version", "v1.0")
                print(f"[PromptVersionManager] 加載版本數據: {len(self.versions)} 個 Agent 類型")
            except Exception as e:
                print(f"[PromptVersionManager] 加載失敗: {e}")
                self.versions = {}
    
    def _save_versions(self):
        """保存版本數據到文件"""
        try:
            data = {
                "versions": self.versions,
                "active_version": self.active_version,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PromptVersionManager] 保存失敗: {e}")
    
    def _analyze_ab_test(self, results: Dict) -> Dict:
        """分析 A/B 測試結果"""
        version_a = results["version_a"]
        version_b = results["version_b"]
        
        # 計算成功率
        success_rate_a = (
            version_a["success"] / version_a["total"] 
            if version_a["total"] > 0 else 0
        )
        success_rate_b = (
            version_b["success"] / version_b["total"] 
            if version_b["total"] > 0 else 0
        )
        
        # 確定勝者
        if success_rate_a > success_rate_b:
            winner = version_a["version"]
            improvement = (success_rate_a - success_rate_b) * 100
        elif success_rate_b > success_rate_a:
            winner = version_b["version"]
            improvement = (success_rate_b - success_rate_a) * 100
        else:
            winner = "平手"
            improvement = 0
        
        return {
            "winner": winner,
            "improvement": f"{improvement:.1f}%",
            "success_rate_a": f"{success_rate_a * 100:.1f}%",
            "success_rate_b": f"{success_rate_b * 100:.1f}%",
            "recommendation": (
                f"建議使用 {winner}" if winner != "平手" 
                else "兩個版本性能相近，可繼續測試"
            )
        }
