"""
RAG 整合方案 - 最終簡化版
基於診斷結果優化，使用距離閾值而非相似度轉換
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 添加 backend 到路徑
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.rag_service import query_db, build_and_persist_db
from utils.logger import log


# 騙案類型同義詞庫
SCAM_TYPE_SYNONYMS = {
    "假冒銀行": ["銀行職員", "貸款", "信用卡", "賬戶"],
    "假冒官員": ["政府部門", "警察", "海關", "入境處"],
    "投資詐騙": ["股票", "基金", "虛擬貨幣", "高回報"],
    "網購騙案": ["網上購物", "二手交易", "轉賬"],
    "愛情詐騙": ["交友", "感情", "借錢", "網戀"],
    "求職騙案": ["招聘", "兼職", "工作", "面試"],
    "電話騙案": ["來電", "語音訊息", "回撥"],
    "釣魚短訊": ["短訊", "連結", "點擊", "驗證"],
    "虛假投資": ["投資應用", "交易平台", "出金"],
    "刷單騙案": ["刷單", "兼職", "佣金", "任務"]
}


class GeminiRAGHelper:
    """
    Gemini RAG 輔助類（最終簡化版）
    使用距離閾值過濾，不進行相似度轉換
    """
    
    def __init__(self, n_results: int = 5, max_distance: float = 10.0):
        """
        初始化 RAG 輔助類
        
        Args:
            n_results: 每次檢索返回的結果數量（默認 5）
            max_distance: 最大距離閾值（默認 10.0，基於數據分析）
        """
        self.n_results = n_results
        self.max_distance = max_distance
        self._cache = {}
        log.info(f"[RAG_HELPER] 初始化 - 檢索 {n_results} 個結果，最大距離 {max_distance}")
    
    def get_relevant_cases(self, query: str) -> str:
        """
        根據查詢檢索相關案例
        
        Args:
            query: 查詢文本
        
        Returns:
            str: 格式化的相關案例文本
        """
        # 檢查緩存
        if query in self._cache:
            log.info(f"[RAG_HELPER] 使用緩存結果")
            return self._cache[query]
        
        try:
            results = query_db(query, n_results=self.n_results)
            
            if not results or not results['documents']:
                log.warning(f"[RAG_HELPER] 未找到相關案例")
                return "（未找到相關案例）"
            
            # 格式化結果並過濾距離太遠的
            formatted_cases = []
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i]
                
                # 過濾距離太遠的結果
                if distance > self.max_distance:
                    log.debug(f"[RAG_HELPER] 過濾距離過遠的結果: {distance:.2f}")
                    continue
                
                metadata = results['metadatas'][0][i]
                
                case_text = f"""
案例 {len(formatted_cases) + 1}:
標題: {metadata.get('title', 'N/A')}
日期: {metadata.get('date', 'N/A')}
內容: {doc[:250]}...
"""
                formatted_cases.append(case_text.strip())
            
            if not formatted_cases:
                log.warning(f"[RAG_HELPER] 所有結果距離過遠（> {self.max_distance}）")
                return "（未找到足夠相關的案例）"
            
            # 只返回 top-3
            result_text = "\n\n".join(formatted_cases[:3])
            log.info(f"[RAG_HELPER] 檢索到 {len(formatted_cases)} 個相關案例（返回 top-3）")
            
            # 存入緩存
            self._cache[query] = result_text
            
            return result_text
            
        except Exception as e:
            log.error(f"[RAG_HELPER] 檢索失敗: {e}")
            return "（檢索失敗）"
    
    def get_scam_type_cases(self, scam_type: str, context: str = "") -> str:
        """
        根據騙案類型檢索相關案例
        
        Args:
            scam_type: 騙案類型
            context: 額外上下文（可選）
        
        Returns:
            str: 格式化的相關案例文本
        """
        # 構建查詢
        query_parts = [scam_type]
        
        # 添加同義詞
        if scam_type in SCAM_TYPE_SYNONYMS:
            synonyms = SCAM_TYPE_SYNONYMS[scam_type][:2]
            query_parts.extend(synonyms)
        
        # 添加上下文
        if context:
            query_parts.append(context[:50])
        
        query = " ".join(query_parts)
        log.info(f"[RAG_HELPER] 查詢: {query}")
        
        return self.get_relevant_cases(query)
    
    def format_for_prompt(self, scam_type: str, context: str = "") -> str:
        """
        為 prompt 格式化相關案例
        
        Args:
            scam_type: 騙案類型
            context: 額外上下文
        
        Returns:
            str: 可直接插入 prompt 的文本
        """
        cases = self.get_scam_type_cases(scam_type, context)
        
        if "未找到" in cases or "失敗" in cases:
            formatted = f"""
## 騙案類型參考

類型: {scam_type}

請根據此類型的常見手法進行對話。
"""
        else:
            formatted = f"""
## 相關真實案例（RAG 檢索）

{cases}

請參考以上真實案例，使用類似的手法和話術。
"""
        return formatted
    
    def clear_cache(self):
        """清空緩存"""
        self._cache.clear()
        log.info("[RAG_HELPER] 緩存已清空")


def initialize_rag_db():
    """初始化 RAG 數據庫"""
    print("=" * 60)
    print("初始化 RAG 數據庫")
    print("=" * 60)
    
    try:
        build_and_persist_db()
        print("\n[SUCCESS] RAG 數據庫初始化完成！")
        return True
    except Exception as e:
        print(f"\n[ERROR] 初始化失敗: {e}")
        return False


def test_rag_retrieval():
    """測試 RAG 檢索功能"""
    print("\n" + "=" * 60)
    print("測試 RAG 檢索（最終版）")
    print("=" * 60)
    
    helper = GeminiRAGHelper(n_results=5, max_distance=10.0)
    
    test_cases = [
        ("假冒銀行", "貸款"),
        ("投資詐騙", "高回報"),
        ("網購騙案", ""),
        ("愛情詐騙", "")
    ]
    
    for scam_type, context in test_cases:
        print(f"\n{'='*60}")
        print(f"測試: {scam_type}" + (f" (上下文: {context})" if context else ""))
        print('='*60)
        result = helper.format_for_prompt(scam_type, context)
        print(result)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG 整合工具（最終版）")
    parser.add_argument("--init", action="store_true", help="初始化 RAG 數據庫")
    parser.add_argument("--test", action="store_true", help="測試 RAG 檢索")
    
    args = parser.parse_args()
    
    if args.init:
        initialize_rag_db()
    elif args.test:
        test_rag_retrieval()
    else:
        print("使用方法:")
        print("  初始化: python rag_integration.py --init")
        print("  測試:   python rag_integration.py --test")
