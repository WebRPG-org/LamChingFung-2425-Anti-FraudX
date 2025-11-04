import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import os
from utils.logger import log
from api.frontend_routes import router as frontend_router
from api.simulation_routes import router as simulation_router
from api.training_routes import router as training_router
from api.game_routes import router as game_router
from api.chat_routes import router as chat_router
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

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
app.include_router(game_router)
app.include_router(chat_router)

# --- API routes ---

@app.get("/")
def read_root():
    log.info("Health check endpoint was called.")
    """ Root route for health check """
    return {"status": "Backend is running", "model_in_use": AGENT_MODEL_NAME}

# WebSocket endpoints are now handled in api/simulation_routes.py


# --- Server Startup ---

if __name__ == "__main__":
    log.info(f"Starting server with model: {AGENT_MODEL_NAME}")
    # uvicorn.run("filename:FastAPI_instance_name", ...other_parameters)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)