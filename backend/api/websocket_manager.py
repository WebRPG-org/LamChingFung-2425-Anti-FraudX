import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from utils.logger import log

class WebSocketManager:
    def __init__(self):
        # Active WebSocket connections: simulation_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Stop flags: simulation_id -> bool
        self.stop_flags: Dict[str, bool] = {}
        # Global stop flag: stops all simulations
        self.global_stop_flag: bool = False
        # Heartbeat tasks: simulation_id -> asyncio.Task
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        # Event buffers for replay: simulation_id -> List[dict]
        self.event_buffers: Dict[str, List[dict]] = {}
        # Event sequence numbers: simulation_id -> int
        self.event_seqs: Dict[str, int] = {}

    def should_stop(self, simulation_id: str) -> bool:
        # Check both global and individual stop flags
        return self.global_stop_flag or self.stop_flags.get(simulation_id, False)
    
    def set_stop_flag(self, simulation_id: str, value: bool):
        self.stop_flags[simulation_id] = value
    
    def set_global_stop_flag(self, value: bool):
        """Set global stop flag to stop all simulations"""
        self.global_stop_flag = value
        log.info(f"🛑 Global stop flag set to: {value}")
    
    def stop_all_simulations(self):
        """Stop all running simulations"""
        self.global_stop_flag = True
        # Also set individual flags for all active simulations
        for sim_id in list(self.active_connections.keys()):
            self.stop_flags[sim_id] = True
        log.info(f"🛑 Stopping all simulations ({len(self.active_connections)} active)")

    def reset_simulation_state(self, simulation_id: str, clear_stop_flag: bool = True):
        """Reset state for a new simulation run"""
        if clear_stop_flag:
            self.stop_flags[simulation_id] = False
            # Only clear global flag if user explicitly starts a new simulation
            self.global_stop_flag = False
        self.event_buffers[simulation_id] = []
        self.event_seqs[simulation_id] = 0

    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        self.active_connections[simulation_id] = websocket
        
        # Replay recent events (last 10)
        try:
            buf = self.event_buffers.get(simulation_id) or []
            for evt in buf[-10:]:
                try:
                    await websocket.send_json(evt)
                except Exception:
                    break
        except Exception:
            pass

        # Start heartbeat
        self._start_heartbeat(simulation_id)
        log.info(f"WebSocket connected for simulation: {simulation_id}")

        try:
            # Send connection_success
            await websocket.send_json({
                "event_type": "connection_success",
                "payload": {"simulation_id": simulation_id}
            })
            
            # Handle incoming messages
            while simulation_id in self.active_connections:
                try:
                    # Wait for message with timeout to allow checking connection status
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    await self._handle_message(simulation_id, msg, websocket)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    # Connection closed or error
                    break
                    
        except WebSocketDisconnect:
            log.info(f"WebSocket disconnected for simulation: {simulation_id}")
        except Exception as e:
            log.error(f"WebSocket error for simulation {simulation_id}: {e}")
        finally:
            self.disconnect(simulation_id)

    async def _handle_message(self, simulation_id: str, msg: str, websocket: WebSocket):
        try:
            if msg.strip().lower() == 'stop_now':
                await self._handle_stop_command(simulation_id, websocket)
            else:
                data = json.loads(msg)
                cmd = isinstance(data, dict) and data.get('command')
                if cmd == 'stop_now':
                    await self._handle_stop_command(simulation_id, websocket)
                elif cmd == 'replay':
                    await self._handle_replay_command(simulation_id, websocket)
        except Exception as e:
            log.debug(f"WebSocket message handling error: {e}")

    async def _handle_stop_command(self, simulation_id: str, websocket: WebSocket):
        log.warning(f"🛑 Received stop command for simulation {simulation_id}")
        # Stop all simulations, not just this one
        self.stop_all_simulations()
        await websocket.send_json({
            "event_type": "ack", 
            "payload": {"command": "stop_now", "ok": True, "message": "Stopping all simulations..."}
        })
        # Force close to exit quickly
        await websocket.close(code=1000, reason="User stop")

    async def _handle_replay_command(self, simulation_id: str, websocket: WebSocket):
        buf = self.event_buffers.get(simulation_id) or []
        for evt in buf[-20:]:
            try:
                await websocket.send_json(evt)
            except Exception:
                break
        await websocket.send_json({
            "event_type": "ack", 
            "payload": {"command": "replay", "ok": True}
        })

    def disconnect(self, simulation_id: str):
        if simulation_id in self.active_connections:
            del self.active_connections[simulation_id]
        
        task = self.heartbeat_tasks.pop(simulation_id, None)
        if task and not task.done():
            task.cancel()

    def _start_heartbeat(self, simulation_id: str):
        # Cancel old if exists
        old = self.heartbeat_tasks.get(simulation_id)
        if old and not old.done():
            old.cancel()
            
        async def _heartbeat_loop(sim_id: str):
            try:
                while sim_id in self.active_connections:
                    try:
                        await self.send_event(sim_id, "heartbeat", {"ts": datetime.now().isoformat()})
                    except Exception:
                        break
                    await asyncio.sleep(15)
            except Exception:
                pass

        self.heartbeat_tasks[simulation_id] = asyncio.create_task(_heartbeat_loop(simulation_id))

    async def send_event(self, simulation_id: str, event_type: str, payload: dict):
        """Send a WebSocket event and buffer it"""
        try:
            seq = self.event_seqs.get(simulation_id, 0) + 1
            self.event_seqs[simulation_id] = seq
            
            evt = {"seq": seq, "event_type": event_type, "payload": payload}
            
            # Buffer logic
            if simulation_id not in self.event_buffers:
                self.event_buffers[simulation_id] = []
            buf = self.event_buffers[simulation_id]
            buf.append(evt)
            if len(buf) > 100:
                del buf[: len(buf) - 100]
            
            # Send logic
            if simulation_id in self.active_connections:
                # Yield to event loop
                await asyncio.sleep(0)
                await self.active_connections[simulation_id].send_json(evt)
                
        except Exception as e:
            log.error(f"Failed to send WebSocket event: {e}")

    def get_events(self, simulation_id: str, since_seq: Optional[int] = None) -> dict:
        buf = self.event_buffers.get(simulation_id) or []
        if since_seq is None:
            events = buf[-50:]
        else:
            try:
                cutoff = int(since_seq)
            except Exception:
                cutoff = 0
            events = [e for e in buf if int(e.get('seq', 0)) > cutoff][-200:]
            
        next_seq = int(self.event_seqs.get(simulation_id, len(buf)))
        return {"events": events, "next_seq": next_seq}

# Global instance
manager = WebSocketManager()
