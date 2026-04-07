"""
Firestore RAG 詐騙數據集成系統
將生成式數據和ADCC爬蟲數據存儲到Firestore
用於LLM prompt的上下文注入
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

try:
    from services.firestore_service import FirestoreService
except ImportError:
    FirestoreService = None

try:
    from utils.logger import log
except ImportError:
    import logging
    log = logging.getLogger(__name__)


class FirestoreRAGDataLoader:
    """Firestore RAG 數據加載器 - 將數據上傳到Firestore"""
    
    def __init__(self):
        self.firestore_service = FirestoreService() if FirestoreService else None
        self.db = self.firestore_service.get_db() if self.firestore_service else None
    
    async def load_generator_data(self, generator_path: str) -> int:
        """
        從massive_generator.py加載數據到Firestore
        
        Args:
            generator_path: 生成器文件路徑
        
        Returns:
            int: 加載的特徵數量
        """
        try:
            log.info("🔄 開始加載生成式數據到Firestore...")
            
            # 讀取生成器文件
            with open(generator_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取模板
            templates = self._extract_templates_from_generator(content)
            
            # 上傳到Firestore
            count = 0
            for scam_type, template_list in templates.items():
                for idx, template in enumerate(template_list):
                    doc_data = {
                        'scam_type': scam_type,
                        'source': 'generator',
                        'template_id': idx,
                        'opening': template.get('opening', ''),
                        'hook': template.get('hook', ''),
                        'request': template.get('request', ''),
                        'urgency': template.get('urgency', ''),
                        'created_at': datetime.now(),
                        'type': 'scammer_template'
                    }
                    
                    self.db.collection('rag_features').add(doc_data)
                    count += 1
            
            log.info(f"✅ 生成式數據加載完成: {count} 個特徵")
            return count
        
        except Exception as e:
            log.error(f"❌ 加載生成式數據失敗: {e}")
            return 0
    
    async def load_adcc_data(self, adcc_path: str) -> int:
        """
        從scraped_alerts.json加載真實案例到Firestore
        
        Args:
            adcc_path: ADCC數據文件路徑
        
        Returns:
            int: 加載的案例數量
        """
        try:
            log.info("🔄 開始加載ADCC真實案例到Firestore...")
            
            # 讀取ADCC數據
            with open(adcc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            count = 0
            for line_idx, line in enumerate(lines):
                if not line.strip():
                    continue
                
                try:
                    case = json.loads(line)
                except:
                    case = {'description': line.strip()}
                
                # 提取騙案類型
                scam_type = case.get('scam_type') or case.get('type') or '其他騙案'
                
                doc_data = {
                    'scam_type': scam_type,
                    'source': 'adcc',
                    'case_id': line_idx,
                    'description': case.get('description', ''),
                    'method': case.get('method', ''),
                    'content': case.get('content', ''),
                    'created_at': datetime.now(),
                    'type': 'real_case'
                }
                
                self.db.collection('rag_features').add(doc_data)
                count += 1
            
            log.info(f"✅ ADCC數據加載完成: {count} 個案例")
            return count
        
        except Exception as e:
            log.error(f"❌ 加載ADCC數據失敗: {e}")
            return 0
    
    def _extract_templates_from_generator(self, content: str) -> Dict[str, List[Dict]]:
        """從生成器代碼中提取模板"""
        templates = {}
        
        # 簡單的模板提取邏輯
        scam_types = [
            "網上購物騙案", "電話騙案", "求職騙案", "投資騙案",
            "網上情緣", "財務中介公司騙案", "裸聊騙案",
            "社交媒體騙案", "街頭騙案", "電郵騙案", "其他騙案"
        ]
        
        for scam_type in scam_types:
            templates[scam_type] = [
                {
                    'opening': f'你好，我係{scam_type}',
                    'hook': '有重要事項',
                    'request': '需要你配合',
                    'urgency': '請盡快處理'
                }
            ]
        
        return templates


class FirestoreRAGContextProvider:
    """Firestore RAG 上下文提供器 - 為LLM提供上下文"""
    
    def __init__(self):
        self.firestore_service = FirestoreService() if FirestoreService else None
        self.db = self.firestore_service.get_db() if self.firestore_service else None
    
    async def check_data_exists(self) -> bool:
        """
        檢查 Firestore 中是否已有 RAG 數據
        
        Returns:
            bool: 若已有數據返回 True，否則返回 False
        """
        try:
            if not self.db:
                return False
            docs = self.db.collection('rag_features').limit(1).stream()
            return any(True for _ in docs)
        except Exception as e:
            log.error(f"❌ 檢查 RAG 數據失敗: {e}")
            return False

    async def get_scammer_context(self, scam_type: str, max_items: int = 3) -> str:
        """
        為騙徒AI獲取上下文（用於prompt注入）
        
        Args:
            scam_type: 騙案類型
            max_items: 最多返回項數
        
        Returns:
            str: 格式化的上下文字符串
        """
        try:
            # 從Firestore查詢生成式數據
            docs = self.db.collection('rag_features') \
                .where('scam_type', '==', scam_type) \
                .where('source', '==', 'generator') \
                .limit(max_items) \
                .stream()
            
            context_items = []
            for doc in docs:
                data = doc.to_dict()
                context_items.append({
                    'opening': data.get('opening', ''),
                    'hook': data.get('hook', ''),
                    'request': data.get('request', ''),
                    'urgency': data.get('urgency', '')
                })
            
            # 格式化為prompt
            if not context_items:
                return ""
            
            prompt = f"""
【{scam_type}騙術參考】
你可以參考以下騙術模式，但要變化很大，每次都要不同：

"""
            for idx, item in enumerate(context_items, 1):
                prompt += f"""
案例{idx}:
- 開場: {item['opening']}
- 誘餌: {item['hook']}
- 要求: {item['request']}
- 緊迫感: {item['urgency']}
"""
            
            return prompt
        
        except Exception as e:
            log.error(f"❌ 獲取騙徒上下文失敗: {e}")
            return ""
    
    async def get_expert_context(self, scam_type: str, max_items: int = 3) -> str:
        """
        為防騙專家AI獲取上下文（用於prompt注入）
        
        Args:
            scam_type: 騙案類型
            max_items: 最多返回項數
        
        Returns:
            str: 格式化的上下文字符串
        """
        try:
            # 從Firestore查詢真實案例
            docs = self.db.collection('rag_features') \
                .where('scam_type', '==', scam_type) \
                .where('source', '==', 'adcc') \
                .limit(max_items) \
                .stream()
            
            real_cases = []
            for doc in docs:
                data = doc.to_dict()
                real_cases.append({
                    'description': data.get('description', ''),
                    'method': data.get('method', ''),
                    'content': data.get('content', '')
                })
            
            # 格式化為prompt
            if not real_cases:
                return ""
            
            prompt = f"""
【{scam_type}真實案例參考】
根據以下真實案例提供防騙建議：

"""
            for idx, case in enumerate(real_cases, 1):
                prompt += f"""
真實案例{idx}:
{case['description']}
"""
            
            return prompt
        
        except Exception as e:
            log.error(f"❌ 獲取專家上下文失敗: {e}")
            return ""
    
    async def get_warning_signs(self, scam_type: str) -> List[str]:
        """
        獲取警告信號列表
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            list: 警告信號列表
        """
        warning_signs_map = {
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
        
        return warning_signs_map.get(scam_type, [])
    
    async def get_prevention_tips(self, scam_type: str) -> List[str]:
        """
        獲取防騙建議列表
        
        Args:
            scam_type: 騙案類型
        
        Returns:
            list: 防騙建議列表
        """
        prevention_tips_map = {
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
        
        return prevention_tips_map.get(scam_type, [])


class FirestoreRAGPromptBuilder:
    """Firestore RAG Prompt構建器 - 為LLM構建完整prompt"""
    
    def __init__(self):
        self.context_provider = FirestoreRAGContextProvider()
    
    async def build_scammer_prompt(self, scam_type: str, user_message: str = "") -> str:
        """
        為騙徒AI構建完整prompt
        
        Args:
            scam_type: 騙案類型
            user_message: 用戶消息（可選）
        
        Returns:
            str: 完整的prompt
        """
        # 獲取上下文
        context = await self.context_provider.get_scammer_context(scam_type)
        
        # 構建prompt
        prompt = f"""你是一個詐騙者，正在進行『{scam_type}』詐騙。

{context}

重要提醒：
- 每次回應都要變化很大，不能重複
- 使用港式廣東話
- 要製造緊迫感和信任感
- 逐步引導受害者提供信息或轉賬

"""
        
        if user_message:
            prompt += f"受害者說: {user_message}\n\n你的回應:"
        
        return prompt
    
    async def build_expert_prompt(self, scam_type: str, user_message: str = "") -> str:
        """
        為防騙專家AI構建完整prompt
        
        Args:
            scam_type: 騙案類型
            user_message: 用戶消息（可選）
        
        Returns:
            str: 完整的prompt
        """
        # 獲取上下文
        context = await self.context_provider.get_expert_context(scam_type)
        warning_signs = await self.context_provider.get_warning_signs(scam_type)
        prevention_tips = await self.context_provider.get_prevention_tips(scam_type)
        
        # 構建prompt
        prompt = f"""你是一個防騙專家，幫助市民識別和防範『{scam_type}』詐騙。

{context}

警告信號:
"""
        for sign in warning_signs:
            prompt += f"- {sign}\n"
        
        prompt += "\n防騙建議:\n"
        for tip in prevention_tips:
            prompt += f"- {tip}\n"
        
        prompt += "\n用港式廣東話回答，要清楚、實用、有說服力。\n"
        
        if user_message:
            prompt += f"用戶問: {user_message}\n\n你的回答:"
        
        return prompt
    
    async def build_victim_prompt(self, scam_type: str, user_message: str = "") -> str:
        """
        為受害者AI構建完整prompt
        
        Args:
            scam_type: 騙案類型
            user_message: 用戶消息（可選）
        
        Returns:
            str: 完整的prompt
        """
        warning_signs = await self.context_provider.get_warning_signs(scam_type)
        prevention_tips = await self.context_provider.get_prevention_tips(scam_type)
        
        # 構建prompt
        prompt = f"""你是一個容易受騙的受害者，正在遭遇『{scam_type}』詐騙。

你的特點:
- 容易相信他人
- 容易被緊迫感影響
- 不太懂技術
- 想幫助別人

警告信號（你可能沒注意到）:
"""
        for sign in warning_signs:
            prompt += f"- {sign}\n"
        
        prompt += "\n防騙建議（你應該知道但可能忽略了）:\n"
        for tip in prevention_tips:
            prompt += f"- {tip}\n"
        
        prompt += "\n用港式廣東話回應，表現出受害者的心理狀態。\n"
        
        if user_message:
            prompt += f"騙徒說: {user_message}\n\n你的反應:"
        
        return prompt


# 使用示例
async def main():
    """主程序"""
    
    print("=" * 70)
    print("Firestore RAG 詐騙數據集成系統")
    print("=" * 70)
    
    # 初始化加載器
    loader = FirestoreRAGDataLoader()
    
    # 加載數據
    print("\n📋 步驟1: 加載數據到Firestore...")
    generator_path = r"c:\Users\andy1\Desktop\scammer_file\massive_generator.py"
    adcc_path = r"c:\Users\andy1\Desktop\scammer_file\scraped_alerts.json"
    
    gen_count = await loader.load_generator_data(generator_path)
    adcc_count = await loader.load_adcc_data(adcc_path)
    
    print(f"✅ 加載完成: {gen_count} 個生成式特徵 + {adcc_count} 個真實案例")
    
    # 初始化Prompt構建器
    print("\n📋 步驟2: 構建LLM Prompt...")
    prompt_builder = FirestoreRAGPromptBuilder()
    
    # 為騙徒構建prompt
    scammer_prompt = await prompt_builder.build_scammer_prompt("網上購物騙案")
    print("\n騙徒Prompt示例:")
    print(scammer_prompt[:200] + "...")
    
    # 為專家構建prompt
    expert_prompt = await prompt_builder.build_expert_prompt("網上購物騙案")
    print("\n專家Prompt示例:")
    print(expert_prompt[:200] + "...")
    
    print("\n✅ 系統準備就緒！")


if __name__ == "__main__":
    asyncio.run(main())


