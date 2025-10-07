import os
import re
import json
import asyncio
import time
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, InternalServerError

from app.rag_service import rag_service
from app.core.mongo_client import mongo_client
from app.fraud_detect.checker import check_entity
import logging

logger = logging.getLogger(__name__)

class AIService:
    """Unified AI service combining all best features."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.conversation_history = {}
        self.response_cache = {}
        self.entity_cache = {}
        self.rag_cache = {}
        
        # Performance optimization settings
        self.max_concurrent_requests = 5
        self.cache_ttl = 1800  # 30 minutes
        self.rag_cache_ttl = 3600  # 1 hour
        self.entity_cache_ttl = 7200  # 2 hours
        
        # Initialize Google AI
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("Unified AI service initialized with Google AI")
        else:
            logger.warning("No Google API key found, using fallback mode")
            self.model = None
    
    async def generate_response(self, query: str, session_id: str = "default", use_cache: bool = True) -> dict:
        """
        Generate unified AI response with all best features.
        """
        if not self.api_key:
            return {"error": "AI 服務未設定 API 金鑰。"}
        
        try:
            # Check cache first
            if use_cache:
                cache_key = f"{session_id}:{query}"
                if cache_key in self.response_cache:
                    cached_data = self.response_cache[cache_key]
                    if time.time() - cached_data['timestamp'] < self.cache_ttl:
                        logger.info(f"Returning cached response for query: {query[:50]}...")
                        return cached_data['response']
            
            # Start timing
            start_time = time.time()
            
            # Parallel data gathering for maximum performance
            context = await self._gather_context_parallel(query)
            
            # Perform intelligent risk assessment
            risk_level, risk_score, recommendations = self._assess_risk(query, context)
            
            # Get conversation history for context
            history = self.conversation_history.get(session_id, [])
            
            # Build comprehensive prompt
            prompt = self._build_comprehensive_prompt(query, context, history, risk_level, risk_score)
            
            # Generate response with timeout and retry logic
            result = await self._generate_with_retry(prompt, timeout=15)
            response_time = time.time() - start_time
            
            if "error" not in result:
                enhanced_result = {
                    "response": result["response"],
                    "metadata": {
                        "risk_level": risk_level,
                        "risk_score": risk_score,
                        "context_sources": {
                            "rag_results_count": len(context.get('rag_results', [])),
                            "entity_matches_count": len(context.get('entity_matches', [])),
                            "recent_alerts_count": len(context.get('recent_alerts', [])),
                            "official_entities_count": len(context.get('official_entities', [])),
                            "risk_indicators_count": len(context.get('risk_indicators', []))
                        },
                        "recommendations": recommendations,
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id,
                        "query_length": len(query),
                        "context_richness": self._calculate_context_richness(context)
                    }
                }
                
                # Update conversation history
                self._update_conversation_history(session_id, query, enhanced_result)
                
                # Cache the response
                if use_cache:
                    cache_key = f"{session_id}:{query}"
                    self.response_cache[cache_key] = {
                        'response': enhanced_result,
                        'timestamp': time.time()
                    }
                
                # Log analytics
                await self._log_analytics(session_id, query, response_time, "unified_ai", risk_level, len(context.get('rag_results', [])))
                
                return enhanced_result
            
            return result
            
        except Exception as e:
            logger.error(f"Unified response generation failed: {e}")
            return {"error": f"生成回應時發生錯誤: {e}"}
    
    async def _gather_context_parallel(self, query: str) -> Dict[str, Any]:
        """Gather context data in parallel for maximum performance."""
        context = {
            'rag_results': [],
            'entity_matches': [],
            'recent_alerts': [],
            'official_entities': [],
            'risk_indicators': []
        }
        
        # Create tasks for parallel execution
        tasks = []
        
        # RAG search task
        rag_task = asyncio.create_task(self._get_rag_results_cached(query))
        tasks.append(("rag", rag_task))
        
        # Entity extraction and checking
        entity_task = asyncio.create_task(self._extract_and_check_entities(query))
        tasks.append(("entities", entity_task))
        
        # Recent alerts task
        alerts_task = asyncio.create_task(self._get_recent_alerts_cached(limit=5))
        tasks.append(("alerts", alerts_task))
        
        # Official entities task
        official_task = asyncio.create_task(self._get_official_entities_cached(limit=5))
        tasks.append(("official", official_task))
        
        # Risk indicators task
        risk_task = asyncio.create_task(self._get_risk_indicators_cached(query, limit=5))
        tasks.append(("risk", risk_task))
        
        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                timeout=10.0
            )
            
            # Process results
            for i, (task_name, _) in enumerate(tasks):
                result = results[i]
                if not isinstance(result, Exception):
                    if task_name == "rag":
                        context['rag_results'] = result
                    elif task_name == "entities":
                        context['entity_matches'] = result
                    elif task_name == "alerts":
                        context['recent_alerts'] = result
                    elif task_name == "official":
                        context['official_entities'] = result
                    elif task_name == "risk":
                        context['risk_indicators'] = result
                else:
                    logger.warning(f"Task {task_name} failed: {result}")
        
        except asyncio.TimeoutError:
            logger.warning("Context gathering timed out, using partial results")
        
        return context
    
    async def _get_rag_results_cached(self, query: str) -> List[Dict[str, Any]]:
        """Get RAG results with caching."""
        cache_key = f"rag_{hash(query)}"
        
        # Check cache first
        if cache_key in self.rag_cache:
            cached_time, results = self.rag_cache[cache_key]
            if time.time() - cached_time < self.rag_cache_ttl:
                return results
        
        try:
            results = await rag_service.enhanced_search(query, top_k=8)
            # Cache results
            self.rag_cache[cache_key] = (time.time(), results)
            return results
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return []
    
    async def _extract_and_check_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract and check entities with caching."""
        entities = self._extract_entities_from_query(query)
        matches = []
        
        for entity in entities:
            cache_key = f"entity_{hash(entity)}"
            
            # Check entity cache
            if cache_key in self.entity_cache:
                cached_time, result = self.entity_cache[cache_key]
                if time.time() - cached_time < self.entity_cache_ttl:
                    if result.get("is_scam") or result.get("is_licensed"):
                        matches.append(result)
                    continue
            
            try:
                result = await check_entity(entity)
                # Cache result
                self.entity_cache[cache_key] = (time.time(), result)
                
                if result.get("is_scam") or result.get("is_licensed"):
                    matches.append(result)
            except Exception as e:
                logger.warning(f"Entity check failed for '{entity}': {e}")
        
        return matches
    
    async def _get_recent_alerts_cached(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent alerts with caching."""
        cache_key = f"alerts_{limit}"
        
        # Check cache
        if cache_key in self.rag_cache:
            cached_time, results = self.rag_cache[cache_key]
            if time.time() - cached_time < 300:  # 5 minutes cache
                return results
        
        try:
            db = mongo_client.get_db()
            collection = db.sfc_alert_list
            cursor = collection.find({}).sort("date_posted", -1).limit(limit)
            results = await cursor.to_list(length=limit)
            
            # Cache results
            self.rag_cache[cache_key] = (time.time(), results)
            return results
        except Exception as e:
            logger.warning(f"Failed to get recent alerts: {e}")
            return []
    
    async def _get_official_entities_cached(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get official entities with caching."""
        cache_key = f"official_{limit}"
        
        # Check cache
        if cache_key in self.rag_cache:
            cached_time, results = self.rag_cache[cache_key]
            if time.time() - cached_time < 600:  # 10 minutes cache
                return results
        
        try:
            db = mongo_client.get_db()
            collection = db.licensed_entities
            cursor = collection.find({}).limit(limit)
            results = await cursor.to_list(length=limit)
            
            # Cache results
            self.rag_cache[cache_key] = (time.time(), results)
            return results
        except Exception as e:
            logger.warning(f"Failed to get official entities: {e}")
            return []
    
    async def _get_risk_indicators_cached(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get risk indicators with caching."""
        cache_key = f"risk_{hash(query)}_{limit}"
        
        # Check cache
        if cache_key in self.rag_cache:
            cached_time, results = self.rag_cache[cache_key]
            if time.time() - cached_time < 300:  # 5 minutes cache
                return results
        
        try:
            db = mongo_client.get_db()
            collection = db.scam_indicators
            
            # Search for relevant risk indicators
            search_terms = self._extract_search_terms(query)
            results = []
            
            for term in search_terms:
                cursor = collection.find({
                    "$or": [
                        {"value": {"$regex": term, "$options": "i"}},
                        {"alleged_name": {"$regex": term, "$options": "i"}}
                    ]
                }).limit(limit)
                term_results = await cursor.to_list(length=limit)
                results.extend(term_results)
            
            # Remove duplicates
            seen = set()
            unique_results = []
            for result in results:
                result_id = result.get('_id')
                if result_id not in seen:
                    seen.add(result_id)
                    unique_results.append(result)
            
            # Cache results
            self.rag_cache[cache_key] = (time.time(), unique_results[:limit])
            return unique_results[:limit]
        except Exception as e:
            logger.warning(f"Failed to get risk indicators: {e}")
            return []
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """Extract potential entities from query."""
        entities = []
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, query)
        entities.extend(urls)
        
        # Extract potential company names (Chinese and English)
        company_patterns = [
            r'[\u4e00-\u9fff]+(?:證券|投資|金融|基金|保險|銀行|公司|集團|控股|有限|股份)',
            r'[A-Za-z\s]+(?:Securities|Investment|Finance|Fund|Insurance|Bank|Corp|Group|Holdings|Limited|Inc)',
            r'[\u4e00-\u9fff]{2,6}(?=\s|$)',  # Chinese words 2-6 characters
            r'[A-Za-z]{3,15}(?=\s|$)'  # English words 3-15 characters
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Remove duplicates and filter
        entities = list(set([e.strip() for e in entities if len(e.strip()) > 1]))
        return entities[:5]  # Limit to 5 entities
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract search terms from query."""
        stop_words = {'的', '是', '在', '有', '和', '與', '或', '但', '如果', '因為', '所以', 'the', 'is', 'are', 'and', 'or', 'but', 'if', 'because', 'so'}
        
        # Split by spaces and punctuation
        terms = re.findall(r'[\u4e00-\u9fff]+|[A-Za-z]+', query)
        terms = [term for term in terms if term.lower() not in stop_words and len(term) > 1]
        
        return terms[:3]  # Limit to 3 terms
    
    def _assess_risk(self, query: str, context: Dict[str, Any]) -> Tuple[str, float, List[str]]:
        """Comprehensive risk assessment based on context."""
        risk_score = 0.0
        risk_factors = []
        
        # Check for scam indicators
        if context.get('entity_matches'):
            scam_count = sum(1 for match in context['entity_matches'] if match.get('is_scam'))
            if scam_count > 0:
                risk_score += 0.4
                risk_factors.append(f"發現 {scam_count} 個詐騙實體")
        
        # Check for high-risk RAG results
        rag_results = context.get('rag_results', [])
        high_risk_rag = sum(1 for result in rag_results if result.get('metadata', {}).get('risk_level') == 'HIGH')
        if high_risk_rag > 0:
            risk_score += 0.8  
            risk_factors.append(f"RAG 發現 {high_risk_rag} 個高風險結果")
        
        # extra check for SFC alert list matches in RAG results
        for result in rag_results:
            metadata = result.get('metadata', {})
            if metadata.get('collection') == 'sfc_alert_list':
                risk_score += 0.9  # 極高風險
                risk_factors.append(f"該實體在 SFC 警示名單中")
                break
        
        # Check for risk indicators
        if context.get('risk_indicators'):
            risk_score += 0.2
            risk_factors.append("發現風險指標")
        
        # Check for suspicious keywords
        suspicious_keywords = ['投資', '回報', '保證', '高收益', '快速', '緊急', '限時', '獨家', '內幕']
        query_lower = query.lower()
        for keyword in suspicious_keywords:
            if keyword in query_lower:
                risk_score += 0.1
                risk_factors.append(f"包含可疑關鍵詞: {keyword}")
        
        # Check for licensed entities (reduces risk)
        licensed_count = sum(1 for match in context.get('entity_matches', []) if match.get('is_licensed'))
        if licensed_count > 0:
            risk_score -= 0.2
            risk_factors.append(f"發現 {licensed_count} 個持牌實體")
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "高風險"
        elif risk_score >= 0.4:
            risk_level = "中風險"
        elif risk_score >= 0.2:
            risk_level = "低風險"
        else:
            risk_level = "安全"
        
        # Generate recommendations
        recommendations = []
        if risk_score >= 0.7:
            recommendations.append("強烈建議避免此投資機會")
            recommendations.append("建議向相關監管機構舉報")
            recommendations.append("請勿提供個人資料或資金")
        elif risk_score >= 0.4:
            recommendations.append("建議謹慎評估此投資機會")
            recommendations.append("建議查詢更多官方信息")
            recommendations.append("建議諮詢專業財務顧問")
        elif risk_score >= 0.2:
            recommendations.append("建議進一步核實信息")
            recommendations.append("建議查詢官方資料庫")
        else:
            recommendations.append("未發現明顯風險")
            recommendations.append("建議持續關注相關資訊")
        
        return risk_level, max(0.0, min(1.0, risk_score)), recommendations
    
    def _build_comprehensive_prompt(self, query: str, context: Dict[str, Any], history: List[Dict], risk_level: str, risk_score: float) -> str:
        """Build comprehensive prompt for detailed analysis."""
        prompt = f"""你是一個專業的香港金融詐騙分析專家，具有豐富的監管知識和風險評估經驗。請分析以下查詢並提供專業、準確的回應。

查詢: {query}

風險評估: {risk_level} (風險分數: {risk_score:.2f})

相關信息:
"""
        
        # Add RAG results
        rag_results = context.get('rag_results', [])
        if rag_results:
            prompt += "\n相關警示信息:\n"
            for i, result in enumerate(rag_results[:5], 1):
                prompt += f"{i}. {result.get('text', '')[:300]}...\n"
        
        # Add entity matches
        entity_matches = context.get('entity_matches', [])
        if entity_matches:
            prompt += "\n實體檢查結果:\n"
            for match in entity_matches:
                if match.get('is_scam'):
                    prompt += f"- 詐騙實體: {match.get('entity', '')} - {match.get('message', '')}\n"
                elif match.get('is_licensed'):
                    prompt += f"- 持牌實體: {match.get('entity', '')} - {match.get('message', '')}\n"
        
        # Add recent alerts
        recent_alerts = context.get('recent_alerts', [])
        if recent_alerts:
            prompt += "\n最近相關警示:\n"
            for alert in recent_alerts[:3]:
                company_name = alert.get('company_name_tc', '') or alert.get('company_name_en', '')
                website = alert.get('website', '')
                if company_name:
                    prompt += f"- {company_name} ({website})\n"
        
        # Add conversation history
        if history:
            prompt += "\n對話歷史:\n"
            for exchange in history[-3:]:  # Last 3 exchanges
                prompt += f"用戶: {exchange.get('user', '')}\n"
                prompt += f"助手: {exchange.get('assistant', '')[:100]}...\n"
        
        prompt += f"""
請提供專業分析，包括:

1. **風險評估**: 基於以上信息，詳細分析風險等級和原因
2. **具體建議**: 針對性的建議和行動方案
3. **監管信息**: 相關的香港監管機構信息和查詢方式
4. **預防措施**: 如何避免類似風險的建議

回應要求:
- 使用繁體中文
- 專業、客觀、準確
- 結構清晰，重點突出
- 提供實用的建議和資源
- 字數控制在300-500字之間
"""
        
        return prompt
    
    async def _generate_with_retry(self, prompt: str, timeout: int = 15, max_retries: int = 3) -> dict:
        """Generate response with retry logic and timeout."""
        for attempt in range(max_retries):
            try:
                if not self.model:
                    return {"error": "AI 模型未初始化"}
                
                # Use asyncio.wait_for for timeout
                response = await asyncio.wait_for(
                    self._generate_async(prompt),
                    timeout=timeout
                )
                return {"response": response}
                
            except asyncio.TimeoutError:
                logger.warning(f"AI generation timed out (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return {"error": "AI 回應超時，請稍後再試"}
            except ResourceExhausted:
                logger.warning(f"API quota exceeded (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return {"error": "API 配額已用完，請稍後再試"}
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except InternalServerError:
                logger.warning(f"Internal server error (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    return {"error": "AI 服務暫時不可用，請稍後再試"}
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"AI generation failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"error": f"AI 生成失敗: {e}"}
                await asyncio.sleep(1)
        
        return {"error": "AI 生成失敗，已達最大重試次數"}
    
    async def _generate_async(self, prompt: str) -> str:
        """Async wrapper for AI generation."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_sync, prompt)
    
    def _generate_sync(self, prompt: str) -> str:
        """Synchronous AI generation."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Sync AI generation failed: {e}")
            raise e
    
    def _update_conversation_history(self, session_id: str, query: str, response: dict):
        """Update conversation history efficiently."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "user": query,
            "assistant": response["response"],
            "metadata": response["metadata"]
        })
        
        # Keep only last 10 exchanges for performance
        if len(self.conversation_history[session_id]) > 10:
            self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
    
    def _calculate_context_richness(self, context: Dict[str, Any]) -> str:
        """Calculate context richness score."""
        total_sources = sum(len(v) if isinstance(v, list) else 0 for v in context.values())
        if total_sources >= 15:
            return "豐富"
        elif total_sources >= 8:
            return "中等"
        elif total_sources >= 3:
            return "基本"
        else:
            return "有限"
    
    async def _log_analytics(self, session_id: str, query: str, response_time: float, source: str, risk_level: str = "unknown", rag_count: int = 0):
        """Log analytics efficiently."""
        try:
            # Simple analytics logging without external service
            logger.info(f"Query logged - Session: {session_id}, Response time: {response_time:.2f}s, Risk: {risk_level}, Source: {source}")
        except Exception as e:
            logger.warning(f"Failed to log analytics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "conversation_sessions": len(self.conversation_history),
            "rag_cache_size": len(self.rag_cache),
            "entity_cache_size": len(self.entity_cache),
            "api_configured": self.api_key is not None,
            "model_available": self.model is not None,
            "cache_ttl": self.cache_ttl,
            "rag_cache_ttl": self.rag_cache_ttl,
            "entity_cache_ttl": self.entity_cache_ttl
        }

# Create global instance
ai_service = AIService()

# Legacy function for backward compatibility
async def generate_response(prompt: str) -> dict:
    """Legacy function for backward compatibility."""
    return await ai_service.generate_response(prompt)

async def generate_rag_response(query: str, session_id: str = "default") -> dict:
    """Legacy function for backward compatibility."""
    return await ai_service.generate_response(query, session_id)

async def initialize_rag_system() -> bool:
    """Legacy function for backward compatibility."""
    try:
        return await rag_service.build_vector_index()
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        return False
