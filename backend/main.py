import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 延遲導入日誌
try:
    from utils.logger import log
except Exception as e:
    log = logging.getLogger(__name__)
    log.warning(f"Failed to import custom logger: {e}")

# Load environment variables from backend/.env (authoritative single source)
_env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(_env_file, override=True)

# Setting the agent model name from environment variables
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL", "gemma3:4b")

# Setting up FastAPI application instance
app = FastAPI(
    title="AI Agent Simulation Backend + RPG Maker Game",
    description="offering backend services for AI scam attack-defense simulations and RPG Maker integration.",
    version="1.0.0"
)

# 添加 CORS 支援 (for RPG Maker)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API routes ---

@app.get("/")
def read_root():
    """主頁路由 - 返回模式選擇頁面"""
    log.info("Root endpoint was called.")
    index_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"status": "Backend is running", "model_in_use": AGENT_MODEL_NAME, "error": "index.html not found"}

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

# 延遲加載所有路由
@app.on_event("startup")
async def load_all_routers():
    """在應用啟動時加載所有路由"""
    logger.info("Loading routers...")
    
    routers_to_load = [
        ("api.game_routes_v2", "router"),
        ("api.frontend_routes", "router"),
        ("api.simulation_routes", "router"),
        ("api.training_routes", "router"),
        ("api.game_routes", "router"),
        ("api.chat_routes", "router"),
        ("api.personal_chat_routes", "router"),
        ("api.prompt_version_routes", "router"),
        ("api.demo_routes", "router"),
        ("api.model_switch_routes", "router"),
        ("api.tools_routes", "router"),
    ]
    
    loaded_count = 0
    for module_name, router_name in routers_to_load:
        try:
            module = __import__(module_name, fromlist=[router_name])
            router = getattr(module, router_name)
            app.include_router(router)
            logger.info(f"✅ Loaded {module_name}")
            loaded_count += 1
        except Exception as e:
            logger.warning(f"⚠️ Failed to load {module_name}: {str(e)[:100]}")
    
    logger.info(f"✅ Loaded {loaded_count} routers successfully")

# 掛載 RPGv2 項目的靜態文件
rpgv2_path = os.path.join(os.path.dirname(__file__), '..', 'rpg-platform-v2')
if os.path.exists(rpgv2_path):
    # 掛載整個 rpg-platform-v2 目錄（包含 src, public 等）
    app.mount("/rpgv2-static", StaticFiles(directory=rpgv2_path, html=True), name="rpgv2_static")
    logger.info(f"✅ 已掛載 RPGv2 項目靜態文件: {rpgv2_path}")
else:
    logger.warning(f"⚠️ RPGv2 項目路徑不存在: {rpgv2_path}")

# --- Server Startup ---

if __name__ == "__main__":
    logger.info(f"Starting server with model: {AGENT_MODEL_NAME}")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
