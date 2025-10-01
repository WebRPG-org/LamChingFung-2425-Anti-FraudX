from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime
from app.fraud_detect import checker
from app.ai_service import generate_response, generate_rag_response, initialize_rag_system
from app.ai_service import ai_service
from app.rag_service import rag_service

logger = logging.getLogger(__name__)


router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    use_rag: Optional[bool] = True

@router.post("/chat", tags=["Chat UI"])
async def handle_chat(request: ChatRequest):
    """
    Receive all requests from Web UI and intelligently distribute to different backend services.
    """
    query = request.query.strip()
    session_id = request.session_id or "default"
    use_rag = request.use_rag
    
    try:
        if use_rag:
            # Use AI service
            logger.info(f"Using AI service to process query: '{query}' (Session ID: {session_id})")
            result = await ai_service.generate_response(query, session_id)
            
            if "error" in result:
                return {"response": result["error"], "source": "ai_error"}
            else:
                return {
                    "response": result["response"],
                    "metadata": result.get("metadata", {}),
                    "source": "unified_ai"
                }
        else:
            # Use standard RAG system
            logger.info(f"Using RAG system to process query: '{query}' (Session ID: {session_id})")
            result = await generate_rag_response(query, session_id)
            
            if "error" in result:
                return {"response": result["error"], "source": "rag_error"}
            else:
                return {"response": result["response"], "source": "rag"}
        
        # Traditional intelligent distribution logic (backward compatibility)
        if not use_rag:
            if len(query) < 50 and 'http' not in query:
                print(f"Detected entity query: '{query}', executing database comparison...")
                result = await checker.check_entity(query)
                return {"response": result.get("message"), "source": "entity_check"}
            else:
                logger.info("Detected text analysis request, submitting to AI...")
                
                prompt = f"""
                You are a fraud analysis expert specializing in Hong Kong financial markets. Your task is to analyze the text provided by users and identify potential fraud characteristics.

                Please follow these rules:
                1.  Identify suspicious elements in the text, such as: urgency, guaranteed high returns, unofficial contact methods, suspicious links, requests for personal information, etc.
                2.  Summarize your analysis in concise, clear Traditional Chinese, directly telling users whether there are risks and the reasons.

                The text provided by the user is as follows:
                ---
                {query}
                ---
                Your analysis report:
                """
                
                ai_result = generate_response(prompt=prompt)
                
                if "error" in ai_result:
                    return {"response": ai_result["error"]}
                else:
                    return {"response": ai_result["response"]}
                    
    except Exception as e:
        logger.error(f"Error occurred while processing chat request: {e}")
        return {"response": f"Error occurred while processing request: {e}", "source": "error"}

@router.post("/rag/initialize", tags=["RAG System"])
async def initialize_rag():
    """Initialize RAG system vector index."""
    try:
        success = await initialize_rag_system()
        if success:
            return {"message": "RAG system initialization successful", "status": "success"}
        else:
            return {"message": "RAG system initialization failed", "status": "error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while initializing RAG system: {str(e)}")

@router.get("/rag/stats", tags=["RAG System"])
async def get_rag_stats():
    """Get RAG system statistics."""
    try:
        stats = rag_service.get_stats()
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while getting RAG statistics: {str(e)}")

@router.post("/rag/search", tags=["RAG System"])
async def semantic_search(query: str, top_k: int = 5):
    """Perform semantic search."""
    try:
        results = await rag_service.semantic_search(query, top_k)
        return {"results": results, "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred during semantic search: {str(e)}")

@router.post("/rag/hybrid-search", tags=["RAG System"])
async def hybrid_search(query: str, top_k: int = 5):
    """Perform hybrid search (semantic + fuzzy matching)."""
    try:
        results = await rag_service.enhanced_search(query, top_k)
        return {"results": results, "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred during hybrid search: {str(e)}")

@router.post("/rag/process-documents", tags=["RAG System"])
async def process_documents():
    """Process all documents to enhance RAG system."""
    try:
        # Rebuild RAG index
        success = await rag_service.build_vector_index()
        if success:
            stats = rag_service.get_stats()
            return {"message": "Document processing completed", "results": stats}
        else:
            return {"message": "Document processing failed", "results": {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred during document processing: {str(e)}")

@router.post("/rag/rebuild-index", tags=["RAG System"])
async def rebuild_index():
    """Rebuild vector index."""
    try:
        success = await rag_service.build_vector_index(use_processed_docs=True)
        if success:
            return {"message": "Vector index rebuild successful", "status": "success"}
        else:
            return {"message": "Vector index rebuild failed", "status": "error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while rebuilding index: {str(e)}")

@router.get("/data/summary", tags=["Data"])
async def get_data_summary():
    """Get database summary information."""
    try:
        from app.core.mongo_client import mongo_client
        db = mongo_client.get_db()
        
        summary = {}
        
        # Get statistics for each collection
        collections = ['sfc_alert_list', 'scam_indicators', 'licensed_entities', 'official_contacts']
        
        for collection_name in collections:
            try:
                collection = db[collection_name]
                count = await collection.count_documents({})
                summary[collection_name] = {
                    "total_documents": count,
                    "status": "available" if count > 0 else "empty"
                }
            except Exception as e:
                summary[collection_name] = {
                    "total_documents": 0,
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "database_summary": summary,
            "timestamp": datetime.now().isoformat(),
            "rag_status": rag_service.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while getting data summary: {str(e)}")

