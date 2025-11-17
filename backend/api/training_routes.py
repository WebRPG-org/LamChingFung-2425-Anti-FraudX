import os
import asyncio
import json
import time
import shutil
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.logger import log

router = APIRouter()

# File paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TRAINING_DATA_DIR = os.path.join(BASE_DIR, 'training_data')


@router.get("/api/training/status")
async def training_status():
    """查詢訓練狀態（包含統計信息）。"""
    
    # Calculate statistics from training data
    stats = {
        "total_records": 0,
        "success_count": 0,
        "failure_count": 0,
        "partial_count": 0,
        "persona_distribution": {"elderly": 0, "average": 0, "overconfident": 0},
        "avg_trust_scammer": 0.0,
        "avg_trust_expert": 0.0,
        "avg_scammer_score": 0.0,
        "avg_expert_score": 0.0
    }
    
    if os.path.isdir(TRAINING_DATA_DIR):
        files = [f for f in os.listdir(TRAINING_DATA_DIR) if f.endswith('.json') and not f.endswith('_error.json')]
        stats["total_records"] = len(files)
        
        trust_scammer_sum = 0
        trust_expert_sum = 0
        scammer_score_sum = 0
        expert_score_sum = 0
        valid_records = 0
        
        for fname in files[:100]:  # Limit to last 100 files for performance
            fpath = os.path.join(TRAINING_DATA_DIR, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                analysis = data.get("analysis", {})
                outcome = analysis.get("outcome", "PARTIAL")
                if outcome == "SUCCESS":
                    stats["success_count"] += 1
                elif outcome == "FAILURE":
                    stats["failure_count"] += 1
                else:
                    stats["partial_count"] += 1
                
                # Persona distribution
                victim_persona = analysis.get("victim_persona") or data.get("metadata", {}).get("victim_persona")
                if victim_persona in stats["persona_distribution"]:
                    stats["persona_distribution"][victim_persona] += 1
                
                # Trust and performance scores
                trust_tracking = data.get("trust_tracking", {})
                performance_tracking = data.get("performance_tracking", {})
                
                if trust_tracking:
                    final = trust_tracking.get("final", {})
                    if isinstance(final, dict):
                        trust_scammer = final.get("trust_in_scammer", 50)
                        trust_expert = final.get("trust_in_expert", 50)
                        trust_scammer_sum += trust_scammer
                        trust_expert_sum += trust_expert
                        valid_records += 1
                
                if performance_tracking:
                    scammer_perf = performance_tracking.get("scammer", {})
                    expert_perf = performance_tracking.get("expert", {})
                    if isinstance(scammer_perf, dict):
                        scammer_score_sum += scammer_perf.get("overall_score", 50)
                    if isinstance(expert_perf, dict):
                        expert_score_sum += expert_perf.get("overall_score", 50)
                        
            except Exception as e:
                log.warning(f"Error reading training record {fname}: {e}")
                continue
        
        if valid_records > 0:
            stats["avg_trust_scammer"] = round(trust_scammer_sum / valid_records, 2)
            stats["avg_trust_expert"] = round(trust_expert_sum / valid_records, 2)
        if stats["total_records"] > 0:
            stats["avg_scammer_score"] = round(scammer_score_sum / stats["total_records"], 2)
            stats["avg_expert_score"] = round(expert_score_sum / stats["total_records"], 2)
    
    return {
        "status": "active",
        "statistics": stats
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



