"""tools_routes.py — /api/tools/* endpoints for tools.html

Covers:
  scraper    — backend/scripts/scraper.py
  finetune   — backend/scripts/generate_finetuning_data.py
  modelgen   — backend/scripts/model_fine_tuning.py  (expert + scammer)
  ollama     — ollama create / ollama list
"""

import os
import sys
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional
from fastapi import APIRouter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log

router = APIRouter(prefix="/api/tools")

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(BACKEND_DIR, 'scripts')
MODELS_DIR  = os.path.join(BACKEND_DIR, 'models')
DATA_DIR    = os.path.join(BACKEND_DIR, '..', 'data')
FINETUNE_DIR = os.path.join(BACKEND_DIR, 'training_data', 'fine_tuning_data')

# ── shared process state ───────────────────────────────────────────────────

class ProcState:
    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.log_lines: list = []
        self.exit_code: Optional[int] = None
        self.lock = threading.Lock()

    def start(self, cmd, cwd=None, env=None):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                return False, "已在運行中"
            self.log_lines = []
            self.exit_code = None
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=cwd,
                    env=env,
                )
                threading.Thread(target=self._drain, daemon=True).start()
                return True, self.proc.pid
            except Exception as e:
                return False, str(e)

    def _drain(self):
        for line in self.proc.stdout:
            with self.lock:
                self.log_lines.append(line.rstrip())
        self.proc.wait()
        with self.lock:
            self.exit_code = self.proc.returncode

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def status(self):
        with self.lock:
            return {
                "running": self.running,
                "exit_code": self.exit_code,
                "log": list(self.log_lines),
            }


_scraper  = ProcState()
_finetune = ProcState()
_modelgen = ProcState()


# ── helpers ────────────────────────────────────────────────────────────────

def _py():
    """Return python executable path."""
    return sys.executable


def _file_list(directory, extensions=('.json', '.jsonl')):
    if not os.path.exists(directory):
        return []
    files = []
    for name in os.listdir(directory):
        if name.endswith(extensions):
            full = os.path.join(directory, name)
            stat = os.stat(full)
            files.append({
                "name": name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files


# ═══════════════════════════════════════════════════════════════════════════
# SCRAPER
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/scraper/run")
async def scraper_run():
    script = os.path.join(SCRIPTS_DIR, 'scraper.py')
    ok, pid_or_err = _scraper.start([_py(), script], cwd=BACKEND_DIR)
    if ok:
        log.info(f"Scraper started PID={pid_or_err}")
        return {"success": True, "message": "爬蟲已啟動", "pid": pid_or_err}
    return {"success": False, "message": pid_or_err}


@router.get("/scraper/status")
async def scraper_status():
    s = _scraper.status()
    # Count scraped data files
    count = 0
    data_file = os.path.join(DATA_DIR, 'scraped_alerts.json')
    if os.path.exists(data_file):
        try:
            import json
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count = len(data) if isinstance(data, list) else 1
        except Exception:
            count = 1
    s["data_count"] = count
    return s


# ═══════════════════════════════════════════════════════════════════════════
# FINE-TUNE
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/finetune/run")
async def finetune_run():
    script = os.path.join(SCRIPTS_DIR, 'generate_finetuning_data.py')
    ok, pid_or_err = _finetune.start([_py(), script], cwd=BACKEND_DIR)
    if ok:
        return {"success": True, "message": "Fine-tune 數據生成已啟動", "pid": pid_or_err}
    return {"success": False, "message": pid_or_err}


@router.get("/finetune/status")
async def finetune_status():
    s = _finetune.status()
    s["ft_file_count"] = len(_file_list(FINETUNE_DIR))
    return s


@router.get("/finetune/files")
async def finetune_files():
    return {"files": _file_list(FINETUNE_DIR)}


# ═══════════════════════════════════════════════════════════════════════════
# MODEL GEN  — generates Modelfile.expert + Modelfile.scammer in one shot
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/modelgen/run")
async def modelgen_run():
    script = os.path.join(SCRIPTS_DIR, 'model_fine_tuning.py')
    ok, pid_or_err = _modelgen.start([_py(), script], cwd=BACKEND_DIR)
    if ok:
        return {"success": True, "message": "正在同時生成 專家 + 騙徒 Modelfile...", "pid": pid_or_err}
    return {"success": False, "message": pid_or_err}


@router.get("/modelgen/status")
async def modelgen_status():
    s = _modelgen.status()
    model_files = []
    if os.path.exists(MODELS_DIR):
        for name in os.listdir(MODELS_DIR):
            full = os.path.join(MODELS_DIR, name)
            if os.path.isfile(full):
                stat = os.stat(full)
                model_files.append({"name": name, "size": stat.st_size})
    s["model_files"] = model_files
    return s


# ── ollama create (both models at once) ────────────────────────────────────

@router.post("/modelgen/ollama-create-both")
async def ollama_create_both(
    expert_name: str = "anti-fraud-expert",
    scammer_name: str = "scammer-sim",
):
    """Run `ollama create` for expert AND scammer sequentially in background."""
    expert_mf  = os.path.join(MODELS_DIR, 'Modelfile.expert')
    scammer_mf = os.path.join(MODELS_DIR, 'Modelfile.scammer')

    missing = []
    if not os.path.exists(expert_mf):  missing.append('Modelfile.expert')
    if not os.path.exists(scammer_mf): missing.append('Modelfile.scammer')
    if missing:
        return {"success": False, "message": f"找不到 Modelfile: {', '.join(missing)}，請先執行『生成 Modelfile』"}

    def _run_both():
        import shutil, httpx, asyncio
        use_cli = bool(shutil.which('ollama'))
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
        for name, mf in [(expert_name, expert_mf), (scammer_name, scammer_mf)]:
            with _modelgen.lock:
                _modelgen.log_lines.append(f"▶ ollama create {name} ...")
            if use_cli:
                result = subprocess.run(
                    ['ollama', 'create', name, '-f', mf],
                    capture_output=True, text=True, encoding='utf-8', errors='replace'
                )
                with _modelgen.lock:
                    for line in (result.stdout + result.stderr).splitlines():
                        _modelgen.log_lines.append(line)
                    _modelgen.log_lines.append(
                        f"✅ {name} 完成" if result.returncode == 0 else f"❌ {name} 失敗 (exit {result.returncode})"
                    )
            else:
                # Docker mode: use Ollama HTTP API /api/create
                try:
                    with open(mf, 'r', encoding='utf-8') as f:
                        modelfile_content = f.read()
                    with httpx.Client(timeout=300) as client:
                        with client.stream('POST', f'{ollama_url}/api/create',
                                           json={'name': name, 'modelfile': modelfile_content}) as resp:
                            for line in resp.iter_lines():
                                if line:
                                    with _modelgen.lock:
                                        _modelgen.log_lines.append(line)
                    with _modelgen.lock:
                        _modelgen.log_lines.append(f"✅ {name} 完成")
                except Exception as e:
                    with _modelgen.lock:
                        _modelgen.log_lines.append(f"❌ {name} 失敗: {e}")

    threading.Thread(target=_run_both, daemon=True).start()
    return {"success": True, "message": f"開始建立 {expert_name} + {scammer_name}"}


@router.post("/modelgen/ollama-create")
async def ollama_create_single(model_name: str = "anti-fraud-expert", role: str = "expert"):
    """Run `ollama create` for a single model. role='expert' | 'scammer'"""
    if role == "scammer":
        mf = os.path.join(MODELS_DIR, 'Modelfile.scammer')
    else:
        mf = os.path.join(MODELS_DIR, 'Modelfile.expert')

    if not os.path.exists(mf):
        return {"success": False, "message": f"找不到 {os.path.basename(mf)}，請先執行『生成 Modelfile』"}

    def _run():
        import shutil, httpx
        use_cli = bool(shutil.which('ollama'))
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
        with _modelgen.lock:
            _modelgen.log_lines.append(f"▶ ollama create {model_name} -f {os.path.basename(mf)}")
        if use_cli:
            result = subprocess.run(
                ['ollama', 'create', model_name, '-f', mf],
                capture_output=True, text=True, encoding='utf-8', errors='replace'
            )
            with _modelgen.lock:
                for line in (result.stdout + result.stderr).splitlines():
                    _modelgen.log_lines.append(line)
                _modelgen.log_lines.append(
                    f"✅ {model_name} 完成" if result.returncode == 0 else f"❌ {model_name} 失敗 (exit {result.returncode})"
                )
        else:
            # Docker mode: use Ollama HTTP API /api/create
            try:
                with open(mf, 'r', encoding='utf-8') as f:
                    modelfile_content = f.read()
                with httpx.Client(timeout=300) as client:
                    with client.stream('POST', f'{ollama_url}/api/create',
                                       json={'name': model_name, 'modelfile': modelfile_content}) as resp:
                        for line in resp.iter_lines():
                            if line:
                                with _modelgen.lock:
                                    _modelgen.log_lines.append(line)
                with _modelgen.lock:
                    _modelgen.log_lines.append(f"✅ {model_name} 完成")
            except Exception as e:
                with _modelgen.lock:
                    _modelgen.log_lines.append(f"❌ {model_name} 失敗: {e}")

    threading.Thread(target=_run, daemon=True).start()
    return {"success": True, "message": f"開始建立 {model_name}（{'騙徒' if role == 'scammer' else '專家'}）"}


@router.get("/modelgen/ollama-list")
async def ollama_list():
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10
        )
        if result.returncode != 0:
            return {"models": [], "error": result.stderr.strip() or "ollama list 失敗"}
        lines = result.stdout.strip().splitlines()
        models = []
        for line in lines[1:]:  # skip header
            parts = line.split()
            if parts:
                models.append({
                    "name": parts[0],
                    "size": parts[2] if len(parts) > 2 else '—',
                    "modified": ' '.join(parts[3:]) if len(parts) > 3 else '—',
                })
        return {"models": models}
    except FileNotFoundError:
        return {"models": [], "error": "Ollama 未安裝或不在 PATH 中"}
    except Exception as e:
        return {"models": [], "error": str(e)}
