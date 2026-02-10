"""
評分系統端到端測試
測試完整的API整合流程
"""

import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi.testclient import TestClient
from backend.main import app  # 假設主應用在這裡

# 如果main.py不存在，使用模擬的app
try:
    from backend.main import app
except ImportError:
    from fastapi import FastAPI
    from backend.api.scoring_v2_routes import router
    
    app = FastAPI()
    app.include_router(router)

client = TestClient(app)


class TestScoringAPIv2:
    """測試評分API v2"""
    
    def test_health_check(self):
        """測試健康檢查"""
        response = client.get("/api/v2/scoring/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0"
        assert "evaluator_cache_size" in data
        assert "timestamp" in data
    
    def test_evaluate_simple_conversation(self):
        """測試簡單對話評估"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "你好，我是警察", "strategy": "authority"},
                {"role": "victim", "content": "有什麼事嗎？"}
            ],
            "persona_type": "average",
            "initial_trust": 50,
            "rule_weight": 0.7,
            "agent_weight": 0.3,
            "enable_agent_scoring": True
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "trust_change" in data
        assert "confidence" in data
        assert data["method"] in ["rule", "agent", "hybrid"]
        assert "rule_score" in data
        assert "timestamp" in data
        assert "evaluation_time_ms" in data
    
    def test_evaluate_elderly_persona(self):
        """測試老年人人設"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "奶奶，我是你孫子", "strategy": "sympathy"},
                {"role": "victim", "content": "你是誰？"},
                {"role": "scammer", "content": "我出事了需要錢", "strategy": "urgency"}
            ],
            "persona_type": "elderly",
            "initial_trust": 60
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 老年人應該更容易被情感操控
        assert data["trust_change"] < 0  # 警覺性下降
    
    def test_evaluate_victim_resistance(self):
        """測試受害人抵抗"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "你中獎了", "strategy": "greed"},
                {"role": "victim", "content": "這是詐騙，我要報警"}
            ],
            "persona_type": "student",
            "initial_trust": 30
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 受害人識破騙局，警覺性應該上升
        assert data["trust_change"] > 0
    
    def test_evaluate_pure_rule_mode(self):
        """測試純規則模式"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "緊急通知", "strategy": "urgency"},
                {"role": "victim", "content": "什麼事？"}
            ],
            "persona_type": "average",
            "rule_weight": 1.0,
            "agent_weight": 0.0,
            "enable_agent_scoring": False
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["method"] == "rule"
    
    def test_invalid_conversation_empty(self):
        """測試空對話"""
        request_data = {
            "conversation_history": [],
            "persona_type": "average"
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 400
        assert "對話歷史不能為空" in response.json()["detail"]
    
    def test_invalid_weights(self):
        """測試無效權重"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "測試", "strategy": "none"},
                {"role": "victim", "content": "測試"}
            ],
            "persona_type": "average",
            "rule_weight": 0.5,
            "agent_weight": 0.3  # 總和不為1.0
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 400
        assert "權重總和必須為1.0" in response.json()["detail"]
    
    def test_get_statistics(self):
        """測試獲取統計信息"""
        # 先執行一次評估
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "測試", "strategy": "none"},
                {"role": "victim", "content": "測試"}
            ],
            "persona_type": "average"
        }
        client.post("/api/v2/scoring/evaluate", json=request_data)
        
        # 獲取統計
        response = client.get("/api/v2/scoring/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "cache_size" in data
        assert "evaluators" in data
        assert "timestamp" in data
    
    def test_clear_cache(self):
        """測試清除緩存"""
        # 先執行一次評估創建緩存
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "測試", "strategy": "none"},
                {"role": "victim", "content": "測試"}
            ],
            "persona_type": "average"
        }
        client.post("/api/v2/scoring/evaluate", json=request_data)
        
        # 清除緩存
        response = client.post("/api/v2/scoring/clear-cache")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "已清除" in data["message"]
    
    def test_multiple_personas(self):
        """測試多個人設"""
        personas = ["elderly", "average", "overconfident", "student"]
        
        for persona in personas:
            request_data = {
                "conversation_history": [
                    {"role": "scammer", "content": "你好", "strategy": "none"},
                    {"role": "victim", "content": "你好"}
                ],
                "persona_type": persona
            }
            
            response = client.post("/api/v2/scoring/evaluate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_performance(self):
        """測試性能"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "測試", "strategy": "none"},
                {"role": "victim", "content": "測試"}
            ],
            "persona_type": "average"
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 評估時間應該小於1秒
        assert data["evaluation_time_ms"] < 1000


class TestScoringAccuracy:
    """測試評分準確性"""
    
    def test_high_pressure_scam(self):
        """測試高壓詐騙案例"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "你好，我是警察局的，你的銀行帳戶涉嫌洗錢！", "strategy": "authority"},
                {"role": "victim", "content": "什麼？我沒有做違法的事啊！"},
                {"role": "scammer", "content": "現在必須立即配合調查，否則會凍結你所有資產！", "strategy": "urgency"}
            ],
            "persona_type": "elderly",
            "initial_trust": 50
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 高壓詐騙應該大幅降低警覺性
        assert data["trust_change"] < -15
    
    def test_victim_alert(self):
        """測試受害人警覺案例"""
        request_data = {
            "conversation_history": [
                {"role": "scammer", "content": "恭喜中獎！", "strategy": "greed"},
                {"role": "victim", "content": "這是詐騙，我要報警"}
            ],
            "persona_type": "overconfident",
            "initial_trust": 30
        }
        
        response = client.post("/api/v2/scoring/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 受害人識破騙局，警覺性應該上升
        assert data["trust_change"] > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
