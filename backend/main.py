"""
main.py - RPG v2 + Vertex AI minimal backend entry
只保留 RPG v2 所需入口、健康檢查、TTS 與必要靜態掛載。
"""

import os
import time
import logging
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from utils.logger import log
except Exception as e:
    log = logging.getLogger(__name__)
    log.warning(f"Failed to import custom logger: {e}")

from seed_alerts import seed_alerts
from utils.db import initialize_game_tables

_env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(_env_file, override=True)

AGENT_MODEL_NAME = os.getenv(
    "VERTEX_AI_MODEL",
    os.getenv(
        "BEDROCK_MODEL_ID",
        os.getenv("AZURE_OPENAI_DEPLOYMENT", os.getenv("AGENT_MODEL", "gemini-2.5-flash-lite"))
    )
)
AI_PROVIDER = os.getenv("AI_PROVIDER", "vertex")
CLOUD_NAME = os.getenv("CLOUD_NAME", "unknown")

app = FastAPI(
    title="Anti-FraudX RPG v2 Backend",
    description="Minimal backend for RPG v2 gameplay powered by multi-cloud AI providers.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    index_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "Backend is running",
        "model_in_use": AGENT_MODEL_NAME,
        "error": "index.html not found"
    }


@app.get("/rpgv2")
def rpgv2_game():
    log.info("RPG v2 game endpoint was called.")

    if os.path.exists(rpgv2_dist_index_path):
        return FileResponse(rpgv2_dist_index_path)

    return {
        "error": "RPGv2 dist index.html not found",
        "path": rpgv2_dist_index_path
    }


@app.get("/health")
def health_check():
    return {
        "status": "Backend is running",
        "model_in_use": AGENT_MODEL_NAME,
        "ai_provider": AI_PROVIDER,
        "cloud": CLOUD_NAME,
    }


@app.get("/stress")
def stress_test(duration_ms: int = 500, intensity: int = 12000):
    duration_ms = max(50, min(duration_ms, 5000))
    intensity = max(1000, min(intensity, 200000))
    deadline = time.perf_counter() + (duration_ms / 1000)
    rounds = 0
    checksum = 0

    while time.perf_counter() < deadline:
        for i in range(intensity):
            checksum = (checksum + ((i * i) % 97)) % 1000003
        rounds += 1

    return {
        "status": "stress completed",
        "duration_ms": duration_ms,
        "intensity": intensity,
        "rounds": rounds,
        "checksum": checksum,
        "cloud": CLOUD_NAME,
    }


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 70)
    logger.info("🚀 Anti-FraudX RPG v2 backend starting...")
    logger.info("=" * 70)
    initialize_game_tables()
    seeded = seed_alerts()
    logger.info(f"✅ Database initialized, alerts available: {seeded}")
    await load_required_routers()
    logger.info("✅ Minimal RPG v2 routers loaded")


async def load_required_routers():
    routers_to_load = [
        ("api.rpgv2_game_modes_routes", "router"),
        ("api.rpgv2_battle_routes", "router"),
        ("api.game_routes_v2", "router"),
        ("api.tts_routes", "router"),
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
            logger.warning(f"⚠️ Failed to load {module_name}: {str(e)[:160]}")

    logger.info(f"✅ Loaded {loaded_count} routers successfully")


frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
frontend_css_path = os.path.join(frontend_path, 'css')
frontend_js_path = os.path.join(frontend_path, 'js')
rpgv2_path = os.path.join(os.path.dirname(__file__), '..', 'rpg-platform-v2')
rpgv2_dist_path = os.path.join(rpgv2_path, 'dist')
rpgv2_dist_index_path = os.path.join(rpgv2_dist_path, 'index.html')

if os.path.exists(frontend_css_path):
    app.mount("/css", StaticFiles(directory=frontend_css_path), name="frontend_css")
    logger.info(f"✅ 已掛載 frontend CSS: {frontend_css_path}")
else:
    logger.warning(f"⚠️ frontend CSS 路徑不存在: {frontend_css_path}")

if os.path.exists(frontend_js_path):
    app.mount("/js", StaticFiles(directory=frontend_js_path), name="frontend_js")
    logger.info(f"✅ 已掛載 frontend JS: {frontend_js_path}")
else:
    logger.warning(f"⚠️ frontend JS 路徑不存在: {frontend_js_path}")

if os.path.exists(rpgv2_dist_path):
    app.mount("/rpgv2-static", StaticFiles(directory=rpgv2_dist_path, html=True), name="rpgv2_static")
    logger.info(f"✅ 已掛載 RPGv2 build 靜態文件: {rpgv2_dist_path}")
else:
    logger.warning(f"⚠️ RPGv2 build 路徑不存在: {rpgv2_dist_path}")


if __name__ == "__main__":
    logger.info(f"Starting server with model: {AGENT_MODEL_NAME}")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
