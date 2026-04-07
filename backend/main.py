"""
main.py - 完整的RAG系統集成
在應用啟動時自動加載RAG數據和初始化所有系統
"""

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 延遲導入日誌
try:
    from utils.logger import log
except Exception as e:
    log = logging.getLogger(__name__)
    log.warning(f"Failed to import custom logger: {e}")

# Load environment variables from backend/.env
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

# 添加 CORS 支援
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# RAG系統初始化
# ============================================================

async def initialize_rag_system():
    """
    初始化RAG系統
    檢查Firestore中是否已有RAG數據
    如果沒有，則從本地文件加載
    """
    try:
        logger.info("🔄 開始初始化RAG系統...")
        
        from services.firestore_rag_fraud_loader import FirestoreRAGDataLoader, FirestoreRAGContextProvider
        
        # 初始化加載器和提供器
        loader = FirestoreRAGDataLoader()
        provider = FirestoreRAGContextProvider()
        
        # 檢查Firestore中是否已有數據
        logger.info("📋 檢查Firestore中的RAG數據...")
        has_data = await provider.check_data_exists()
        
        if has_data:
            logger.info("✅ Firestore中已有RAG數據，跳過加載")
            logger.info("✅ RAG系統初始化完成")
            return True
        
        # 如果沒有數據，從本地文件加載
        logger.info("📥 Firestore中沒有數據，開始從本地文件加載...")
        
        # 數據文件位置
        generator_path = os.path.join(os.path.dirname(__file__), 'data', 'massive_generator.py')
        adcc_path = os.path.join(os.path.dirname(__file__), 'data', 'scraped_alerts.json')
        
        # 檢查文件是否存在
        if not os.path.exists(generator_path):
            logger.warning(f"⚠️ 生成式數據文件不存在: {generator_path}")
        else:
            logger.info(f"✅ 找到生成式數據: {generator_path}")
        
        if not os.path.exists(adcc_path):
            logger.warning(f"⚠️ ADCC數據文件不存在: {adcc_path}")
        else:
            logger.info(f"✅ 找到ADCC數據: {adcc_path}")
        
        # 加載生成式數據
        if os.path.exists(generator_path):
            logger.info("📥 加載生成式數據到Firestore...")
            gen_count = await loader.load_generator_data(generator_path)
            logger.info(f"✅ 生成式數據加載完成: {gen_count}個特徵")
        
        # 加載ADCC真實案例
        if os.path.exists(adcc_path):
            logger.info("📥 加載ADCC真實案例到Firestore...")
            adcc_count = await loader.load_adcc_data(adcc_path)
            logger.info(f"✅ ADCC數據加載完成: {adcc_count}個案例")
        
        logger.info("✅ RAG系統初始化完成")
        return True
    
    except Exception as e:
        logger.error(f"❌ RAG系統初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def initialize_session_manager():
    """
    初始化SessionManager
    確保RAG集成的SessionManager已準備好
    """
    try:
        logger.info("🔄 初始化SessionManager...")
        
        from services.session_manager_with_rag import get_session_manager_with_rag
        
        # 獲取SessionManager實例
        session_manager = get_session_manager_with_rag()
        logger.info("✅ SessionManager已初始化")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ SessionManager初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def initialize_analyzers():
    """
    初始化所有分析器
    確保Phase 2.1-2.3的分析器已準備好
    """
    try:
        logger.info("🔄 初始化分析器...")
        
        from services.tactic_analyzer import get_tactic_analyzer
        from services.verdict_judge import get_verdict_judge
        from services.scam_scoring_v2 import get_scam_scorer
        
        # 初始化騙術分析器
        tactic_analyzer = get_tactic_analyzer()
        logger.info("✅ 騙術分析器已初始化")
        
        # 初始化勝負判定器
        verdict_judge = get_verdict_judge()
        logger.info("✅ 勝負判定器已初始化")
        
        # 初始化評分系統
        scam_scorer = get_scam_scorer()
        logger.info("✅ 評分系統已初始化")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 分析器初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def initialize_phase_3_4_services():
    """
    初始化Phase 3和Phase 4的服務
    包括口語化處理、長度控制、評估集成
    """
    try:
        logger.info("🔄 初始化Phase 3 & 4服務...")
        
        from services.conversational_style_processor import get_conversational_style_processor
        from services.response_length_controller import get_response_length_controller
        from services.evaluation_integration import get_evaluation_integration
        from services.api_integration import get_api_integration
        
        # 初始化口語化處理器
        style_processor = get_conversational_style_processor()
        logger.info("✅ 口語化處理器已初始化 (Phase 3.1)")
        
        # 初始化長度控制器
        length_controller = get_response_length_controller()
        logger.info("✅ 長度控制器已初始化 (Phase 3.2)")
        
        # 初始化評估集成
        evaluation_integration = get_evaluation_integration()
        logger.info("✅ 評估集成已初始化 (Phase 3.3)")
        
        # 初始化API集成
        api_integration = get_api_integration()
        logger.info("✅ API集成已初始化 (Phase 3.4)")
        
        logger.info("✅ Phase 3 & 4服務初始化完成")
        return True
    
    except Exception as e:
        logger.error(f"❌ Phase 3 & 4服務初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# API路由
# ============================================================

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
        with open(rpgv2_index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
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

@app.get("/rag/status")
def rag_status():
    """RAG系統狀態端點"""
    try:
        from services.firestore_rag_fraud_loader import FirestoreRAGContextProvider
        
        provider = FirestoreRAGContextProvider()
        
        return {
            "status": "ok",
            "rag_system": "initialized",
            "message": "RAG系統已初始化並準備就緒"
        }
    except Exception as e:
        return {
            "status": "error",
            "rag_system": "failed",
            "error": str(e)
        }

# ============================================================
# 應用啟動事件
# ============================================================

@app.on_event("startup")
async def startup_event():
    """
    應用啟動事件
    在應用啟動時執行所有初始化
    """
    logger.info("=" * 70)
    logger.info("🚀 AI-Agent 後端啟動中...")
    logger.info("=" * 70)
    
    # 1. 初始化RAG系統
    logger.info("\n📋 步驟1: 初始化RAG系統")
    rag_success = await initialize_rag_system()
    
    # 2. 初始化SessionManager
    logger.info("\n📋 步驟2: 初始化SessionManager")
    session_success = await initialize_session_manager()
    
    # 3. 初始化分析器
    logger.info("\n📋 步驟3: 初始化分析器 (Phase 2.1-2.3)")
    analyzer_success = await initialize_analyzers()
    
    # 4. 初始化Phase 3 & 4服務 ✨ NEW
    logger.info("\n📋 步驟4: 初始化Phase 3 & 4服務")
    phase_3_4_success = await initialize_phase_3_4_services()
    
    # 5. 加載所有API路由
    logger.info("\n📋 步驟5: 加載API路由")
    await load_all_routers()
    
    # 6. 總結
    logger.info("\n" + "=" * 70)
    if rag_success and session_success and analyzer_success and phase_3_4_success:
        logger.info("✅ 所有系統初始化完成！")
        logger.info("✅ 架構已完整建立 (Phase 1-6 + Phase 3 & 4)")
        logger.info("✅ 系統準備就緒")
    else:
        logger.warning("⚠️ 部分系統初始化失敗，請檢查日誌")
    logger.info("=" * 70 + "\n")


async def load_all_routers():
    """在應用啟動時加載所有路由"""
    logger.info("Loading routers...")
    
    routers_to_load = [
        # 核心路由
        ("api.rpgv2_game_modes_routes", "router"),
        ("api.rpgv2_battle_routes", "router"),
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
        ("api.tts_routes", "router"),
        # RAG和評估路由
        ("api.rag_routes", "router"),
        ("api.evaluation_routes", "router"),
        # Phase 3 & 4 路由 ✨ NEW
        ("routes.evaluation_routes", "router"),
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
    app.mount("/rpgv2-static", StaticFiles(directory=rpgv2_path, html=True), name="rpgv2_static")
    logger.info(f"✅ 已掛載 RPGv2 項目靜態文件: {rpgv2_path}")
else:
    logger.warning(f"⚠️ RPGv2 項目路徑不存在: {rpgv2_path}")

# ============================================================
# 服務器啟動
# ============================================================

if __name__ == "__main__":
    logger.info(f"Starting server with model: {AGENT_MODEL_NAME}")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
