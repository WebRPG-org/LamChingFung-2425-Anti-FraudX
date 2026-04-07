"""
RAG 詐騙數據集成系統
集成生成式數據 + ADCC爬蟲數據
優化token用量，保持高度多樣性，隱藏受害者信息
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np
from collections import defaultdict

from fraud_feature_extractor import (
    FraudFeatureExtractor, VariationManager, PrivacyProtector, FraudFeature
)


class RAGFraudDatabase:
    """RAG詐騙數據庫 - 管理所有騙術特徵"""
    
    def __init__(self, db_path: str = "fraud_rag_db.json"):
        self.db_path = db_path
        self.features: Dict[str, List[Dict]] = defaultdict(list)
        self.embeddings: Dict[str, np.ndarray] = {}
        self.variation_manager = VariationManager()
        self.privacy_protector = PrivacyProtector()
        self.extractor = FraudFeatureExtractor()
        self.stats = {
            "total_features": 0,
            "by_scam_type": defaultdict(int),
            "by_source": defaultdict(int),
            "token_saved": 0
        }
    
    async def initialize_from_files(self, generator_path: str, adcc_path: str) -> bool:
        """從文件初始化數據庫"""
        try:
            print("🔄 正在初始化RAG詐騙數據庫...")
            
            # 讀取文件
            print(f"📖 讀取生成式數據: {generator_path}")
            with open(generator_path, 'r', encoding='utf-8') as f:
                generator_data = f.read()
            
            print(f"📖 讀取ADCC爬蟲數據: {adcc_path}")
            with open(adcc_path, 'r', encoding='utf-8') as f:
                adcc_data = f.read()
            
            # 提取特徵
            print("🔍 提取生成式數據特徵...")
            generator_features = self.extractor.extract_from_generator(generator_data)
            
            print("🔍 提取ADCC爬蟲數據特徵...")
            adcc_features = self.extractor.extract_from_adcc(adcc_data)
            
            # 合併特徵
            print("🔀 合併特徵...")
            merged_features = self.extractor.merge_features(generator_features, adcc_features)
            
            # 優化特徵
            print("⚡ 優化特徵（減少token用量）...")
            optimized_features = self.extractor.optimize_features(merged_features, max_per_type=100)
            
            # 導出為RAG格式
            print("📤 導出為RAG格式...")
            rag_data = self.extractor.export_to_rag_format(optimized_features)
            
            # 存儲到數據庫
            for entry in rag_data:
                scam_type = entry['scam_type']
                self.features[scam_type].append(entry)
                self.stats['total_features'] += 1
                self.stats['by_scam_type'][scam_type] += 1
                self.stats['by_source'][entry['source']] += 1
            
            print(f"✅ 初始化完成！")
            self._print_stats()
            
            return True
        
        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            return False
    
    async def search_similar_cases(self, query: str, scam_type: Optional[str] = None, 
                                   top_k: int = 5) -> List[Dict]:
        """搜索相似案例"""
        try:
            results = []
            
            # 確定搜索範圍
            search_types = [scam_type] if scam_type else list(self.features.keys())
            
            for stype in search_types:
                if stype not in self.features:
                    continue
                
                # 簡單的文本相似度匹配
                for feature in self.features[stype]:
                    similarity = self._calculate_text_similarity(query, feature['pattern'])
                    
                    if similarity > 0.3:  # 相似度閾值
                        results.append({
                            **feature,
                            'similarity_score': similarity
                        })
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return results[:top_k]
        
        except Exception as e:
            print(f"❌ 搜索失敗: {e}")
            return []
    
    async def get_random_case(self, scam_type: str, variation_id: int = 0) -> Optional[Dict]:
        """獲取隨機案例（帶變體）"""
        try:
            if scam_type not in self.features:
                return None
            
            features = self.features[scam_type]
            if not features:
                return None
            
            # 隨機選擇特徵
            import random
            feature = random.choice(features)
            
            # 生成變體
            variation = self.variation_manager.generate_variation(
                FraudFeature(**feature),
                variation_id
            )
            
            return {
                **feature,
                'variation': variation,
                'variation_id': variation_id
            }
        
        except Exception as e:
            print(f"❌ 獲取案例失敗: {e}")
            return None
    
    async def get_diverse_cases(self, scam_type: str, count: int = 5) -> List[Dict]:
        """獲取多個高度多樣化的案例"""
        try:
            if scam_type not in self.features:
                return []
            
            features = self.features[scam_type]
            if not features:
                return []
            
            # 按多樣性分數排序
            sorted_features = sorted(features, 
                                    key=lambda f: f['diversity_score'], 
                                    reverse=True)
            
            # 選擇前count個
            selected = sorted_features[:count]
            
            # 為每個特徵生成變體
            results = []
            for idx, feature in enumerate(selected):
                variations = self.variation_manager.ensure_diversity(
                    FraudFeature(**feature),
                    count=3  # 每個特徵生成3個變體
                )
                
                results.append({
                    **feature,
                    'variations': variations,
                    'variation_count': len(variations)
                })
            
            return results
        
        except Exception as e:
            print(f"❌ 獲取多樣化案例失敗: {e}")
            return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """計算文本相似度（簡單版本）"""
        # 分詞
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _print_stats(self):
        """打印統計信息"""
        print("\n📊 數據庫統計：")
        print(f"  總特徵數: {self.stats['total_features']}")
        print(f"  按騙案類型:")
        for stype, count in sorted(self.stats['by_scam_type'].items()):
            print(f"    - {stype}: {count}")
        print(f"  按數據源:")
        for source, count in self.stats['by_source'].items():
            print(f"    - {source}: {count}")
    
    async def save_to_disk(self, output_path: str) -> bool:
        """保存數據庫到磁盤"""
        try:
            data = {
                'features': dict(self.features),
                'stats': dict(self.stats),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 數據庫已保存: {output_path}")
            return True
        
        except Exception as e:
            print(f"❌ 保存失敗: {e}")
            return False
    
    async def load_from_disk(self, input_path: str) -> bool:
        """從磁盤加載數據庫"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.features = defaultdict(list, data.get('features', {}))
            self.stats = data.get('stats', {})
            
            print(f"✅ 數據庫已加載: {input_path}")
            return True
        
        except Exception as e:
            print(f"❌ 加載失敗: {e}")
            return False


class RAGQueryEngine:
    """RAG查詢引擎 - 為AI提供上下文"""
    
    def __init__(self, db: RAGFraudDatabase):
        self.db = db
        self.privacy_protector = PrivacyProtector()
    
    async def get_context_for_scammer(self, scam_type: str, 
                                      context_type: str = "full") -> Dict[str, Any]:
        """為騙徒AI獲取上下文"""
        try:
            context = {
                'scam_type': scam_type,
                'timestamp': datetime.now().isoformat(),
                'cases': [],
                'patterns': [],
                'variations': []
            }
            
            if context_type in ["full", "cases"]:
                # 獲取多個多樣化案例
                cases = await self.db.get_diverse_cases(scam_type, count=3)
                context['cases'] = cases
            
            if context_type in ["full", "patterns"]:
                # 獲取騙術模式
                if scam_type in self.db.features:
                    patterns = self.db.features[scam_type][:10]
                    context['patterns'] = [p['pattern'] for p in patterns]
            
            if context_type in ["full", "variations"]:
                # 獲取變體示例
                if scam_type in self.db.features:
                    feature = self.db.features[scam_type][0]
                    variations = self.privacy_protector.mask_sensitive_data(
                        feature['pattern']
                    )
                    context['variations'] = [variations]
            
            return context
        
        except Exception as e:
            print(f"❌ 獲取上下文失敗: {e}")
            return {}
    
    async def get_context_for_expert(self, scam_type: str) -> Dict[str, Any]:
        """為防騙專家AI獲取上下文"""
        try:
            context = {
                'scam_type': scam_type,
                'timestamp': datetime.now().isoformat(),
                'warning_signs': [],
                'prevention_tips': [],
                'real_cases': []
            }
            
            # 獲取真實案例（來自ADCC）
            if scam_type in self.db.features:
                adcc_cases = [f for f in self.db.features[scam_type] 
                             if f['source'] == 'adcc']
                context['real_cases'] = adcc_cases[:5]
            
            # 提取警告信號
            context['warning_signs'] = self._extract_warning_signs(scam_type)
            
            # 提取防騙建議
            context['prevention_tips'] = self._extract_prevention_tips(scam_type)
            
            return context
        
        except Exception as e:
            print(f"❌ 獲取專家上下文失敗: {e}")
            return {}
    
    def _extract_warning_signs(self, scam_type: str) -> List[str]:
        """提取警告信號"""
        warning_signs = {
            "網上購物騙案": [
                "要求提供完整銀行帳戶資料",
                "超低價格",
                "釣魚連結",
                "要求轉數快或匯款"
            ],
            "電話騙案": [
                "聲稱是執法人員",
                "威脅即刻拘捕",
                "要求提供密碼或OTP",
                "要求轉賬到安全帳戶"
            ],
            "求職騙案": [
                "高人工但無經驗要求",
                "要求先交培訓費",
                "在家工作",
                "淨係WhatsApp聯絡"
            ],
            "投資騙案": [
                "保證回報",
                "零風險",
                "內幕消息",
                "限時優惠"
            ],
            "網上情緣": [
                "未見過面就講愛",
                "不斷要求借錢",
                "各種藉口要錢",
                "拒絕見面或視訊"
            ]
        }
        
        return warning_signs.get(scam_type, [])
    
    def _extract_prevention_tips(self, scam_type: str) -> List[str]:
        """提取防騙建議"""
        prevention_tips = {
            "網上購物騙案": [
                "登入官方網站查看訂單",
                "唔好點擊短訊連結",
                "面交驗貨",
                "保留所有記錄"
            ],
            "電話騙案": [
                "掛線後自己打去官方熱線查證",
                "警察唔會要求提供銀行資料",
                "撥打防騙易18222查詢",
                "唔好俾任何密碼"
            ],
            "求職騙案": [
                "正規公司唔會要求先交錢",
                "去公司辦公室見工",
                "簽正式合約",
                "查公司背景"
            ],
            "投資騙案": [
                "查證公司係咪持有證監會牌照",
                "去證監會網站查持牌人名單",
                "唔好相信內幕消息",
                "真正好嘅投資唔會逼你即刻決定"
            ],
            "網上情緣": [
                "用Google圖片搜尋對方相片",
                "未見過面唔好俾錢",
                "真正愛你嘅人唔會不斷要錢",
                "即刻停止聯絡"
            ]
        }
        
        return prevention_tips.get(scam_type, [])


class TokenOptimizer:
    """Token優化器 - 減少不必要的重複"""
    
    @staticmethod
    def compress_features(features: List[Dict]) -> List[Dict]:
        """壓縮特徵 - 移除重複信息"""
        compressed = []
        seen_patterns = set()
        
        for feature in features:
            pattern = feature['pattern']
            
            # 檢查是否已經見過相似的模式
            if pattern not in seen_patterns:
                compressed.append(feature)
                seen_patterns.add(pattern)
        
        return compressed
    
    @staticmethod
    def calculate_token_savings(original_count: int, compressed_count: int) -> float:
        """計算token節省百分比"""
        if original_count == 0:
            return 0.0
        
        return ((original_count - compressed_count) / original_count) * 100


# 使用示例
async def main():
    """主程序"""
    
    # 初始化數據庫
    db = RAGFraudDatabase()
    
    generator_path = r"c:\Users\andy1\Desktop\scammer_file\massive_generator.py"
    adcc_path = r"c:\Users\andy1\Desktop\scammer_file\scraped_alerts.json"
    
    # 初始化
    success = await db.initialize_from_files(generator_path, adcc_path)
    
    if success:
        # 保存數據庫
        await db.save_to_disk("fraud_rag_database.json")
        
        # 創建查詢引擎
        query_engine = RAGQueryEngine(db)
        
        # 測試查詢
        print("\n🧪 測試查詢...")
        
        # 為騙徒獲取上下文
        scammer_context = await query_engine.get_context_for_scammer("網上購物騙案")
        print(f"\n騙徒上下文: {json.dumps(scammer_context, ensure_ascii=False, indent=2)[:500]}...")
        
        # 為專家獲取上下文
        expert_context = await query_engine.get_context_for_expert("網上購物騙案")
        print(f"\n專家上下文: {json.dumps(expert_context, ensure_ascii=False, indent=2)[:500]}...")


if __name__ == "__main__":
    asyncio.run(main())


