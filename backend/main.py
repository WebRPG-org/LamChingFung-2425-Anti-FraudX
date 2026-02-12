import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from utils.logger import log
from api.frontend_routes import router as frontend_router
from api.simulation_routes import router as simulation_router
from api.training_routes import router as training_router
from api.game_routes import router as game_router
from api.game_routes_v2 import router as game_router_v2
from api.chat_routes import router as chat_router
from api.personal_chat_routes import router as personal_chat_router
from api.rpgv2_battle_routes import router as rpgv2_battle_router
from api.rpgv2_game_modes_routes import router as rpgv2_game_modes_router
from api.prompt_version_routes import router as prompt_version_router
from api.demo_routes import router as demo_router
from api.model_switch_routes import router as model_switch_router
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

# 離線模式檢查（確保數據不流出）
try:
    from utils.offline_mode import check_offline_mode, check_data_isolation, verify_ollama_local_only
    check_offline_mode()
    check_data_isolation()
    verify_ollama_local_only()
except Exception as e:
    log.warning(f"離線模式檢查失敗: {e}")

# GPU检查（启动时执行）
try:
    from utils.gpu_checker import check_and_enforce_gpu
    log.info("正在执行GPU检测...")
    gpu_available = check_and_enforce_gpu()
    if gpu_available:
        log.info("✅ GPU已启用，将使用GPU加速")
    else:
        log.warning("⚠️ 未使用GPU，性能可能受限")
except Exception as e:
    log.error(f"GPU检测失败: {e}")
    # 如果FORCE_GPU=1，则失败退出
    if os.getenv("FORCE_GPU", "1") == "1":
        log.error("强制GPU模式启用，但GPU检测失败，程序退出")
        import sys
        sys.exit(1)

# Setting the agent model name from environment variables
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL", "gemma3:4b")

# Setting up FastAPI application instance
app = FastAPI(
    title="AI Agent Simulation Backend + RPG Maker Game",
    description="offering backend services for AI scam attack-defense simulations and RPG Maker integration.",
    version="1.0.0"
)

# 初始化 Prompt 版本管理器並註冊初始版本
try:
    from services.prompt_helper import register_initial_prompts
    from utils.prompt_version_manager import PromptVersionManager
    
    version_manager = PromptVersionManager()
    register_initial_prompts(version_manager)
    log.info("✅ Prompt 版本管理器初始化完成")
except Exception as e:
    log.error(f"❌ Prompt 版本管理器初始化失敗: {e}")

# 添加 CORS 支援 (for RPG Maker)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include frontend and API routes
app.include_router(frontend_router)
app.include_router(simulation_router)
app.include_router(training_router)
app.include_router(game_router)      # v1 - 保留向後兼容
app.include_router(game_router_v2)   # v2 - 使用完整 Agent 系統
app.include_router(chat_router)
app.include_router(personal_chat_router)  # 個人對話模式
app.include_router(rpgv2_battle_router)   # RPGv2 三方對話
app.include_router(rpgv2_game_modes_router)  # RPGv2 遊戲模式（新）
app.include_router(prompt_version_router)  # Prompt 版本管理
app.include_router(demo_router)           # 演示模式
app.include_router(model_switch_router)   # 模型切換 API

# 掛載RPG項目的靜態文件（HTML, JS, CSS等）
rpg_project_path = os.path.join(os.path.dirname(__file__), '..', 'RPG_platform', 'RPG_Project')
if os.path.exists(rpg_project_path):
    # 先掛載靜態文件目錄
    app.mount("/RPG_Project", StaticFiles(directory=rpg_project_path, html=True), name="rpg_project")
    log.info(f"✅ 已掛載RPG項目靜態文件: {rpg_project_path}")
else:
    log.warning(f"⚠️ RPG項目路徑不存在: {rpg_project_path}")

# 掛載 RPGv2 項目的靜態文件
rpgv2_path = os.path.join(os.path.dirname(__file__), '..', 'rpg-platform-v2')
if os.path.exists(rpgv2_path):
    # 掛載整個 rpg-platform-v2 目錄（包含 src, public 等）
    app.mount("/rpgv2-static", StaticFiles(directory=rpgv2_path, html=True), name="rpgv2_static")
    log.info(f"✅ 已掛載 RPGv2 項目靜態文件: {rpgv2_path}")
else:
    log.warning(f"⚠️ RPGv2 項目路徑不存在: {rpgv2_path}")

# --- API routes ---

@app.get("/")
def read_root():
    """主頁路由 - 返回模式選擇頁面"""
    log.info("Root endpoint was called.")
    # 優先使用 frontend/index.html（包含模型切換開關）
    frontend_index_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    if os.path.exists(frontend_index_path):
        return FileResponse(frontend_index_path)
    
    # Fallback 到 RPG 項目的 index.html
    rpg_index_path = os.path.join(os.path.dirname(__file__), '..', 'RPG_platform', 'RPG_Project', 'index.html')
    if os.path.exists(rpg_index_path):
        return FileResponse(rpg_index_path)
    else:
        return {"status": "Backend is running", "model_in_use": AGENT_MODEL_NAME, "error": "index.html not found"}

@app.get("/rpg")
def rpg_game():
    """RPG 遊戲路由 - 返回修改後的 RPG 遊戲頁面"""
    log.info("RPG game endpoint was called.")
    rpg_game_path = os.path.join(os.path.dirname(__file__), '..', 'RPG_platform', 'RPG_Project', 'rpg_game.html')
    
    if os.path.exists(rpg_game_path):
        # 讀取 HTML 內容
        with open(rpg_game_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 將相對路徑替換為絕對路徑
        html_content = html_content.replace('href="icon/', 'href="/RPG_Project/icon/')
        html_content = html_content.replace('href="fonts/', 'href="/RPG_Project/fonts/')
        html_content = html_content.replace('src="js/', 'src="/RPG_Project/js/')
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    else:
        return {"error": "rpg_game.html not found", "path": rpg_game_path}

@app.get("/rpgv2")
def rpgv2_game():
    """RPG v2 遊戲路由 - 返回新版 2D RPG 遊戲頁面"""
    log.info("RPG v2 game endpoint was called.")
    rpgv2_index_path = os.path.join(os.path.dirname(__file__), '..', 'rpg-platform-v2', 'index.html')
    
    if os.path.exists(rpgv2_index_path):
        # 讀取 HTML 內容
        with open(rpgv2_index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 將相對路徑替換為絕對路徑
        html_content = html_content.replace('href="/src/', 'href="/rpgv2-static/src/')
        html_content = html_content.replace('src="/src/', 'src="/rpgv2-static/src/')
        html_content = html_content.replace('from "/src/', 'from "/rpgv2-static/src/')
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    else:
        return {"error": "RPGv2 index.html not found", "path": rpgv2_index_path}

@app.get("/health")
def health_check():
    """健康檢查端點"""
    log.info("Health check endpoint was called.")
    return {"status": "Backend is running", "model_in_use": AGENT_MODEL_NAME}

@app.get("/test/json")
def test_json_endpoint():
    """測試端點 (JSON) - 返回服務器狀態信息"""
    from datetime import datetime
    log.info("Test JSON endpoint was called.")
    return {
        "status": "ok",
        "message": "Test endpoint is working! 🎉",
        "timestamp": datetime.now().isoformat(),
        "server_info": {
            "model": AGENT_MODEL_NAME,
            "version": "2.0.0",
            "environment": os.getenv("APP_ENV", "development")
        },
        "available_routes": {
            "health": "/health",
            "docs": "/docs",
            "test_page": "/test",
            "test_json": "/test/json",
            "simulation": "/simulation/start",
            "game_api": "/api/game/info",
            "personal_chat": "/api/personal-chat/start",
            "rpg_game": "/rpg"
        }
    }

# WebSocket endpoints are now handled in api/simulation_routes.py


# --- Server Startup ---

if __name__ == "__main__":
    log.info(f"Starting server with model: {AGENT_MODEL_NAME}")
    # uvicorn.run("filename:FastAPI_instance_name", ...other_parameters)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)