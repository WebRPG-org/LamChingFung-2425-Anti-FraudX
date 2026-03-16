"""
RAG 系統診斷工具
檢查數據庫狀態、Embedding 質量、檢索性能
"""

import os
import sys
import math
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.rag_service import query_db, DB_PATH, COLLECTION_NAME
import chromadb
from sentence_transformers import SentenceTransformer


def diagnose_database():
    """診斷數據庫狀態"""
    print("=" * 60)
    print("RAG 數據庫診斷")
    print("=" * 60)
    
    # 1. 檢查數據庫是否存在
    print("\n[1] 檢查數據庫文件...")
    if os.path.exists(DB_PATH):
        print(f"✅ 數據庫路徑存在: {DB_PATH}")
    else:
        print(f"❌ 數據庫路徑不存在: {DB_PATH}")
        return False
    
    # 2. 連接數據庫
    print("\n[2] 連接數據庫...")
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        print("✅ 數據庫連接成功")
    except Exception as e:
        print(f"❌ 數據庫連接失敗: {e}")
        return False
    
    # 3. 檢查集合
    print("\n[3] 檢查集合...")
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        count = collection.count()
        print(f"✅ 集合存在: {COLLECTION_NAME}")
        print(f"✅ 文檔數量: {count}")
    except Exception as e:
        print(f"❌ 集合不存在或無法訪問: {e}")
        return False
    
    # 4. 檢查 Embedding 模型
    print("\n[4] 檢查 Embedding 模型...")
    try:
        from services.rag_service import EMBEDDING_MODEL_NAME
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print(f"✅ 模型加載成功: {EMBEDDING_MODEL_NAME}")
        
        # 測試 embedding
        test_text = "這是一個測試"
        embedding = model.encode(test_text)
        print(f"✅ Embedding 維度: {len(embedding)}")
    except Exception as e:
        print(f"❌ 模型加載失敗: {e}")
        return False
    
    # 5. 測試檢索
    print("\n[5] 測試檢索功能...")
    test_queries = [
        "銀行",
        "投資",
        "詐騙",
        "假冒銀行職員"
    ]
    
    for query in test_queries:
        print(f"\n  查詢: '{query}'")
        try:
            results = query_db(query, n_results=3)
            
            if results and results['documents']:
                print(f"  ✅ 找到 {len(results['documents'][0])} 個結果")
                
                # 顯示距離分布
                distances = results['distances'][0]
                print(f"  距離範圍: {min(distances):.2f} - {max(distances):.2f}")
                
                # 轉換為相似度
                similarities = [math.exp(-abs(d)) for d in distances]
                print(f"  相似度範圍: {min(similarities):.4f} - {max(similarities):.4f}")
                
                # 顯示第一個結果
                print(f"  第一個結果:")
                print(f"    標題: {results['metadatas'][0][0].get('title', 'N/A')[:50]}...")
                print(f"    內容: {results['documents'][0][0][:100]}...")
            else:
                print(f"  ❌ 未找到結果")
        except Exception as e:
            print(f"  ❌ 檢索失敗: {e}")
    
    print("\n" + "=" * 60)
    print("診斷完成")
    print("=" * 60)
    
    return True


def analyze_distance_distribution():
    """分析距離分布，找出合適的閾值"""
    print("\n" + "=" * 60)
    print("距離分布分析")
    print("=" * 60)
    
    test_queries = [
        ("假冒銀行", "銀行職員 貸款"),
        ("投資詐騙", "股票 高回報"),
        ("網購騙案", "二手交易"),
        ("愛情詐騙", "交友 借錢")
    ]
    
    all_distances = []
    
    for scam_type, keywords in test_queries:
        query = f"{scam_type} {keywords}"
        print(f"\n查詢: {query}")
        
        try:
            results = query_db(query, n_results=10)
            
            if results and results['distances']:
                distances = results['distances'][0]
                all_distances.extend(distances)
                
                print(f"  距離: {[f'{d:.2f}' for d in distances[:5]]}")
                print(f"  相似度: {[f'{math.exp(-abs(d)):.4f}' for d in distances[:5]]}")
        except Exception as e:
            print(f"  錯誤: {e}")
    
    if all_distances:
        print("\n" + "=" * 60)
        print("統計摘要")
        print("=" * 60)
        print(f"總樣本數: {len(all_distances)}")
        print(f"最小距離: {min(all_distances):.2f}")
        print(f"最大距離: {max(all_distances):.2f}")
        print(f"平均距離: {sum(all_distances)/len(all_distances):.2f}")
        
        # 計算百分位數
        sorted_distances = sorted(all_distances)
        p25 = sorted_distances[len(sorted_distances)//4]
        p50 = sorted_distances[len(sorted_distances)//2]
        p75 = sorted_distances[len(sorted_distances)*3//4]
        
        print(f"\n百分位數:")
        print(f"  25%: {p25:.2f} (相似度: {math.exp(-abs(p25)):.4f})")
        print(f"  50%: {p50:.2f} (相似度: {math.exp(-abs(p50)):.4f})")
        print(f"  75%: {p75:.2f} (相似度: {math.exp(-abs(p75)):.4f})")
        
        print(f"\n建議閾值:")
        print(f"  寬鬆 (top 75%): 距離 < {p75:.2f}, 相似度 > {math.exp(-abs(p75)):.4f}")
        print(f"  中等 (top 50%): 距離 < {p50:.2f}, 相似度 > {math.exp(-abs(p50)):.4f}")
        print(f"  嚴格 (top 25%): 距離 < {p25:.2f}, 相似度 > {math.exp(-abs(p25)):.4f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG 系統診斷工具")
    parser.add_argument("--diagnose", action="store_true", help="運行完整診斷")
    parser.add_argument("--analyze", action="store_true", help="分析距離分布")
    
    args = parser.parse_args()
    
    if args.diagnose:
        diagnose_database()
    elif args.analyze:
        analyze_distance_distribution()
    else:
        print("使用方法:")
        print("  完整診斷:     python rag_diagnostics.py --diagnose")
        print("  距離分析:     python rag_diagnostics.py --analyze")
