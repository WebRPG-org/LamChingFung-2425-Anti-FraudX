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


# ============================================================================
# Scraper API
# ============================================================================

_scraper_process = None
_scraper_log: List[str] = []

@router.post("/api/tools/scraper/run")
async def run_scraper():
    """觸發爬蟲抓取 ADCC 詐騙警示資料"""
    global _scraper_process, _scraper_log
    if _scraper_process and _scraper_process.returncode is None:
        return {"success": False, "message": "爬蟲正在運行中，請稍候"}
    _scraper_log = []
    script_path = os.path.join(BASE_DIR, 'scripts', 'scraper.py')
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="scraper.py 不存在")
    try:
        _scraper_process = await asyncio.create_subprocess_exec(
            'python', script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=BASE_DIR
        )
        asyncio.create_task(_read_scraper_output(_scraper_process))
        return {"success": True, "message": "爬蟲已啟動", "pid": _scraper_process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _read_scraper_output(proc):
    global _scraper_log
    async for line in proc.stdout:
        _scraper_log.append(line.decode('utf-8', errors='replace').rstrip())
        if len(_scraper_log) > 500:
            _scraper_log = _scraper_log[-500:]
    await proc.wait()

@router.get("/api/tools/scraper/status")
async def scraper_status():
    """查詢爬蟲狀態與日誌"""
    global _scraper_process, _scraper_log
    running = _scraper_process is not None and _scraper_process.returncode is None
    # 計算已爬取的資料數量
    data_file = os.path.join(BASE_DIR, '..', 'data', 'scraped_alerts.json')
    data_count = 0
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data_count = len(json.load(f))
        except Exception:
            pass
    return {
        "running": running,
        "exit_code": _scraper_process.returncode if _scraper_process else None,
        "log": _scraper_log[-100:],
        "data_count": data_count
    }


# ============================================================================
# Fine-tune API
# ============================================================================

_finetune_process = None
_finetune_log: List[str] = []

@router.post("/api/tools/finetune/run")
async def run_finetune():
    """觸發 Fine-tune 數據生成與訓練"""
    global _finetune_process, _finetune_log
    if _finetune_process and _finetune_process.returncode is None:
        return {"success": False, "message": "Fine-tune 正在運行中，請稍候"}
    _finetune_log = []
    script_path = os.path.join(BASE_DIR, 'scripts', 'generate_finetuning_data.py')
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="generate_finetuning_data.py 不存在")
    try:
        _finetune_process = await asyncio.create_subprocess_exec(
            'python', script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=BASE_DIR
        )
        asyncio.create_task(_read_finetune_output(_finetune_process))
        return {"success": True, "message": "Fine-tune 已啟動", "pid": _finetune_process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _read_finetune_output(proc):
    global _finetune_log
    async for line in proc.stdout:
        _finetune_log.append(line.decode('utf-8', errors='replace').rstrip())
        if len(_finetune_log) > 500:
            _finetune_log = _finetune_log[-500:]
    await proc.wait()

@router.get("/api/tools/finetune/status")
async def finetune_status():
    """查詢 Fine-tune 狀態與日誌"""
    global _finetune_process, _finetune_log
    running = _finetune_process is not None and _finetune_process.returncode is None
    # 計算 fine-tuning 資料數量
    ft_dir = os.path.join(BASE_DIR, 'training_data', 'finetuning')
    ft_count = 0
    if os.path.exists(ft_dir):
        ft_count = len([f for f in os.listdir(ft_dir) if f.endswith('.jsonl') or f.endswith('.json')])
    return {
        "running": running,
        "exit_code": _finetune_process.returncode if _finetune_process else None,
        "log": _finetune_log[-100:],
        "ft_file_count": ft_count
    }

@router.get("/api/tools/finetune/files")
async def list_finetune_files():
    """列出 fine-tuning 輸出檔案"""
    ft_dir = os.path.join(BASE_DIR, 'training_data', 'finetuning')
    if not os.path.exists(ft_dir):
        return {"files": []}
    files = []
    for f in sorted(os.listdir(ft_dir), reverse=True):
        fpath = os.path.join(ft_dir, f)
        if os.path.isfile(fpath):
            files.append({
                "name": f,
                "size": os.path.getsize(fpath),
                "modified": os.path.getmtime(fpath)
            })
    return {"files": files[:50]}


# ============================================================================
# Training Runner API (訓練模擬)
# ============================================================================

_training_process = None
_training_log: List[str] = []

@router.post("/api/tools/training/run")
async def run_training(rounds: int = 3):
    """觸發 AI 三方對話訓練模擬"""
    global _training_process, _training_log
    if _training_process and _training_process.returncode is None:
        return {"success": False, "message": "訓練正在運行中，請稍候"}
    _training_log = []
    script_path = os.path.join(BASE_DIR, 'scripts', 'training_runner.py')
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="training_runner.py 不存在")
    try:
        env = os.environ.copy()
        env['TRAINING_ROUNDS'] = str(max(1, min(rounds, 20)))
        _training_process = await asyncio.create_subprocess_exec(
            'python', script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=BASE_DIR,
            env=env
        )
        asyncio.create_task(_read_training_output(_training_process))
        return {"success": True, "message": f"訓練已啟動（{rounds} 輪）", "pid": _training_process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _read_training_output(proc):
    global _training_log
    async for line in proc.stdout:
        _training_log.append(line.decode('utf-8', errors='replace').rstrip())
        if len(_training_log) > 1000:
            _training_log = _training_log[-1000:]
    await proc.wait()

@router.get("/api/tools/training/status")
async def training_run_status():
    """查詢訓練模擬狀態與日誌"""
    global _training_process, _training_log
    running = _training_process is not None and _training_process.returncode is None
    # 計算訓練記錄數
    record_count = 0
    if os.path.isdir(TRAINING_DATA_DIR):
        record_count = len([f for f in os.listdir(TRAINING_DATA_DIR) if f.endswith('.json')])
    return {
        "running": running,
        "exit_code": _training_process.returncode if _training_process else None,
        "log": _training_log[-150:],
        "record_count": record_count
    }

@router.post("/api/tools/training/stop")
async def stop_training():
    """停止訓練模擬"""
    global _training_process
    if _training_process and _training_process.returncode is None:
        _training_process.terminate()
        return {"success": True, "message": "已發送停止信號"}
    return {"success": False, "message": "訓練未在運行"}


# ============================================================================
# Model Fine-tuning API (生成 Ollama 模型)
# ============================================================================

_modelgen_process = None
_modelgen_log: List[str] = []

@router.post("/api/tools/modelgen/run")
async def run_modelgen():
    """執行 model_fine_tuning.py 生成 Ollama Modelfile 和訓練數據"""
    global _modelgen_process, _modelgen_log
    if _modelgen_process and _modelgen_process.returncode is None:
        return {"success": False, "message": "模型生成正在運行中"}
    _modelgen_log = []
    script_path = os.path.join(BASE_DIR, 'scripts', 'model_fine_tuning.py')
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="model_fine_tuning.py 不存在")
    try:
        _modelgen_process = await asyncio.create_subprocess_exec(
            'python', script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=BASE_DIR
        )
        asyncio.create_task(_read_modelgen_output(_modelgen_process))
        return {"success": True, "message": "模型生成已啟動", "pid": _modelgen_process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _read_modelgen_output(proc):
    global _modelgen_log
    async for line in proc.stdout:
        _modelgen_log.append(line.decode('utf-8', errors='replace').rstrip())
        if len(_modelgen_log) > 500:
            _modelgen_log = _modelgen_log[-500:]
    await proc.wait()

@router.get("/api/tools/modelgen/status")
async def modelgen_status():
    """查詢模型生成狀態"""
    global _modelgen_process, _modelgen_log
    running = _modelgen_process is not None and _modelgen_process.returncode is None
    # 列出 models 目錄
    models_dir = os.path.join(BASE_DIR, 'models')
    model_files = []
    if os.path.exists(models_dir):
        for f in os.listdir(models_dir):
            fpath = os.path.join(models_dir, f)
            if os.path.isfile(fpath):
                model_files.append({"name": f, "size": os.path.getsize(fpath)})
    return {
        "running": running,
        "exit_code": _modelgen_process.returncode if _modelgen_process else None,
        "log": _modelgen_log[-100:],
        "model_files": model_files
    }

@router.post("/api/tools/modelgen/ollama-create")
async def ollama_create_model(model_name: str = "anti-fraud-expert"):
    """執行 ollama create 從 Modelfile 建立模型（自動帶日期）"""
    global _modelgen_process, _modelgen_log
    if _modelgen_process and _modelgen_process.returncode is None:
        return {"success": False, "message": "已有進程在運行"}
    
    modelfile_path = os.path.join(BASE_DIR, 'models', 'Modelfile')
    
    # 如果 Modelfile 不存在，先執行 model_fine_tuning.py 生成
    if not os.path.exists(modelfile_path):
        log.info("[MODELGEN] Modelfile 不存在，先執行 model_fine_tuning.py...")
        ft_script = os.path.join(BASE_DIR, 'scripts', 'model_fine_tuning.py')
        if os.path.exists(ft_script):
            try:
                proc = await asyncio.create_subprocess_exec(
                    'python', ft_script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=BASE_DIR
                )
                await proc.wait()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"生成 Modelfile 失敗: {e}")
        if not os.path.exists(modelfile_path):
            raise HTTPException(status_code=404, detail="Modelfile 仍不存在，請先執行步驟 1")
    
    # 自動加日期後綴
    from datetime import datetime as _dt
    if not any(c.isdigit() for c in model_name.split('-')[-1]):
        model_name = f"{model_name}-{_dt.now().strftime('%Y%m%d_%H%M%S')}"
    
    _modelgen_log = [f"[ollama create] 建立模型: {model_name}",
                     f"[ollama create] Modelfile: {modelfile_path}"]
    try:
        # 優先嘗試 CLI（本地模式）；Docker 模式則改用 HTTP API
        import shutil
        if shutil.which('ollama'):
            _modelgen_process = await asyncio.create_subprocess_exec(
                'ollama', 'create', model_name, '-f', modelfile_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=BASE_DIR
            )
            asyncio.create_task(_read_modelgen_output(_modelgen_process))
        else:
            # Docker 模式：使用 Ollama HTTP API /api/create
            import httpx
            ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
            with open(modelfile_path, 'r', encoding='utf-8') as f:
                modelfile_content = f.read()
            async def _http_create():
                async with httpx.AsyncClient(timeout=300) as client:
                    async with client.stream('POST', f'{ollama_url}/api/create',
                                             json={'name': model_name, 'modelfile': modelfile_content}) as resp:
                        async for line in resp.aiter_lines():
                            if line:
                                _modelgen_log.append(line)
            asyncio.create_task(_http_create())
        return {"success": True, "message": f"ollama create {model_name} 已啟動", "model_name": model_name}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="找不到 ollama 指令，請確認 Ollama 已安裝並在 PATH 中")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/tools/modelgen/ollama-list")
async def ollama_list_models():
    """列出已安裝的 Ollama 模型"""
    try:
        import shutil
        if shutil.which('ollama'):
            # 本地模式：使用 CLI
            proc = await asyncio.create_subprocess_exec(
                'ollama', 'list',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode('utf-8', errors='replace').strip()
            models = []
            lines = output.splitlines()
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append({
                        "name": parts[0],
                        "size": parts[2] + ' ' + parts[3] if len(parts) > 3 else (parts[2] if len(parts) > 2 else '—'),
                        "modified": ' '.join(parts[4:]) if len(parts) > 4 else '—'
                    })
            return {"models": models, "raw": output}
        else:
            # Docker 模式：使用 Ollama HTTP API
            import httpx
            ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f'{ollama_url}/api/tags')
                resp.raise_for_status()
                data = resp.json()
            models = [
                {
                    "name": m.get('name', ''),
                    "size": f"{m.get('size', 0) // 1024 // 1024} MB",
                    "modified": m.get('modified_at', '—')
                }
                for m in data.get('models', [])
            ]
            return {"models": models}
    except FileNotFoundError:
        return {"models": [], "error": "找不到 ollama 指令，請確認 Ollama 已安裝"}
    except Exception as e:
        return {"models": [], "error": str(e)}



