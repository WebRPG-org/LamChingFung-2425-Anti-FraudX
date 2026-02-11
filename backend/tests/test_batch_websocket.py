"""
批量評估和WebSocket功能測試
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 創建測試應用
app = FastAPI()

try:
    from backend.api.batch_routes import router as batch_router
    from backend.api.websocket_routes import router as ws_router
    
    app.include_router(batch_router)
    app.include_router(ws_router)
except ImportError:
    # 如果導入失敗，創建模擬路由
    pass

client = TestClient(app)


class TestBatchEvaluation:
    """測試批量評估功能"""
    
    def test_batch_evaluate_success(self):
        """測試批量評估成功"""
        request_data = {
            "conversations": [
                {
                    "conversation_id": "test_001",
                    "conversation_history": [
                        {"role": "scammer", "content": "你好，我是警察", "strategy": "authority"},
                        {"role": "victim", "content": "有什麼事嗎？"}
                    ],
                    "persona_type": "average",
                    "initial_trust": 50
                },
                {
                    "conversation_id": "test_002",
                    "conversation_history": [
                        {"role": "scammer", "content": "恭喜中獎", "strategy": "greed"},
                        {"role": "victim", "content": "真的嗎？"}
                    ],
                    "persona_type": "student",
                    "initial_trust": 40
                }
            ],
            "rule_weight": 1.0,
            "agent_weight": 0.0,
            "enable_agent_scoring": False,
            "max_concurrent": 2
        }
        
        response = client.post("/api/v2/batch/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["total_conversations"] == 2
        assert data["successful_evaluations"] >= 0
        assert len(data["results"]) == 2
        
        # 檢查每個結果
        for result in data["results"]:
            assert "conversation_id" in result
            assert "success" in result
    
    def test_batch_evaluate_empty(self):
        """測試空對話列表"""
        request_data = {
            "conversations": [],
            "rule_weight": 0.7,
            "agent_weight": 0.3
        }
        
        response = client.post("/api/v2/batch/evaluate", json=request_data)
        
        assert response.status_code == 400
        assert "對話列表不能為空" in response.json()["detail"]
    
    def test_batch_evaluate_too_many(self):
        """測試超過最大數量"""
        request_data = {
            "conversations": [
                {
                    "conversation_history": [
                        {"role": "scammer", "content": "測試", "strategy": "none"},
                        {"role": "victim", "content": "測試"}
                    ],
                    "persona_type": "average"
                }
            ] * 101,  # 超過100個
            "rule_weight": 0.7,
            "agent_weight": 0.3
        }
        
        response = client.post("/api/v2/batch/evaluate", json=request_data)
        
        assert response.status_code == 400
        assert "最多評估100個對話" in response.json()["detail"]
    
    def test_batch_evaluate_invalid_weights(self):
        """測試無效權重"""
        request_data = {
            "conversations": [
                {
                    "conversation_history": [
                        {"role": "scammer", "content": "測試", "strategy": "none"},
                        {"role": "victim", "content": "測試"}
                    ],
                    "persona_type": "average"
                }
            ],
            "rule_weight": 0.5,
            "agent_weight": 0.3  # 總和不為1.0
        }
        
        response = client.post("/api/v2/batch/evaluate", json=request_data)
        
        assert response.status_code == 400
        assert "權重總和必須為1.0" in response.json()["detail"]
    
    def test_batch_status(self):
        """測試獲取批量評估狀態"""
        response = client.get("/api/v2/batch/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "evaluator_cache_size" in data
        assert "max_concurrent_default" in data
        assert "max_conversations_per_batch" in data
    
    def test_batch_concurrent_control(self):
        """測試併發控制"""
        # 創建10個對話，但限制併發為2
        request_data = {
            "conversations": [
                {
                    "conversation_id": f"test_{i:03d}",
                    "conversation_history": [
                        {"role": "scammer", "content": "測試", "strategy": "none"},
                        {"role": "victim", "content": "測試"}
                    ],
                    "persona_type": "average",
                    "initial_trust": 50
                }
                for i in range(10)
            ],
            "rule_weight": 1.0,
            "agent_weight": 0.0,
            "enable_agent_scoring": False,
            "max_concurrent": 2
        }
        
        response = client.post("/api/v2/batch/evaluate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_conversations"] == 10
        # 併發控制不應影響結果數量
        assert len(data["results"]) == 10


class TestWebSocket:
    """測試WebSocket功能"""
    
    def test_websocket_status(self):
        """測試WebSocket狀態端點"""
        response = client.get("/api/v2/ws/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "active_connections" in data
        assert "subscriptions" in data
        assert "available_channels" in data
        
        # 檢查可用頻道
        channels = data["available_channels"]
        assert "evaluations" in channels
        assert "monitoring" in channels
        assert "alerts" in channels
    
    def test_websocket_connect(self):
        """測試WebSocket連接"""
        with client.websocket_connect("/api/v2/ws/connect") as websocket:
            # 接收歡迎消息
            data = websocket.receive_json()
            
            assert data["type"] == "connected"
            assert "message" in data
            assert "timestamp" in data
    
    def test_websocket_subscribe(self):
        """測試訂閱頻道"""
        with client.websocket_connect("/api/v2/ws/connect") as websocket:
            # 接收歡迎消息
            websocket.receive_json()
            
            # 訂閱評估頻道
            websocket.send_json({
                "action": "subscribe",
                "channel": "evaluations"
            })
            
            # 接收訂閱確認
            data = websocket.receive_json()
            
            assert data["type"] == "subscribed"
            assert data["channel"] == "evaluations"
    
    def test_websocket_unsubscribe(self):
        """測試取消訂閱"""
        with client.websocket_connect("/api/v2/ws/connect") as websocket:
            websocket.receive_json()
            
            # 先訂閱
            websocket.send_json({
                "action": "subscribe",
                "channel": "monitoring"
            })
            websocket.receive_json()
            
            # 再取消訂閱
            websocket.send_json({
                "action": "unsubscribe",
                "channel": "monitoring"
            })
            
            data = websocket.receive_json()
            
            assert data["type"] == "unsubscribed"
            assert data["channel"] == "monitoring"
    
    def test_websocket_ping(self):
        """測試ping/pong"""
        with client.websocket_connect("/api/v2/ws/connect") as websocket:
            websocket.receive_json()
            
            # 發送ping
            websocket.send_json({"action": "ping"})
            
            # 接收pong
            data = websocket.receive_json()
            
            assert data["type"] == "pong"
            assert "timestamp" in data
    
    def test_websocket_get_status(self):
        """測試獲取WebSocket狀態"""
        with client.websocket_connect("/api/v2/ws/connect") as websocket:
            websocket.receive_json()
            
            # 請求狀態
            websocket.send_json({"action": "get_status"})
            
            # 接收狀態
            data = websocket.receive_json()
            
            assert data["type"] == "status"
            assert "active_connections" in data["data"]
            assert "subscriptions" in data["data"]
    
    def test_websocket_invalid_action(self):
        """測試無效操作"""
        with client.websocket_connect("/api/v2/ws/connect") as websocket:
            websocket.receive_json()
            
            # 發送無效操作
            websocket.send_json({"action": "invalid_action"})
            
            # 接收錯誤消息
            data = websocket.receive_json()
            
            assert data["type"] == "error"
            assert "未知的操作" in data["message"]
    
    def test_websocket_invalid_channel(self):
        """測試訂閱無效頻道"""
        with client.websocket_connect("/api/v2/ws/connect") as websocket:
            websocket.receive_json()
            
            # 訂閱無效頻道
            websocket.send_json({
                "action": "subscribe",
                "channel": "invalid_channel"
            })
            
            # 接收錯誤消息
            data = websocket.receive_json()
            
            assert data["type"] == "error"
            assert "無效的頻道" in data["message"]


class TestIntegration:
    """測試批量評估和WebSocket集成"""
    
    def test_batch_with_websocket_notification(self):
        """測試批量評估時的WebSocket通知"""
        # 這個測試需要實際的集成環境
        # 這裡只是示例結構
        pass
    
    def test_concurrent_batch_evaluations(self):
        """測試併發批量評估"""
        # 測試多個批量評估請求同時進行
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
