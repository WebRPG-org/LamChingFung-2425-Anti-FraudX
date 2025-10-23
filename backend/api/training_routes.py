import os
import asyncio
import json
import time
import shutil
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.logger import log

# Use the core routine of the training flow; one round produces analysis and saves records
from scripts.training_runner import run_training_round  # Each call runs one round and saves multiple files


router = APIRouter()

# Runtime state variables
_loop_task: Optional[asyncio.Task] = None
_stop_event: Optional[asyncio.Event] = None
_interval_seconds: float = 5.0
_current_round: int = 1
_mode: str = "fast"


# File paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TRAINING_DATA_DIR = os.path.join(BASE_DIR, 'training_data')


class StartLoopRequest(BaseModel):
    interval_seconds: Optional[float] = 5.0
    mode: Optional[str] = "fast"  # fast | demo


async def _training_loop():
    global _current_round
    log.info(f"Training loop started, interval={_interval_seconds}s")
    try:
        while _stop_event and not _stop_event.is_set():
            try:
                success, files = await run_training_round(_current_round, mode=_mode)
                log.info(f"Round #{_current_round} finished: success={success}, files={len(files)}")
            except Exception as e:
                log.error(f"Training loop error on round #{_current_round}: {e}")

            _current_round += 1

            if _stop_event.is_set():
                break

            try:
                # Support interruptible wait
                await asyncio.wait_for(_stop_event.wait(), timeout=max(0.1, _interval_seconds))
            except asyncio.TimeoutError:
                # Normal timeout, proceed to next round
                pass
    finally:
        log.info("Training loop stopped")


@router.post("/api/training/loop/start")
async def start_training_loop(req: Optional[StartLoopRequest] = None):
    """啟動循環訓練（背景執行）。"""
    global _loop_task, _stop_event, _interval_seconds, _mode

    if _loop_task and not _loop_task.done():
        return {"status": "already_running", "interval_seconds": _interval_seconds}

    _interval_seconds = float((req and req.interval_seconds) or 5.0)
    _mode = (req and req.mode) or "fast"
    _stop_event = asyncio.Event()
    _loop_task = asyncio.create_task(_training_loop())

    return {"status": "started", "interval_seconds": _interval_seconds, "mode": _mode}


@router.post("/api/training/loop/stop")
async def stop_training_loop():
    """停止循環訓練。"""
    global _loop_task, _stop_event

    if not _loop_task or _loop_task.done():
        return {"status": "not_running"}

    if _stop_event:
        _stop_event.set()

    # Do not force awaiting completion; return immediately
    return {"status": "stopping"}


@router.get("/api/training/status")
async def training_status():
    """查詢循環訓練狀態。"""
    running = bool(_loop_task and not _loop_task.done())
    return {
        "status": "running" if running else "stopped",
        "running": running,
        "interval_seconds": _interval_seconds,
        "current_round": _current_round,
    }


def _safe_join_training_file(filename: str) -> str:
    # Basic path traversal protection
    if not filename or os.path.sep in filename or os.path.altsep and os.path.altsep in filename:
        raise HTTPException(status_code=400, detail="invalid filename")
    return os.path.join(TRAINING_DATA_DIR, filename)


@router.get("/api/training/records")
async def list_training_records(limit: int = 50, include_content: bool = False):
    """列出訓練記錄（從 backend/training_data 讀取）。"""
    if not os.path.isdir(TRAINING_DATA_DIR):
        return {"status": "success", "data": {"records": []}}

    files = [f for f in os.listdir(TRAINING_DATA_DIR) if f.endswith('.json')]
    # Sort by modification time (desc)
    files.sort(key=lambda f: os.path.getmtime(os.path.join(TRAINING_DATA_DIR, f)), reverse=True)
    files = files[: max(1, min(limit, 500))]

    records: List[Dict[str, Any]] = []
    for fname in files:
        fpath = os.path.join(TRAINING_DATA_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            log.warning(f"Skip unreadable record {fname}: {e}")
            continue

        analysis = data.get("analysis", {})
        metadata = data.get("metadata", {})
        record = {
            "id": fname,
            "filename": fname,
            "path": f"backend/training_data/{fname}",
            "outcome": analysis.get("outcome"),
            "victim_persona": analysis.get("victim_persona"),
            "scam_tactic": analysis.get("scam_tactic"),
            "timestamp": analysis.get("timestamp") or metadata.get("datetime"),
            "round_number": metadata.get("round_number"),
            "attempt_number": metadata.get("attempt_number"),
            "file_size": os.path.getsize(fpath),
            "created_at": os.path.getmtime(fpath),
        }

        if include_content:
            record["content"] = data

        records.append(record)

    return {"status": "success", "data": {"records": records}}


@router.get("/api/training/records/{record_id}")
async def get_training_record(record_id: str):
    """取得單一訓練記錄的完整內容。"""
    if not os.path.isdir(TRAINING_DATA_DIR):
        raise HTTPException(status_code=404, detail="no training_data directory")

    file_path = _safe_join_training_file(record_id)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="record not found")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to read record: {e}")

    return {"status": "success", "data": data}


class CleanupRequest(BaseModel):
    older_than_days: Optional[int] = None
    match_prefix: Optional[str] = None  # e.g., "training_data_r"
    action: Optional[str] = "archive"   # archive | delete
    require_confirm: Optional[bool] = False  # must be true for delete
    archive_dir: Optional[str] = None   # default to TRAINING_DATA_DIR/_archive



