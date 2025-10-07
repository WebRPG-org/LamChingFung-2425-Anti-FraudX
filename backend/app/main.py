import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import fraud_routes, ingestion_routes, chat_routes, audio_routes, file_routes
from app.core.mongo_client import mongo_client
from app.startup_manager import startup_manager
from app.ai_service import ai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up AI-Agent API...")
    # Run startup sequence in background
    asyncio.create_task(startup_manager.initialize_services())
    yield
    logger.info("Shutting down AI-Agent API...")
    # Perform any cleanup work

app = FastAPI(
    title="AI-Agent Financial Service",
    description="AI-powered financial fraud detection and RAG system.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:5173",  # Frontend URL
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "http://ai-agents-frontend-1:80", # Docker frontend service
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat_routes.router, prefix="/api/v1", tags=["Chat"])
app.include_router(fraud_routes.router, prefix="/api/v1", tags=["Fraud Detection"])
app.include_router(ingestion_routes.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(audio_routes.router, prefix="/api/v1", tags=["Audio Processing"])
app.include_router(file_routes.router, prefix="/api/v1", tags=["File Processing"])

@app.get("/health", summary="Health Check", tags=["Monitoring"])
async def health_check():
    """
    Perform health check on API and its dependencies.
    Returns status of API, MongoDB, RAG system and other features.
    """
    try:
        # Get basic system status
        status = startup_manager.get_system_status()
        
        # Check MongoDB connection
        mongodb_status = "unknown"
        try:
            if mongo_client.client:
                # Try to ping MongoDB
                await mongo_client.client.admin.command('ping')
                mongodb_status = "connected"
            else:
                mongodb_status = "not_connected"
        except Exception as e:
            mongodb_status = f"error: {str(e)}"
        
        # Check RAG system status
        rag_status = "unknown"
        try:
            from app.rag_service import rag_service
            if rag_service.initialized:
                rag_status = "rag_initialized"
            else:
                rag_status = "not_initialized"
        except Exception as e:
            rag_status = f"error: {str(e)}"
        
        # Check AI service status
        ai_status = "unknown"
        try:
            if startup_manager.features.get('google_ai', False):
                ai_status = "google_ai_available"
            else:
                ai_status = "google_ai_not_available"
        except Exception as e:
            ai_status = f"error: {str(e)}"
        
        return {
            "api_status": "healthy",
            "mongodb_status": mongodb_status,
            "rag_status": rag_status,
            "ai_status": ai_status,
            "features": status.get('features', {}),
            "startup_errors": status.get('startup_errors', []),
            "overall_status": status.get('status', 'unknown'),
            "recommended_mode": startup_manager.get_recommended_mode()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    mongo_client.close_client()
    logger.info("Application shutdown complete.")