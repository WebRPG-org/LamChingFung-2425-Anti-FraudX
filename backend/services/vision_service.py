"""
視覺分析服務 - 直接使用 Ollama API
繞過 Google ADK，直接調用 Ollama 的視覺功能
"""

import ollama
from typing import List, Optional
from utils.logger import log


class VisionService:
    """
    視覺分析服務
    使用 Ollama 的原生視覺 API
    """
    
    def __init__(self, model: str = "gemma3:4b"):
        self.model = model
        log.info(f"🎨 VisionService 初始化 - 模型: {model}")
    
    async def analyze_with_vision(
        self,
        message: str,
        images: List[str],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        使用視覺功能分析圖片
        
        Args:
            message: 用戶消息
            images: base64 編碼的圖片列表
            system_prompt: 系統提示詞（可選）
        
        Returns:
            AI 回應
        """
        try:
            log.info(f"🔍 開始視覺分析 - 圖片數量: {len(images)}")
            log.info(f"📝 用戶消息: {message[:100]}...")
            log.info(f"📊 圖片大小: {[len(img) for img in images]} bytes (base64)")
            
            # 第一步：提取圖片文字（使用與測試腳本完全相同的方法）
            extraction_prompt = "請詳細描述這張圖片的內容。如果圖片中有文字，請識別出來。"
            
            log.info(f"📝 第一步：提取圖片文字")
            extraction_response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': extraction_prompt,
                    'images': images
                }]
            )
            
            extracted_text = extraction_response['message']['content']
            log.info(f"✅ 提取完成（長度: {len(extracted_text)}）：")
            log.info(f"{extracted_text}")
            
            # 驗證是否成功提取
            if len(extracted_text) < 20 or "請仔細閱讀" in extracted_text:
                log.error(f"❌ 階段 1 失敗：AI 沒有正確讀取圖片")
                log.error(f"   返回內容: {extracted_text[:200]}")
                return "抱歉，無法讀取圖片內容。請確保圖片清晰可讀。"
            
            # 第二步：詐騙分析（使用與測試腳本完全相同的提示詞）
            analysis_prompt = f"""根據以下圖片內容，判斷是否為詐騙：

{extracted_text}

請檢查以下特徵：
1. 是否有可疑的文字內容（如「立即」「緊急」「中獎」「轉帳」等）
2. 是否有可疑的連結或網址
3. 是否假冒官方機構或品牌
4. 是否要求提供個人資料或密碼
5. 是否製造緊急感或恐嚇

請用繁體中文廣東話回答，並給出：
- 風險等級（高/中/低）
- 詐騙特徵
- 建議措施"""
            
            log.info(f"📝 第二步：詐騙分析")
            analysis_response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': analysis_prompt
                }]
            )
            
            reply = analysis_response['message']['content']
            
            log.info(f"✅ 分析完成（長度: {len(reply)}）")
            log.info(f"📝 回應內容：")
            log.info(f"{reply}")
            
            return reply
            
        except Exception as e:
            log.error(f"❌ 視覺分析失敗: {e}")
            import traceback
            log.error(f"詳細錯誤: {traceback.format_exc()}")
            return f"抱歉，圖片分析失敗：{str(e)}"


# 全局實例
vision_service = VisionService()
