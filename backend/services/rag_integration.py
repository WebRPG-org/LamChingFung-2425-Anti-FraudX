"""
RAG 集成服務 - Phase 1.2 實現
集成真實騙案數據庫，提升系統的現實性和精準度
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from utils.logger import log


class VectorStore:
    """向量存儲 - 管理騙案數據的向量化存儲"""
    
    def __init__(self, store_type: str = "chroma"):
        """
        初始化向量存儲
        
        Args:
            store_type: 存儲類型 (chroma/pinecone)
        """
        self.store_type = store_type
        self.cases: Dict[str, Dict[str, Any]] = {}  # 本地存儲
        self.embeddings: Dict[str, List[float]] = {}  # 嵌入向量
        
        log.info(f"✅ 向量存儲已初始化: {store_type}")
    
    async def add_case(self, case_id: str, case_data: Dict[str, Any], embedding: List[float]) -> bool:
        """
        添加騙案到存儲
        
        Args:
            case_id: 案例 ID
            case_data: 案例數據
            embedding: 嵌入向量
        
        Returns:
            是否添加成功
        """
        try:
            self.cases[case_id] = {
                **case_data,
                "added_at": datetime.now().isoformat()
            }
            self.embeddings[case_id] = embedding
            
            log.info(f"✅ 騙案已添加: {case_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 添加騙案失敗: {e}")
            return False
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        搜索相似的騙案
        
        Args:
            query_embedding: 查詢嵌入向量
            top_k: 返回的最大結果數
        
        Returns:
            [(case_id, similarity_score), ...] 列表
        """
        try:
            if not self.embeddings:
                log.warning("⚠️ 向量存儲為空")
                return []
            
            # 計算相似度（簡單的餘弦相似度）
            similarities = []
            for case_id, embedding in self.embeddings.items():
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append((case_id, similarity))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 返回前 top_k 個
            results = similarities[:top_k]
            
            log.info(f"✅ 搜索完成: 找到 {len(results)} 個相似案例")
            return results
        
        except Exception as e:
            log.error(f"❌ 搜索失敗: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """計算餘弦相似度"""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
            magnitude2 = sum(b ** 2 for b in vec2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        
        except Exception as e:
            log.error(f"❌ 相似度計算失敗: {e}")
            return 0.0
    
    async def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取騙案詳情
        
        Args:
            case_id: 案例 ID
        
        Returns:
            案例數據，如果不存在則返回 None
        """
        return self.cases.get(case_id)
    
    async def list_cases(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出所有騙案
        
        Args:
            limit: 返回的最大案例數
            offset: 偏移量
        
        Returns:
            案例列表
        """
        try:
            cases_list = list(self.cases.values())[offset:offset+limit]
            return cases_list
        
        except Exception as e:
            log.error(f"❌ 列出案例失敗: {e}")
            return []


class EmbeddingModel:
    """嵌入模型 - 將文本轉換為向量"""
    
    def __init__(self, model_type: str = "simple"):
        """
        初始化嵌入模型
        
        Args:
            model_type: 模型類型 (simple/sentence_transformer/openai)
        """
        self.model_type = model_type
        
        log.info(f"✅ 嵌入模型已初始化: {model_type}")
    
    async def embed(self, text: str) -> List[float]:
        """
        將文本轉換為向量
        
        Args:
            text: 輸入文本
        
        Returns:
            嵌入向量
        """
        try:
            if self.model_type == "simple":
                return self._simple_embed(text)
            elif self.model_type == "sentence_transformer":
                return await self._sentence_transformer_embed(text)
            elif self.model_type == "openai":
                return await self._openai_embed(text)
            else:
                log.warning(f"⚠️ 未知的模型類型: {self.model_type}")
                return self._simple_embed(text)
        
        except Exception as e:
            log.error(f"❌ 嵌入失敗: {e}")
            return []
    
    def _simple_embed(self, text: str) -> List[float]:
        """簡單的嵌入方法（基於字符頻率）"""
        try:
            # 創建一個簡單的 128 維向量
            vector = [0.0] * 128
            
            # 基於文本長度和字符頻率填充向量
            text_lower = text.lower()
            for i, char in enumerate(text_lower[:128]):
                vector[i] = ord(char) / 256.0
            
            # 歸一化
            magnitude = sum(v ** 2 for v in vector) ** 0.5
            if magnitude > 0:
                vector = [v / magnitude for v in vector]
            
            return vector
        
        except Exception as e:
            log.error(f"❌ 簡單嵌入失敗: {e}")
            return [0.0] * 128
    
    async def _sentence_transformer_embed(self, text: str) -> List[float]:
        """使用 Sentence Transformer 的嵌入方法"""
        try:
            # TODO: 集成 Sentence Transformer
            log.info("⏳ Sentence Transformer 嵌入待實現")
            return self._simple_embed(text)
        
        except Exception as e:
            log.error(f"❌ Sentence Transformer 嵌入失敗: {e}")
            return []
    
    async def _openai_embed(self, text: str) -> List[float]:
        """使用 OpenAI 的嵌入方法"""
        try:
            # TODO: 集成 OpenAI Embeddings API
            log.info("⏳ OpenAI 嵌入待實現")
            return self._simple_embed(text)
        
        except Exception as e:
            log.error(f"❌ OpenAI 嵌入失敗: {e}")
            return []


class ScamCaseDatabase:
    """騙案數據庫 - 管理真實騙案數據"""
    
    def __init__(self):
        """初始化騙案數據庫"""
        self.cases: Dict[str, Dict[str, Any]] = {}
        
        log.info("✅ 騙案數據庫已初始化")
    
    async def add_case(self, case_id: str, case_data: Dict[str, Any]) -> bool:
        """
        添加騙案
        
        Args:
            case_id: 案例 ID
            case_data: 案例數據
        
        Returns:
            是否添加成功
        """
        try:
            self.cases[case_id] = {
                **case_data,
                "created_at": datetime.now().isoformat()
            }
            
            log.info(f"✅ 騙案已添加: {case_id}")
            return True
        
        except Exception as e:
            log.error(f"❌ 添加騙案失敗: {e}")
            return False
    
    async def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取騙案
        
        Args:
            case_id: 案例 ID
        
        Returns:
            案例數據，如果不存在則返回 None
        """
        return self.cases.get(case_id)
    
    async def list_cases_by_type(self, scam_type: str) -> List[Dict[str, Any]]:
        """
        按騙術類型列出騙案
        
        Args:
            scam_type: 騙術類型
        
        Returns:
            案例列表
        """
        try:
            filtered_cases = [
                case for case in self.cases.values()
                if case.get("scam_type") == scam_type
            ]
            
            return filtered_cases
        
        except Exception as e:
            log.error(f"❌ 列出騙案失敗: {e}")
            return []


class RAGIntegration:
    """RAG 集成 - 檢索增強生成"""
    
    def __init__(self, embedding_model_type: str = "simple", vector_store_type: str = "chroma"):
        """
        初始化 RAG 集成
        
        Args:
            embedding_model_type: 嵌入模型類型
            vector_store_type: 向量存儲類型
        """
        self.embedding_model = EmbeddingModel(embedding_model_type)
        self.vector_store = VectorStore(vector_store_type)
        self.case_database = ScamCaseDatabase()
        self.cache: Dict[str, List[Dict[str, Any]]] = {}  # 查詢緩存
        
        log.info("✅ RAG 集成已初始化")
    
    async def initialize_with_cases(self, cases: List[Dict[str, Any]]) -> int:
        """
        使用騙案初始化 RAG
        
        Args:
            cases: 騙案列表
        
        Returns:
            初始化的案例數
        """
        try:
            initialized_count = 0
            
            for i, case in enumerate(cases):
                case_id = case.get("id", f"case_{i}")
                
                # 添加到數據庫
                await self.case_database.add_case(case_id, case)
                
                # 生成嵌入向量
                case_text = self._prepare_case_text(case)
                embedding = await self.embedding_model.embed(case_text)
                
                # 添加到向量存儲
                await self.vector_store.add_case(case_id, case, embedding)
                
                initialized_count += 1
            
            log.info(f"✅ RAG 已初始化: {initialized_count} 個案例")
            return initialized_count
        
        except Exception as e:
            log.error(f"❌ RAG 初始化失敗: {e}")
            return 0
    
    async def retrieve_relevant_cases(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        檢索相關的騙案
        
        Args:
            query: 查詢文本
            top_k: 返回的最大案例數
        
        Returns:
            相關案例列表
        """
        try:
            # 檢查緩存
            cache_key = f"{query}_{top_k}"
            if cache_key in self.cache:
                log.info(f"✅ 從緩存返回結果: {query}")
                return self.cache[cache_key]
            
            # 生成查詢嵌入
            query_embedding = await self.embedding_model.embed(query)
            
            # 搜索相似案例
            search_results = await self.vector_store.search(query_embedding, top_k)
            
            # 獲取案例詳情
            relevant_cases = []
            for case_id, similarity_score in search_results:
                case = await self.vector_store.get_case(case_id)
                if case:
                    case["similarity_score"] = similarity_score
                    relevant_cases.append(case)
            
            # 緩存結果
            self.cache[cache_key] = relevant_cases
            
            log.info(f"✅ 檢索完成: 找到 {len(relevant_cases)} 個相關案例")
            return relevant_cases
        
        except Exception as e:
            log.error(f"❌ 檢索失敗: {e}")
            return []
    
    async def inject_cases_to_prompt(self, query: str, prompt: str, top_k: int = 3) -> str:
        """
        將相關案例注入到 prompt 中
        
        Args:
            query: 查詢文本
            prompt: 原始 prompt
            top_k: 注入的最大案例數
        
        Returns:
            注入案例後的 prompt
        """
        try:
            # 檢索相關案例
            relevant_cases = await self.retrieve_relevant_cases(query, top_k)
            
            if not relevant_cases:
                log.warning("⚠️ 未找到相關案例")
                return prompt
            
            # 構建案例文本
            cases_text = self._format_cases_for_prompt(relevant_cases)
            
            # 注入到 prompt
            injected_prompt = f"""{prompt}

【相關真實騙案參考】
{cases_text}

請根據上述真實騙案，提供更貼近現實的回應。"""
            
            log.info(f"✅ 已注入 {len(relevant_cases)} 個案例到 prompt")
            return injected_prompt
        
        except Exception as e:
            log.error(f"❌ 注入案例失敗: {e}")
            return prompt
    
    def _prepare_case_text(self, case: Dict[str, Any]) -> str:
        """準備案例文本用於嵌入"""
        try:
            parts = []
            
            if "title" in case:
                parts.append(case["title"])
            
            if "description" in case:
                parts.append(case["description"])
            
            if "scam_type" in case:
                parts.append(f"騙術類型: {case['scam_type']}")
            
            if "tactics" in case:
                parts.append(f"騙術方法: {', '.join(case['tactics'])}")
            
            if "prevention" in case:
                parts.append(f"防騙方法: {', '.join(case['prevention'])}")
            
            return " ".join(parts)
        
        except Exception as e:
            log.error(f"❌ 準備案例文本失敗: {e}")
            return ""
    
    def _format_cases_for_prompt(self, cases: List[Dict[str, Any]]) -> str:
        """格式化案例用於 prompt 注入"""
        try:
            formatted_cases = []
            
            for i, case in enumerate(cases, 1):
                case_text = f"""
案例 {i}:
- 標題: {case.get('title', 'N/A')}
- 騙術類型: {case.get('scam_type', 'N/A')}
- 描述: {case.get('description', 'N/A')}
- 騙術方法: {', '.join(case.get('tactics', []))}
- 防騙方法: {', '.join(case.get('prevention', []))}
- 相似度: {case.get('similarity_score', 0):.2%}
"""
                formatted_cases.append(case_text)
            
            return "\n".join(formatted_cases)
        
        except Exception as e:
            log.error(f"❌ 格式化案例失敗: {e}")
            return ""
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        獲取 RAG 統計信息
        
        Returns:
            統計信息
        """
        try:
            total_cases = len(self.case_database.cases)
            cached_queries = len(self.cache)
            
            # 按騙術類型統計
            scam_types = {}
            for case in self.case_database.cases.values():
                scam_type = case.get("scam_type", "unknown")
                scam_types[scam_type] = scam_types.get(scam_type, 0) + 1
            
            return {
                "total_cases": total_cases,
                "cached_queries": cached_queries,
                "scam_types": scam_types,
                "embedding_model": self.embedding_model.model_type,
                "vector_store": self.vector_store.store_type
            }
        
        except Exception as e:
            log.error(f"❌ 獲取統計信息失敗: {e}")
            return {}


# 全局 RAG 實例
_rag_integration: Optional[RAGIntegration] = None

def get_rag_integration() -> RAGIntegration:
    """獲取 RAG 集成實例"""
    global _rag_integration
    if _rag_integration is None:
        _rag_integration = RAGIntegration()
    return _rag_integration


