import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    print("啟動 AI 反詐騙模擬訓練平台")
    print("=" * 50)
    
    # 檢查後端目錄
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("錯誤: backend 目錄不存在")
        return
    
    # 檢查前端目錄
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("錯誤: frontend 目錄不存在")
        return
    
    # 檢查 .env 文件
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("錯誤: .env 文件不存在")
        return
    
    print("檢查完成，開始啟動服務...")
    
    # 啟動後端服務
    print("\n啟動後端服務...")
    try:
        # 切換到後端目錄
        os.chdir(backend_dir)
        
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
