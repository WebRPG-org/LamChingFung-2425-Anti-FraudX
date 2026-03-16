"""
最小化的 FastAPI 應用 - 用於測試 Cloud Run 部署
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# 加載環境變量
_env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(_env_file, override=True)

# 創建應用
app = FastAPI(
    title="Anti-FraudX Backend",
    version="1.0.0"
)

# 添加 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 基本路由
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Anti-FraudX Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/test/json")
def test_json():
    return {"status": "ok", "test": "json endpoint working"}

# 延遲加載所有路由
@app.on_event("startup")
async def load_all_routers():
    """在應用啟動時加載所有路由"""
    import logging
    logger = logging.getLogger(__name__)
    
    routers_to_load = [
        ("api.frontend_routes", "frontend_router"),
        ("api.simulation_routes", "simulation_router"),
        ("api.training_routes", "training_router"),
        ("api.game_routes", "game_router"),
        ("api.game_routes_v2", "game_router_v2"),
        ("api.chat_routes", "chat_router"),
        ("api.personal_chat_routes", "personal_chat_router"),
        ("api.prompt_version_routes", "prompt_version_router"),
        ("api.demo_routes", "demo_router"),
        ("api.model_switch_routes", "model_switch_router"),
        ("api.tools_routes", "tools_router"),
    ]
    
    for module_name, router_name in routers_to_load:
        try:
            module = __import__(module_name, fromlist=[router_name])
            router = getattr(module, router_name)
            app.include_router(router)
            logger.info(f"✅ Loaded {module_name}.{router_name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load {module_name}.{router_name}: {e}")
    
    logger.info("✅ All routers loaded")

if __name__ == "__main__":
    uvicorn.run("main_minimal:app", host="0.0.0.0", port=8080, reload=False)

