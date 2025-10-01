import os
import json
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Try to import advanced dependencies, fallback to simple if not available
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    ADVANCED_RAG_AVAILABLE = True
except ImportError:
    ADVANCED_RAG_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Advanced RAG dependencies not available, using simple RAG")

from thefuzz import fuzz
from app.core.mongo_client import mongo_client
from app.fraud_detect.checker import check_entity

logger = logging.getLogger(__name__)

class RAGService:
    """Unified RAG service combining advanced and simple features."""
    
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.document_metadata = []
        self.initialized = False
        self.total_documents = 0
        self.cache_size = 0
        self.collections_stats = {
            "sfc_alerts": 0,
            "licensed_entities": 0,
            "official_contacts": 0,
            "scam_indicators": 0
        }
        
        # Initialize based on available dependencies
        if ADVANCED_RAG_AVAILABLE:
            self._initialize_embedding_model()
        else:
            logger.info("Using simple RAG mode")
    
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model for embeddings."""
        try:
            # Use a multilingual model that supports Chinese and English
            self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Advanced embedding model initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize multilingual model, trying alternative: {e}")
            try:
                # Fallback to a more basic model
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Fallback embedding model initialized successfully")
            except Exception as e2:
                logger.error(f"Failed to initialize any embedding model: {e2}")
                self.embedding_model = None
    
    async def build_vector_index(self, use_processed_docs: bool = True) -> bool:
        """Build or rebuild the vector index from MongoDB documents."""
        if ADVANCED_RAG_AVAILABLE and self.embedding_model:
            return await self._build_advanced_index()
        else:
            return await self._build_simple_index()
    
    async def _build_advanced_index(self) -> bool:
        """Build advanced vector index using embeddings."""
        try:
            db = mongo_client.get_db()
            
            # Collect documents from multiple collections
            documents = []
            metadata = []
            
            # 1. SFC Alert List
            sfc_cursor = db.sfc_alert_list.find({})
            sfc_docs = await sfc_cursor.to_list(length=None)
            self.collections_stats["sfc_alerts"] = len(sfc_docs)
            
            for doc in sfc_docs:
                text = f"香港證監會警示名單：公司名稱 {doc.get('company_name', '')}。類型 {doc.get('type', '')}。添加日期 {doc.get('add_date', '')}。此實體未獲香港證監會發牌，可能涉及詐騙或未經授權的金融活動。"
                documents.append(text)
                metadata.append({
                    'collection': 'sfc_alert_list',
                    'id': str(doc['_id']),
                    'company_name': doc.get('company_name', ''),
                    'entity_type': doc.get('type', ''),
                    'add_date': doc.get('add_date', ''),
                    'source_url': doc.get('source_url', ''),
                    'risk_level': 'HIGH',
                    'type': 'unlicensed_entity'
                })
            
            # 2. Licensed Entities (HKMA Authorized Institutions)
            entity_cursor = db.licensed_entities.find({})
            entities = await entity_cursor.to_list(length=None)
            self.collections_stats["licensed_entities"] = len(entities)
            
            for entity in entities:
                text = f"香港金融管理局認可機構：名稱 {entity.get('name_tc', '')} ({entity.get('name_en', '')})。母公司 {entity.get('parent_institution', '')}。類別 {entity.get('segment', '')}。此實體為香港金融管理局認可的金融機構，屬合法運營。"
                documents.append(text)
                metadata.append({
                    'collection': 'licensed_entities',
                    'id': str(entity['_id']),
                    'name_tc': entity.get('name_tc', ''),
                    'name_en': entity.get('name_en', ''),
                    'parent_institution': entity.get('parent_institution', ''),
                    'segment': entity.get('segment', ''),
                    'risk_level': 'LOW',
                    'type': 'licensed_entity'
                })
            
            # 3. Official Contacts (HKMA Hotlines)
            official_cursor = db.official_contacts.find({})
            official_contacts = await official_cursor.to_list(length=None)
            self.collections_stats["official_contacts"] = len(official_contacts)
            
            for contact in official_contacts:
                text = f"香港金融管理局官方聯絡方式：機構名稱 {contact.get('entity_name_tc', '')} ({contact.get('entity_name_en', '')})。熱線電話 {contact.get('value', '')}。此為官方提供的聯絡方式，可用於核實信息。"
                documents.append(text)
                metadata.append({
                    'collection': 'official_contacts',
                    'id': str(contact['_id']),
                    'entity_name_tc': contact.get('entity_name_tc', ''),
                    'entity_name_en': contact.get('entity_name_en', ''),
                    'hotline': contact.get('value', ''),
                    'risk_level': 'LOW',
                    'type': 'official_contact'
                })
            
            # 4. Scam Indicators (HKMA Fraudulent Scams)
            scam_cursor = db.scam_indicators.find({})
            scam_indicators = await scam_cursor.to_list(length=None)
            self.collections_stats["scam_indicators"] = len(scam_indicators)
            
            for scam in scam_indicators:
                text = f"詐騙警示：可疑實體/網站 {scam.get('value', '')}。類型 {scam.get('type', '')}。聲稱名稱 {scam.get('alleged_name', '')}。報告日期 {scam.get('report_date', '')}。來源 {scam.get('source', '')}。此實體/網站已被列為詐騙或可疑，請提高警惕。"
                documents.append(text)
                metadata.append({
                    'collection': 'scam_indicators',
                    'id': str(scam['_id']),
                    'value': scam.get('value', ''),
                    'type': scam.get('type', ''),
                    'alleged_name': scam.get('alleged_name', ''),
                    'report_date': scam.get('report_date', ''),
                    'risk_level': 'HIGH',
                    'type': 'scam_indicator'
                })
            
            if not documents:
                logger.warning("No documents found to build index")
                return False
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = self.embedding_model.encode(documents, show_progress_bar=True)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            self.documents = documents
            self.document_metadata = metadata
            self.total_documents = len(documents)
            self.initialized = True
            
            logger.info(f"Advanced vector index built successfully with {self.total_documents} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build advanced vector index: {e}")
            # Fallback to simple index
            return await self._build_simple_index()
    
    async def _build_simple_index(self) -> bool:
        """Build simple document index without embeddings."""
        try:
            db = mongo_client.get_db()
            
            # Collect documents from multiple collections
            documents = []
            metadata = []
            
            # 1. SFC Alert List
            sfc_cursor = db.sfc_alert_list.find({})
            sfc_docs = await sfc_cursor.to_list(length=None)
            self.collections_stats["sfc_alerts"] = len(sfc_docs)
            
            for doc in sfc_docs:
                text = f"香港證監會警示名單：公司名稱 {doc.get('company_name', '')}。類型 {doc.get('type', '')}。添加日期 {doc.get('add_date', '')}。此實體未獲香港證監會發牌，可能涉及詐騙或未經授權的金融活動。"
                documents.append(text)
                metadata.append({
                    'collection': 'sfc_alert_list',
                    'id': str(doc['_id']),
                    'company_name': doc.get('company_name', ''),
                    'entity_type': doc.get('type', ''),
                    'add_date': doc.get('add_date', ''),
                    'source_url': doc.get('source_url', ''),
                    'risk_level': 'HIGH',
                    'type': 'unlicensed_entity'
                })
            
            # 2. Licensed Entities
            entity_cursor = db.licensed_entities.find({})
            entities = await entity_cursor.to_list(length=None)
            self.collections_stats["licensed_entities"] = len(entities)
            
            for entity in entities:
                text = f"香港金融管理局認可機構：名稱 {entity.get('name_tc', '')} ({entity.get('name_en', '')})。母公司 {entity.get('parent_institution', '')}。類別 {entity.get('segment', '')}。此實體為香港金融管理局認可的金融機構，屬合法運營。"
                documents.append(text)
                metadata.append({
                    'collection': 'licensed_entities',
                    'id': str(entity['_id']),
                    'name_tc': entity.get('name_tc', ''),
                    'name_en': entity.get('name_en', ''),
                    'parent_institution': entity.get('parent_institution', ''),
                    'segment': entity.get('segment', ''),
                    'risk_level': 'LOW',
                    'type': 'licensed_entity'
                })
            
            # 3. Official Contacts
            official_cursor = db.official_contacts.find({})
            official_contacts = await official_cursor.to_list(length=None)
            self.collections_stats["official_contacts"] = len(official_contacts)
            
            for contact in official_contacts:
                text = f"香港金融管理局官方聯絡方式：機構名稱 {contact.get('entity_name_tc', '')} ({contact.get('entity_name_en', '')})。熱線電話 {contact.get('value', '')}。此為官方提供的聯絡方式，可用於核實信息。"
                documents.append(text)
                metadata.append({
                    'collection': 'official_contacts',
                    'id': str(contact['_id']),
                    'entity_name_tc': contact.get('entity_name_tc', ''),
                    'entity_name_en': contact.get('entity_name_en', ''),
                    'hotline': contact.get('value', ''),
                    'risk_level': 'LOW',
                    'type': 'official_contact'
                })
            
            # 4. Scam Indicators
            scam_cursor = db.scam_indicators.find({})
            scam_indicators = await scam_cursor.to_list(length=None)
            self.collections_stats["scam_indicators"] = len(scam_indicators)
            
            for scam in scam_indicators:
                text = f"詐騙警示：可疑實體/網站 {scam.get('value', '')}。類型 {scam.get('type', '')}。聲稱名稱 {scam.get('alleged_name', '')}。報告日期 {scam.get('report_date', '')}。來源 {scam.get('source', '')}。此實體/網站已被列為詐騙或可疑，請提高警惕。"
                documents.append(text)
                metadata.append({
                    'collection': 'scam_indicators',
                    'id': str(scam['_id']),
                    'value': scam.get('value', ''),
                    'type': scam.get('type', ''),
                    'alleged_name': scam.get('alleged_name', ''),
                    'report_date': scam.get('report_date', ''),
                    'risk_level': 'HIGH',
                    'type': 'scam_indicator'
                })
            
            self.documents = documents
            self.document_metadata = metadata
            self.total_documents = len(documents)
            self.initialized = True
            
            logger.info(f"Simple document index built successfully with {self.total_documents} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build simple document index: {e}")
            self.initialized = False
            return False
    
    async def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using the appropriate method."""
        if ADVANCED_RAG_AVAILABLE and self.embedding_model and self.index is not None:
            return await self._advanced_semantic_search(query, top_k)
        else:
            return await self._simple_semantic_search(query, top_k)
    
    async def _advanced_semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform advanced semantic search using embeddings."""
        if not self.initialized or not self.index:
            logger.error("Vector index not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search the index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    result = {
                        'text': self.documents[idx],
                        'metadata': self.document_metadata[idx],
                        'score': float(score)
                    }
                    results.append(result)
            
            logger.info(f"Advanced semantic search for '{query[:50]}...' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Advanced semantic search failed: {e}")
            # Fallback to simple search
            return await self._simple_semantic_search(query, top_k)
    
    async def _simple_semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform simple semantic search using fuzzy matching."""
        if not self.initialized:
            logger.warning("RAG service not initialized. Building index now...")
            await self.build_vector_index()
            if not self.initialized:
                logger.error("Failed to initialize RAG service.")
                return []
        
        results = []
        query_lower = query.lower()
        
        # Prioritize exact matches and high fuzzy scores
        for i, doc in enumerate(self.documents):
            text_lower = doc.lower()
            
            # Exact phrase match
            if query_lower in text_lower:
                results.append((100, i))  # Highest score for exact match
                continue
            
            # Fuzzy ratio match
            fuzz_score = fuzz.ratio(query_lower, text_lower)
            if fuzz_score > 70:  # Threshold for good fuzzy match
                results.append((fuzz_score, i))
                continue
            
            # Token set ratio (good for reordered words)
            token_set_score = fuzz.token_set_ratio(query_lower, text_lower)
            if token_set_score > 70:
                results.append((token_set_score, i))
                continue
            
            # Partial ratio (good for sub-strings)
            partial_score = fuzz.partial_ratio(query_lower, text_lower)
            if partial_score > 80:  # Higher threshold for partial match
                results.append((partial_score * 0.8, i))  # Slightly lower weight
                continue
        
        # Sort by score in descending order and get top_k unique results
        results = sorted(results, key=lambda x: x[0], reverse=True)
        
        unique_results = []
        seen_texts = set()
        for score, idx in results:
            if self.documents[idx] not in seen_texts:
                result = {
                    'text': self.documents[idx],
                    'metadata': self.document_metadata[idx],
                    'score': score
                }
                unique_results.append(result)
                seen_texts.add(self.documents[idx])
            if len(unique_results) >= top_k:
                break
        
        logger.info(f"Simple semantic search for '{query[:50]}...' returned {len(unique_results)} results")
        return unique_results
    
    async def enhanced_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Enhanced search method that combines multiple approaches."""
        return await self.semantic_search(query, top_k)
    
    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the RAG service."""
        return {
            "initialized": self.initialized,
            "total_documents": self.total_documents,
            "cache_size": self.cache_size,
            "collections": self.collections_stats,
            "advanced_mode": ADVANCED_RAG_AVAILABLE and self.embedding_model is not None,
            "index_type": "vector" if self.index is not None else "simple"
        }
    
    async def rebuild_index(self) -> bool:
        """Rebuild the entire index."""
        logger.info("Rebuilding RAG index...")
        return await self.build_vector_index()

# Create global instance
rag_service = RAGService()

# Legacy compatibility functions
async def build_vector_index() -> bool:
    """Legacy function for backward compatibility."""
    return await rag_service.build_vector_index()

async def semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    return await rag_service.semantic_search(query, top_k)