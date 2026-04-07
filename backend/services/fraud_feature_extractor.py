"""
詐騙特徵提取器 - 從生成式數據和爬蟲數據中提取騙術特徵
目標：減少token用量，提升多樣性，隱藏受害者信息
"""

import json
import re
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class FraudFeature:
    """騙術特徵"""
    feature_id: str
    scam_type: str
    category: str  # opening/hook/request/urgency
    pattern: str
    variations: List[str]
    token_count: int
    diversity_score: float
    source: str  # "generator" or "adcc"


class FraudFeatureExtractor:
    """從數據中提取騙術特徵"""
    
    def __init__(self):
        self.features: Dict[str, FraudFeature] = {}
        self.pattern_cache: Dict[str, Set[str]] = defaultdict(set)
        self.scam_types = [
            "網上購物騙案", "電話騙案", "求職騙案", "投資騙案",
            "網上情緣", "財務中介公司騙案", "裸聊騙案",
            "社交媒體騙案", "街頭騙案", "電郵騙案", "其他騙案"
        ]
    
    def extract_from_generator(self, generator_data: str) -> Dict[str, List[FraudFeature]]:
        """從生成式數據提取特徵"""
        features_by_type = defaultdict(list)
        
        # 解析生成器中的模板
        templates = self._parse_generator_templates(generator_data)
        
        for scam_type, template_list in templates.items():
            for idx, template in enumerate(template_list):
                # 提取4個關鍵階段的特徵
                for stage, content in template.items():
                    feature = self._create_feature(
                        scam_type=scam_type,
                        category=stage,
                        pattern=content,
                        source="generator",
                        feature_idx=idx
                    )
                    features_by_type[scam_type].append(feature)
        
        return features_by_type
    
    def extract_from_adcc(self, adcc_data: str) -> Dict[str, List[FraudFeature]]:
        """從ADCC爬蟲數據提取特徵"""
        features_by_type = defaultdict(list)
        
        try:
            lines = adcc_data.strip().split('\n')
            
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    continue
                
                try:
                    case = json.loads(line)
                except:
                    # 嘗試解析非JSON格式
                    case = self._parse_text_case(line)
                
                if not case:
                    continue
                
                scam_type = case.get('scam_type') or case.get('type') or '其他騙案'
                
                # 從案例中提取特徵
                for field in ['description', 'method', 'content', 'text']:
                    if field in case and case[field]:
                        feature = self._create_feature(
                            scam_type=scam_type,
                            category='method',
                            pattern=case[field],
                            source="adcc",
                            feature_idx=line_idx
                        )
                        features_by_type[scam_type].append(feature)
        
        except Exception as e:
            print(f"❌ ADCC解析錯誤: {e}")
        
        return features_by_type
    
    def _create_feature(self, scam_type: str, category: str, pattern: str, 
                       source: str, feature_idx: int) -> FraudFeature:
        """創建特徵對象"""
        
        # 生成特徵ID
        feature_hash = hashlib.md5(f"{scam_type}_{category}_{pattern}".encode()).hexdigest()[:8]
        feature_id = f"{source}_{scam_type}_{feature_idx}_{feature_hash}"
        
        # 提取變體
        variations = self._extract_variations(pattern)
        
        # 計算token數
        token_count = len(pattern) // 4  # 粗略估計
        
        # 計算多樣性分數
        diversity_score = self._calculate_diversity(variations)
        
        return FraudFeature(
            feature_id=feature_id,
            scam_type=scam_type,
            category=category,
            pattern=pattern,
            variations=variations,
            token_count=token_count,
            diversity_score=diversity_score,
            source=source
        )
    
    def _extract_variations(self, pattern: str) -> List[str]:
        """從模式中提取變體"""
        variations = []
        
        # 提取 {variable} 格式的變數
        variables = re.findall(r'\{(\w+)\}', pattern)
        variations.extend(variables)
        
        # 提取關鍵詞
        keywords = re.findall(r'[\u4e00-\u9fff]+', pattern)
        variations.extend(keywords[:5])  # 限制前5個
        
        return list(set(variations))
    
    def _calculate_diversity(self, variations: List[str]) -> float:
        """計算多樣性分數 (0-1)"""
        if not variations:
            return 0.0
        
        # 基於變體數量和唯一性
        unique_count = len(set(variations))
        total_count = len(variations)
        
        if total_count == 0:
            return 0.0
        
        return min(1.0, unique_count / total_count)
    
    def _parse_generator_templates(self, generator_code: str) -> Dict[str, List[Dict]]:
        """解析生成器代碼中的模板"""
        templates = defaultdict(list)
        
        # 提取 templates 字典
        match = re.search(r'templates = \{(.*?)\n        \}', generator_code, re.DOTALL)
        if not match:
            return templates
        
        templates_str = match.group(1)
        
        # 按騙案類型分組
        for scam_type in self.scam_types:
            pattern = f'"{scam_type}":\s*\[(.*?)\n            \]'
            match = re.search(pattern, templates_str, re.DOTALL)
            
            if match:
                template_list_str = match.group(1)
                # 簡單解析模板
                template_dicts = re.findall(r'\{(.*?)\}', template_list_str, re.DOTALL)
                
                for template_dict_str in template_dicts:
                    template = self._parse_template_dict(template_dict_str)
                    if template:
                        templates[scam_type].append(template)
        
        return templates
    
    def _parse_template_dict(self, dict_str: str) -> Dict[str, str]:
        """解析模板字典字符串"""
        template = {}
        
        # 提取 "key": "value" 對
        pairs = re.findall(r'"(\w+)":\s*"([^"]*)"', dict_str)
        
        for key, value in pairs:
            template[key] = value
        
        return template if template else None
    
    def _parse_text_case(self, line: str) -> Dict[str, Any]:
        """解析文本格式的案例"""
        case = {}
        
        # 嘗試提取常見字段
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 2:
                case['scam_type'] = parts[0].strip()
                case['description'] = parts[1].strip()
        elif '：' in line or ':' in line:
            parts = re.split(r'[：:]', line, 1)
            if len(parts) == 2:
                case['scam_type'] = parts[0].strip()
                case['description'] = parts[1].strip()
        else:
            case['description'] = line.strip()
        
        return case if case else None
    
    def merge_features(self, generator_features: Dict[str, List[FraudFeature]], 
                      adcc_features: Dict[str, List[FraudFeature]]) -> Dict[str, List[FraudFeature]]:
        """合併兩個數據源的特徵"""
        merged = defaultdict(list)
        
        # 添加生成器特徵
        for scam_type, features in generator_features.items():
            merged[scam_type].extend(features)
        
        # 添加ADCC特徵（去重）
        for scam_type, features in adcc_features.items():
            existing_patterns = {f.pattern for f in merged[scam_type]}
            
            for feature in features:
                if feature.pattern not in existing_patterns:
                    merged[scam_type].append(feature)
                    existing_patterns.add(feature.pattern)
        
        return merged
    
    def optimize_features(self, features: Dict[str, List[FraudFeature]], 
                         max_per_type: int = 100) -> Dict[str, List[FraudFeature]]:
        """優化特徵集合 - 減少token用量，保持多樣性"""
        optimized = {}
        
        for scam_type, feature_list in features.items():
            # 按多樣性分數排序
            sorted_features = sorted(feature_list, 
                                    key=lambda f: f.diversity_score, 
                                    reverse=True)
            
            # 選擇前max_per_type個
            selected = sorted_features[:max_per_type]
            
            # 進一步優化：確保不同category的均衡
            optimized[scam_type] = self._balance_categories(selected)
        
        return optimized
    
    def _balance_categories(self, features: List[FraudFeature]) -> List[FraudFeature]:
        """平衡不同category的特徵"""
        by_category = defaultdict(list)
        
        for feature in features:
            by_category[feature.category].append(feature)
        
        # 每個category最多保留25個
        balanced = []
        for category, cat_features in by_category.items():
            balanced.extend(cat_features[:25])
        
        return balanced
    
    def export_to_rag_format(self, features: Dict[str, List[FraudFeature]]) -> List[Dict]:
        """導出為RAG系統格式"""
        rag_data = []
        
        for scam_type, feature_list in features.items():
            for feature in feature_list:
                rag_entry = {
                    "id": feature.feature_id,
                    "scam_type": scam_type,
                    "category": feature.category,
                    "pattern": feature.pattern,
                    "variations": feature.variations,
                    "token_count": feature.token_count,
                    "diversity_score": feature.diversity_score,
                    "source": feature.source,
                    "embedding_ready": True
                }
                rag_data.append(rag_entry)
        
        return rag_data


class VariationManager:
    """管理特徵變體 - 確保每次都不同"""
    
    def __init__(self):
        self.variation_history: Dict[str, Set[str]] = defaultdict(set)
        self.variable_pools: Dict[str, List[str]] = self._init_variable_pools()
    
    def _init_variable_pools(self) -> Dict[str, List[str]]:
        """初始化變數池"""
        return {
            "platform": ["淘寶", "天貓", "京東", "拼多多", "Amazon", "蝦皮", "Carousell", "Yahoo拍賣", "eBay", "AliExpress"],
            "amount": ["$500", "$800", "$1000", "$1500", "$2000", "$3000", "$5000", "$8000", "$10000", "$15000", "$20000", "$30000", "$50000", "$100000"],
            "product": ["iPhone 15 Pro Max", "Samsung Galaxy S24", "Dyson風筒", "Nike波鞋", "Coach手袋", "Apple Watch", "iPad Pro", "MacBook Air"],
            "identity": ["香港警察", "內地公安", "廉政公署", "入境處", "海關", "稅務局", "銀行客服", "信用卡中心", "保險公司", "電訊公司"],
            "job": ["點讚員", "刷單員", "打字員", "數據輸入", "客服", "倉務員", "推廣員", "兼職文員", "網店助理", "社交媒體管理"],
            "location": ["美國", "英國", "澳洲", "加拿大", "台灣", "新加坡", "日本", "韓國", "法國", "德國"],
        }
    
    def generate_variation(self, feature: FraudFeature, variation_id: int) -> str:
        """生成特徵的變體"""
        pattern = feature.pattern
        
        # 替換變數
        for var_name, var_pool in self.variable_pools.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in pattern:
                # 使用variation_id確保確定性但多樣
                idx = (variation_id * 7 + hash(var_name)) % len(var_pool)
                pattern = pattern.replace(placeholder, var_pool[idx])
        
        return pattern
    
    def ensure_diversity(self, feature: FraudFeature, count: int) -> List[str]:
        """確保生成多個不同的變體"""
        variations = []
        
        for i in range(count):
            variation = self.generate_variation(feature, i)
            
            # 檢查是否已經生成過
            feature_key = f"{feature.feature_id}_{i}"
            if variation not in self.variation_history[feature_key]:
                variations.append(variation)
                self.variation_history[feature_key].add(variation)
        
        return variations


class PrivacyProtector:
    """隱私保護 - 確保受害者信息不可見"""
    
    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """遮蔽敏感信息"""
        # 遮蔽電話號碼
        text = re.sub(r'\d{4}\s\d{4}', '[PHONE]', text)
        
        # 遮蔽銀行帳戶
        text = re.sub(r'\d{4}-\d{4}-\d{3}', '[ACCOUNT]', text)
        
        # 遮蔽名字
        text = re.sub(r'(陳|李|張|黃|林|王)\w+', '[NAME]', text)
        
        # 遮蔽URL
        text = re.sub(r'https?://\S+', '[URL]', text)
        
        return text
    
    @staticmethod
    def is_victim_data(text: str) -> bool:
        """判斷是否包含受害者數據"""
        victim_indicators = [
            '受害者',
            '被害人',
            '報案',
            '損失',
            '金額',
            '個人資料',
            '身份證',
            '銀行帳戶'
        ]
        
        return any(indicator in text for indicator in victim_indicators)


