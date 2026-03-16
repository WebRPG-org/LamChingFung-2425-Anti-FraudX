import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    print("啟動 AI 反詐騙模擬訓練平台")
    print("=" * 50)
    
    # 獲取腳本所在目錄
    script_dir = Path(__file__).parent.absolute()
    
    # 假設腳本在 scripts/ 目錄，項目根目錄在上一層
    project_root = script_dir.parent
    
    print(f"項目根目錄: {project_root}")
    
    # 設置本地開發環境變量（強制設置，覆蓋 .env）
    os.environ["FORCE_GPU"] = "0"
    print("本地開發模式: 已設置 FORCE_GPU=0 (允許使用CPU)")
    
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    print(f"已設置 OLLAMA_BASE_URL={os.environ['OLLAMA_BASE_URL']}")
    
    # 檢查後端目錄
    backend_dir = project_root / "backend"
    if not backend_dir.exists():
        print("錯誤: backend 目錄不存在")
        return
    
    # 檢查前端目錄
    frontend_dir = project_root / "frontend"
    if not frontend_dir.exists():
        print("錯誤: frontend 目錄不存在")
        return
    
    # 檢查 .env 文件
    env_file = backend_dir / ".env"
    if not env_file.exists():
        # 嘗試在根目錄找
        env_file_root = project_root / ".env"
        if env_file_root.exists():
            print(f"在根目錄找到 .env: {env_file_root}")
        else:
            print("錯誤: .env 文件不存在 (backend 或 根目錄)")
            return
    
    print("檢查完成，開始啟動服務...")
    
    # 啟動後端服務
    print("\n啟動後端服務...")
    try:
        # 切換到後端目錄
        os.chdir(backend_dir)
        
        # 將後端目錄加入 PYTHONPATH
        sys.path.append(str(backend_dir))
        
        # 啟動 FastAPI 服務
        print("後端服務將在 http://localhost:8000 啟動")
        print("前端界面將在 http://localhost:8000 提供")
        print("\n按 Ctrl+C 停止服務")
        print("=" * 50)
        
        # 啟動服務
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n\n服務已停止")
    except Exception as e:
        print(f"啟動失敗: {e}")

if __name__ == "__main__":
    main()
