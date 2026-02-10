"""
WebSocket實時推送
提供實時評估結果和監控數據推送
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
import asyncio
import json
import logging
from datetime import datetime

from utils.scoring_monitor import get_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket連接管理器"""
    
    def __init__(self):
        # 活躍連接
        self.active_connections: Set[WebSocket] = set()
        # 訂閱頻道
        self.subscriptions: Dict[str, Set[WebSocket]] = {
            "evaluations": set(),  # 評估結果
            "monitoring": set(),   # 監控數據
            "alerts": set()        # 告警信息
        }
        # 廣播任務
        self.broadcast_task = None
        
    async def connect(self, websocket: WebSocket):
        """接受新連接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"新WebSocket連接: {websocket.client}")
        
        # 發送歡迎消息
        await self.send_personal_message(websocket, {
            "type": "connected",
            "message": "WebSocket連接成功",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """斷開連接"""
        self.active_connections.discard(websocket)
        
        # 從所有訂閱中移除
        for channel in self.subscriptions.values():
            channel.discard(websocket)
        
        logger.info(f"WebSocket連接斷開: {websocket.client}")
    
    def subscribe(self, websocket: WebSocket, channel: str):
        """訂閱頻道"""
        if channel in self.subscriptions:
            self.subscriptions[channel].add(websocket)
            logger.info(f"訂閱頻道: {channel}")
            return True
        return False
    
    def unsubscribe(self, websocket: WebSocket, channel: str):
        """取消訂閱"""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(websocket)
            logger.info(f"取消訂閱: {channel}")
            return True
        return False
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """發送個人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"發送消息失敗: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """向頻道廣播消息"""
        if channel not in self.subscriptions:
            return
        
        disconnected = set()
        
        for websocket in self.subscriptions[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"廣播失敗: {e}")
                disconnected.add(websocket)
        
        # 清理斷開的連接
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: dict):
        """向所有連接廣播"""
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"廣播失敗: {e}")
                disconnected.add(websocket)
        
        # 清理斷開的連接
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def start_monitoring_broadcast(self):
        """啟動監控數據廣播"""
        if self.broadcast_task is not None:
            return
        
        self.broadcast_task = asyncio.create_task(self._monitoring_loop())
        logger.info("監控數據廣播已啟動")
    
    async def stop_monitoring_broadcast(self):
        """停止監控數據廣播"""
        if self.broadcast_task is not None:
            self.broadcast_task.cancel()
            self.broadcast_task = None
            logger.info("監控數據廣播已停止")
    
    async def _monitoring_loop(self):
        """監控數據廣播循環"""
        monitor = get_monitor()
        
        while True:
            try:
                # 每5秒廣播一次監控數據
                await asyncio.sleep(5)
                
                if not self.subscriptions["monitoring"]:
                    continue
                
                # 獲取監控數據
                stats = monitor.get_stats()
                recent_metrics = monitor.get_recent_metrics(limit=5)
                
                # 廣播到監控頻道
                await self.broadcast_to_channel("monitoring", {
                    "type": "monitoring_update",
                    "data": {
                        "stats": stats,
                        "recent_metrics": recent_metrics
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"監控廣播錯誤: {e}")


# 全局連接管理器
manager = ConnectionManager()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket連接端點
    
    客戶端可以通過此端點建立WebSocket連接，
    然後訂閱不同的頻道接收實時數據
    """
    await manager.connect(websocket)
    
    # 啟動監控廣播（如果還沒啟動）
    await manager.start_monitoring_broadcast()
    
    try:
        while True:
            # 接收客戶端消息
            data = await websocket.receive_json()
            
            # 處理訂閱請求
            if data.get("action") == "subscribe":
                channel = data.get("channel")
                if manager.subscribe(websocket, channel):
                    await manager.send_personal_message(websocket, {
                        "type": "subscribed",
                        "channel": channel,
                        "message": f"已訂閱頻道: {channel}",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await manager.send_personal_message(websocket, {
                        "type": "error",
                        "message": f"無效的頻道: {channel}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 處理取消訂閱請求
            elif data.get("action") == "unsubscribe":
                channel = data.get("channel")
                if manager.unsubscribe(websocket, channel):
                    await manager.send_personal_message(websocket, {
                        "type": "unsubscribed",
                        "channel": channel,
                        "message": f"已取消訂閱: {channel}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 處理ping請求
            elif data.get("action") == "ping":
                await manager.send_personal_message(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            # 處理獲取狀態請求
            elif data.get("action") == "get_status":
                await manager.send_personal_message(websocket, {
                    "type": "status",
                    "data": {
                        "active_connections": len(manager.active_connections),
                        "subscriptions": {
                            channel: len(subs)
                            for channel, subs in manager.subscriptions.items()
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                })
            
            else:
                await manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": f"未知的操作: {data.get('action')}",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket錯誤: {e}")
        manager.disconnect(websocket)


async def broadcast_evaluation_result(result: dict):
    """
    廣播評估結果
    
    當有新的評估完成時調用此函數
    """
    await manager.broadcast_to_channel("evaluations", {
        "type": "evaluation_result",
        "data": result,
        "timestamp": datetime.now().isoformat()
    })


async def broadcast_alert(alert: dict):
    """
    廣播告警信息
    
    當系統檢測到異常時調用此函數
    """
    await manager.broadcast_to_channel("alerts", {
        "type": "alert",
        "data": alert,
        "timestamp": datetime.now().isoformat()
    })


@router.get("/status")
async def get_websocket_status():
    """
    獲取WebSocket狀態
    
    返回當前活躍連接數和訂閱統計
    """
    return {
        "success": True,
        "active_connections": len(manager.active_connections),
        "subscriptions": {
            channel: len(subs)
            for channel, subs in manager.subscriptions.items()
        },
        "available_channels": list(manager.subscriptions.keys()),
        "timestamp": datetime.now().isoformat()
    }


# 使用示例
"""
# JavaScript客戶端示例

// 建立WebSocket連接
const ws = new WebSocket('ws://localhost:8000/api/v2/ws/connect');

// 連接成功
ws.onopen = () => {
    console.log('WebSocket連接成功');
    
    // 訂閱評估結果頻道
    ws.send(JSON.stringify({
        action: 'subscribe',
        channel: 'evaluations'
    }));
    
    // 訂閱監控數據頻道
    ws.send(JSON.stringify({
        action: 'subscribe',
        channel: 'monitoring'
    }));
};

// 接收消息
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'connected':
            console.log('連接確認:', message.message);
            break;
        
        case 'subscribed':
            console.log('訂閱成功:', message.channel);
            break;
        
        case 'evaluation_result':
            console.log('新評估結果:', message.data);
            // 更新UI顯示評估結果
            break;
        
        case 'monitoring_update':
            console.log('監控數據更新:', message.data);
            // 更新儀表板
            break;
        
        case 'alert':
            console.log('告警:', message.data);
            // 顯示告警通知
            break;
    }
};

// 連接關閉
ws.onclose = () => {
    console.log('WebSocket連接關閉');
};

// 錯誤處理
ws.onerror = (error) => {
    console.error('WebSocket錯誤:', error);
};

// 發送ping保持連接
setInterval(() => {
    ws.send(JSON.stringify({ action: 'ping' }));
}, 30000);
"""
