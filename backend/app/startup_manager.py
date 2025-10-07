import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StartupManager:
    """Manages application startup with graceful degradation."""
    
    def __init__(self):
        self.features = {
            'advanced_rag': False,
            'simple_rag': False,
            'document_processing': False,
            'caching': True,  # Always available
            'google_ai': False,
            'mongodb': False
        }
        self.startup_errors = []
    
    async def check_dependencies(self) -> Dict[str, Any]:
        """Check which dependencies are available."""
        results = {}
        
        # Check Google AI
        try:
            import google.generativeai as genai
            self.features['google_ai'] = True
            results['google_ai'] = "available"
        except ImportError as e:
            self.features['google_ai'] = False
            results['google_ai'] = f"not_available: {e}"
            self.startup_errors.append(f"Google AI not available: {e}")
        
        # Check MongoDB
        try:
            import motor.motor_asyncio
            import pymongo
            self.features['mongodb'] = True
            results['mongodb'] = "available"
        except ImportError as e:
            self.features['mongodb'] = False
            results['mongodb'] = f"not_available: {e}"
            self.startup_errors.append(f"MongoDB drivers not available: {e}")
        
        # Check Advanced RAG dependencies
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
            import scikit_learn
            import tiktoken
            self.features['advanced_rag'] = True
            results['advanced_rag'] = "available"
            logger.info("All advanced RAG dependencies are available")
        except ImportError as e:
            self.features['advanced_rag'] = False
            results['advanced_rag'] = f"not_available: {e}"
            logger.warning(f"Advanced RAG not available: {e}")
        
        # Simple RAG is always available (no external dependencies)
        self.features['simple_rag'] = True
        results['simple_rag'] = "available"
        
        # Document processing is always available
        self.features['document_processing'] = True
        results['document_processing'] = "available"
        
        return results
    
    async def initialize_services(self) -> Dict[str, Any]:
        """Initialize available services."""
        init_results = {}
        
        # Initialize RAG system
        if self.features['advanced_rag']:
            try:
                from app.ai_service import initialize_rag_system
                success = await initialize_rag_system()
                init_results['rag_system'] = "advanced_initialized" if success else "advanced_failed"
            except Exception as e:
                logger.error(f"Advanced RAG initialization failed: {e}")
                init_results['rag_system'] = f"advanced_error: {e}"
        elif self.features['simple_rag']:
            try:
                # Simple RAG is handled by the unified rag_service
                init_results['rag_system'] = "simple_available"
            except Exception as e:
                logger.error(f"Simple RAG initialization failed: {e}")
                init_results['rag_system'] = f"simple_error: {e}"
        else:
            init_results['rag_system'] = "not_available"
        
        # Document processing is handled by RAG service
        init_results['document_processing'] = "integrated_with_rag"
        
        return init_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'features': self.features.copy(),
            'startup_errors': self.startup_errors.copy(),
            'status': 'degraded' if self.startup_errors else 'full'
        }
    
    def can_handle_chat(self) -> bool:
        """Check if the system can handle chat requests."""
        return self.features['google_ai'] or self.features['simple_rag']
    
    def can_handle_rag(self) -> bool:
        """Check if the system can handle RAG requests."""
        return self.features['advanced_rag'] or self.features['simple_rag']
    
    def get_recommended_mode(self) -> str:
        """Get recommended operation mode."""
        if self.features['advanced_rag'] and self.features['google_ai']:
            return 'full'
        elif self.features['simple_rag'] and self.features['google_ai']:
            return 'simple_rag'
        elif self.features['simple_rag']:
            return 'basic'
        else:
            return 'minimal'

# Global startup manager
startup_manager = StartupManager()
