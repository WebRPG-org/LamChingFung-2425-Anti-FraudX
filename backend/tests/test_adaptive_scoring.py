"""
測試自適應權重優化器
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from utils.adaptive_scoring import AdaptiveWeightOptimizer, WeightConfig


class TestAdaptiveWeightOptimizer:
    """測試AdaptiveWeightOptimizer類"""
    
    @pytest.fixture
    def optimizer(self):
        """創建優化器實例"""
        return AdaptiveWeightOptimizer()
    
    def test_get_expert_weights_elderly(self, optimizer):
        """測試獲取elderly型專家權重"""
        weights = optimizer.get_expert_weights("elderly")
        
        # 驗證權重值
        assert weights["empathy"] == 0.35
        assert weights["clarity"] == 0.20
        assert weights["evidence"] == 0.20
        assert weights["actionability"] == 0.25
        
        # 驗證權重總和為1
        assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_get_expert_weights_average(self, optimizer):
        """測試獲取average型專家權重"""
        weights = optimizer.get_expert_weights("average")
        
        assert weights["empathy"] == 0.20
        assert weights["clarity"] == 0.25
        assert weights["evidence"] == 0.35
        assert weights["actionability"] == 0.20
        
        assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_get_expert_weights_overconfident(self, optimizer):
        """測試獲取overconfident型專家權重"""
        weights = optimizer.get_expert_weights("overconfident")
        
        assert weights["empathy"] == 0.10
        assert weights["clarity"] == 0.30
        assert weights["evidence"] == 0.40
        assert weights["actionability"] == 0.20
        
        assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_get_expert_weights_unknown_persona(self, optimizer):
        """測試未知persona使用average配置"""
        weights = optimizer.get_expert_weights("unknown_persona")
        
        # 應該返回average配置
        average_weights = optimizer.get_expert_weights("average")
        assert weights == average_weights
    
    def test_calculate_weighted_expert_score_elderly(self, optimizer):
        """測試elderly型加權分數計算"""
        base_scores = {
            "empathy": 80,      # 高分，權重35%
            "clarity": 70,      # 中分，權重20%
            "evidence": 60,     # 低分，權重20%
            "actionability": 75 # 中高分，權重25%
        }
        
        score = optimizer.calculate_weighted_expert_score(base_scores, "elderly")
        
        # 手動計算預期值
        expected = (80 * 0.35 + 70 * 0.20 + 60 * 0.20 + 75 * 0.25)
        assert abs(score - expected) < 0.1
        
        # 驗證分數範圍
        assert 0 <= score <= 100
        
        # elderly型應該偏重empathy，所以分數應該較高
        assert score > 70
    
    def test_calculate_weighted_expert_score_overconfident(self, optimizer):
        """測試overconfident型加權分數計算"""
        base_scores = {
            "empathy": 80,      # 高分，但權重只有10%
            "clarity": 70,      # 中分，權重30%
            "evidence": 90,     # 高分，權重40%
            "actionability": 75 # 中高分，權重20%
        }
        
        score = optimizer.calculate_weighted_expert_score(base_scores, "overconfident")
        
        # 手動計算預期值
        expected = (80 * 0.10 + 70 * 0.30 + 90 * 0.40 + 75 * 0.20)
        assert abs(score - expected) < 0.1
        
        # overconfident型應該偏重evidence，所以分數應該較高
        assert score > 75
    
    def test_calculate_weighted_expert_score_missing_dimension(self, optimizer):
        """測試缺少某個維度的情況"""
        base_scores = {
            "empathy": 80,
            "clarity": 70,
            # 缺少evidence和actionability
        }
        
        score = optimizer.calculate_weighted_expert_score(base_scores, "elderly")
        
        # 應該只計算有的維度
        assert 0 <= score <= 100
    
    def test_get_scammer_multipliers_elderly(self, optimizer):
        """測試獲取elderly型騙徒乘數"""
        multipliers = optimizer.get_scammer_multipliers("elderly")
        
        # elderly對authority和fear特別敏感
        assert multipliers["authority"] == 1.5
        assert multipliers["fear"] == 1.5
        assert multipliers["benefits"] == 1.4
        
        # elderly對challenge不敏感
        assert multipliers["challenge"] == 0.5
    
    def test_get_scammer_multipliers_overconfident(self, optimizer):
        """測試獲取overconfident型騙徒乘數"""
        multipliers = optimizer.get_scammer_multipliers("overconfident")
        
        # overconfident對challenge特別敏感
        assert multipliers["challenge"] == 1.5
        assert multipliers["evidence"] == 1.4
        
        # overconfident對authority不敏感
        assert multipliers["authority"] == 0.5
    
    def test_apply_scammer_multiplier_elderly_authority(self, optimizer):
        """測試elderly型對authority策略的乘數"""
        base_change = 10
        adjusted = optimizer.apply_scammer_multiplier(base_change, "authority", "elderly")
        
        # elderly對authority敏感，乘數1.5
        assert adjusted == 15.0
    
    def test_apply_scammer_multiplier_overconfident_authority(self, optimizer):
        """測試overconfident型對authority策略的乘數"""
        base_change = 10
        adjusted = optimizer.apply_scammer_multiplier(base_change, "authority", "overconfident")
        
        # overconfident對authority不敏感，乘數0.5
        assert adjusted == 5.0
    
    def test_apply_scammer_multiplier_unknown_tactic(self, optimizer):
        """測試未知策略使用默認乘數1.0"""
        base_change = 10
        adjusted = optimizer.apply_scammer_multiplier(base_change, "unknown_tactic", "elderly")
        
        # 未知策略應該使用默認乘數1.0
        assert adjusted == 10.0
    
    def test_get_optimal_expert_approach_elderly(self, optimizer):
        """測試elderly型最佳專家策略"""
        approaches = optimizer.get_optimal_expert_approach("elderly")
        
        # 應該按權重排序
        assert approaches[0] == "empathy"  # 權重35%
        assert approaches[1] == "actionability"  # 權重25%
        assert len(approaches) == 4
    
    def test_get_optimal_expert_approach_overconfident(self, optimizer):
        """測試overconfident型最佳專家策略"""
        approaches = optimizer.get_optimal_expert_approach("overconfident")
        
        # 應該按權重排序
        assert approaches[0] == "evidence"  # 權重40%
        assert approaches[1] == "clarity"  # 權重30%
    
    def test_get_vulnerable_tactics_elderly(self, optimizer):
        """測試elderly型脆弱策略"""
        vulnerabilities = optimizer.get_vulnerable_tactics("elderly")
        
        # 應該只返回乘數>1.0的策略
        assert len(vulnerabilities) > 0
        
        # 應該按乘數降序排序
        for i in range(len(vulnerabilities) - 1):
            assert vulnerabilities[i][1] >= vulnerabilities[i+1][1]
        
        # 所有策略的乘數都應該>1.0
        for tactic, mult in vulnerabilities:
            assert mult > 1.0
    
    def test_get_vulnerable_tactics_overconfident(self, optimizer):
        """測試overconfident型脆弱策略"""
        vulnerabilities = optimizer.get_vulnerable_tactics("overconfident")
        
        # challenge應該是最脆弱的
        assert vulnerabilities[0][0] == "challenge"
        assert vulnerabilities[0][1] == 1.5
    
    def test_analyze_persona_characteristics_elderly(self, optimizer):
        """測試elderly型特徵分析"""
        analysis = optimizer.analyze_persona_characteristics("elderly")
        
        assert analysis["persona"] == "elderly"
        assert analysis["top_expert_approach"] == "empathy"
        assert analysis["top_expert_weight"] == 0.35
        assert analysis["top_scammer_tactic"] in ["authority", "fear"]  # 都是1.5
        assert analysis["avg_vulnerability"] > 1.0  # elderly整體較脆弱
        
        assert "expert_weights" in analysis
        assert "scammer_multipliers" in analysis
        assert "recommendations" in analysis
        assert "vulnerabilities" in analysis
    
    def test_analyze_persona_characteristics_overconfident(self, optimizer):
        """測試overconfident型特徵分析"""
        analysis = optimizer.analyze_persona_characteristics("overconfident")
        
        assert analysis["persona"] == "overconfident"
        assert analysis["top_expert_approach"] == "evidence"
        assert analysis["top_scammer_tactic"] == "challenge"
        assert analysis["avg_vulnerability"] < 1.1  # overconfident整體較不脆弱
    
    def test_compare_personas(self, optimizer):
        """測試persona對比"""
        comparison = optimizer.compare_personas()
        
        assert "personas" in comparison
        assert len(comparison["personas"]) == 4
        
        assert "most_vulnerable" in comparison
        assert "least_vulnerable" in comparison
        assert "summary" in comparison
        
        # elderly應該是最脆弱的
        assert comparison["most_vulnerable"][0] == "elderly"
        
        # overconfident應該是最不脆弱的
        assert comparison["least_vulnerable"][0] == "overconfident"
        
        # 驗證summary
        assert comparison["summary"]["total_personas"] == 4
        assert comparison["summary"]["avg_vulnerability"] > 0


class TestWeightConfig:
    """測試WeightConfig數據類"""
    
    def test_weight_config_creation(self):
        """測試創建WeightConfig"""
        config = WeightConfig(
            empathy=0.3,
            clarity=0.2,
            evidence=0.3,
            actionability=0.2
        )
        
        assert config.empathy == 0.3
        assert config.clarity == 0.2
        assert config.evidence == 0.3
        assert config.actionability == 0.2
        assert config.timing == 0.0  # 默認值
    
    def test_weight_config_with_timing(self):
        """測試帶timing的WeightConfig"""
        config = WeightConfig(
            empathy=0.25,
            clarity=0.25,
            evidence=0.25,
            actionability=0.20,
            timing=0.05
        )
        
        assert config.timing == 0.05


class TestIntegration:
    """整合測試"""
    
    def test_full_workflow_elderly(self):
        """測試elderly型完整工作流程"""
        optimizer = AdaptiveWeightOptimizer()
        
        # 1. 獲取專家權重
        expert_weights = optimizer.get_expert_weights("elderly")
        assert sum(expert_weights.values()) == pytest.approx(1.0)
        
        # 2. 計算專家加權分數
        base_scores = {
            "empathy": 85,
            "clarity": 70,
            "evidence": 65,
            "actionability": 80
        }
        expert_score = optimizer.calculate_weighted_expert_score(base_scores, "elderly")
        assert 70 <= expert_score <= 85
        
        # 3. 獲取騙徒乘數
        scammer_multipliers = optimizer.get_scammer_multipliers("elderly")
        assert scammer_multipliers["authority"] > 1.0
        
        # 4. 應用騙徒策略乘數
        adjusted_change = optimizer.apply_scammer_multiplier(10, "authority", "elderly")
        assert adjusted_change > 10  # 應該被放大
        
        # 5. 分析特徵
        analysis = optimizer.analyze_persona_characteristics("elderly")
        assert analysis["top_expert_approach"] == "empathy"
    
    def test_full_workflow_overconfident(self):
        """測試overconfident型完整工作流程"""
        optimizer = AdaptiveWeightOptimizer()
        
        # 1. 獲取專家權重
        expert_weights = optimizer.get_expert_weights("overconfident")
        assert expert_weights["evidence"] == 0.40  # 最高權重
        
        # 2. 計算專家加權分數
        base_scores = {
            "empathy": 60,
            "clarity": 75,
            "evidence": 90,
            "actionability": 70
        }
        expert_score = optimizer.calculate_weighted_expert_score(base_scores, "overconfident")
        assert expert_score > 75  # evidence高分應該拉高總分
        
        # 3. 應用騙徒策略乘數
        authority_change = optimizer.apply_scammer_multiplier(10, "authority", "overconfident")
        assert authority_change < 10  # authority對overconfident效果差
        
        challenge_change = optimizer.apply_scammer_multiplier(10, "challenge", "overconfident")
        assert challenge_change > 10  # challenge對overconfident效果好
    
    def test_persona_comparison(self):
        """測試persona對比功能"""
        optimizer = AdaptiveWeightOptimizer()
        
        comparison = optimizer.compare_personas()
        
        # 驗證所有persona都被分析
        assert "elderly" in comparison["personas"]
        assert "average" in comparison["personas"]
        assert "overconfident" in comparison["personas"]
        assert "student" in comparison["personas"]
        
        # 驗證脆弱度排序
        elderly_vuln = comparison["personas"]["elderly"]["avg_vulnerability"]
        overconfident_vuln = comparison["personas"]["overconfident"]["avg_vulnerability"]
        assert elderly_vuln > overconfident_vuln


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])
