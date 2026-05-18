"""
測試 Gemma 4 E4B 視覺功能
"""

import ollama
import base64
from pathlib import Path

def test_vision_with_text():
    """測試視覺功能 - 使用文字描述"""
    print("=" * 60)
    print("🧪 測試 1: 純文字對話（無圖片）")
    print("=" * 60)
    
    try:
        response = ollama.chat(
            model='gemma4:e4b',
            messages=[{
                'role': 'user',
                'content': '你好，請介紹一下你的能力。'
            }]
        )
        
        print(f"\n✅ 回應：\n{response['message']['content']}\n")
        return True
    except Exception as e:
        print(f"\n❌ 錯誤：{e}\n")
        return False


def test_vision_with_image(image_path: str = None):
    """測試視覺功能 - 使用圖片"""
    print("=" * 60)
    print("🧪 測試 2: 圖片分析（視覺功能）")
    print("=" * 60)
    
    if not image_path:
        print("\n⚠️ 未提供圖片路徑，跳過此測試")
        print("   使用方法：python test_vision.py <圖片路徑>")
        return False
    
    # 處理路徑（移除可能的引號）
    image_path = image_path.strip('"').strip("'")
    
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"\n❌ 圖片不存在：{image_path}")
        print(f"   完整路徑：{image_file.absolute()}")
        return False
    
    try:
        # 讀取圖片並轉換為 base64
        with open(image_file, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        print(f"\n📷 圖片：{image_file.name}")
        print(f"   大小：{len(image_data)} bytes (base64)")
        print(f"\n🤖 正在分析圖片...\n")
        
        # 使用視覺功能
        response = ollama.chat(
            model='gemma4:e4b',
            messages=[{
                'role': 'user',
                'content': '請詳細描述這張圖片的內容。如果圖片中有文字，請識別出來。',
                'images': [image_data]
            }]
        )
        
        print(f"✅ AI 分析結果：\n{response['message']['content']}\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤：{e}\n")
        return False


def test_scam_detection(image_path: str = None):
    """測試詐騙檢測功能"""
    print("=" * 60)
    print("🧪 測試 3: 詐騙檢測（實際應用）")
    print("=" * 60)
    
    if not image_path:
        print("\n⚠️ 未提供圖片路徑，跳過此測試")
        return False
    
    # 處理路徑（移除可能的引號）
    image_path = image_path.strip('"').strip("'")
    
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"\n❌ 圖片不存在：{image_path}")
        print(f"   完整路徑：{image_file.absolute()}")
        return False
    
    try:
        # 讀取圖片
        with open(image_file, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        print(f"\n📷 圖片：{image_file.name}")
        print(f"\n🤖 正在分析是否為詐騙...\n")
        
        # 詐騙檢測提示
        prompt = """請分析這張圖片，判斷是否為詐騙。

請檢查以下特徵：
1. 是否有可疑的文字內容（如「立即」「緊急」「中獎」「轉帳」等）
2. 是否有可疑的連結或網址
3. 是否假冒官方機構或品牌
4. 是否要求提供個人資料或密碼
5. 是否製造緊急感或恐嚇

請用繁體中文回答，並給出：
- 風險等級（高/中/低）
- 詐騙特徵
- 建議措施"""
        
        response = ollama.chat(
            model='gemma4:e4b',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [image_data]
            }]
        )
        
        print(f"✅ 詐騙分析結果：\n{response['message']['content']}\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤：{e}\n")
        return False


def main():
    """主函數"""
    import sys
    
    print("\n" + "=" * 60)
    print("🎯 Gemma 4 E4B 視覺功能測試")
    print("=" * 60 + "\n")
    
    # 檢查 Ollama 服務
    try:
        models_response = ollama.list()
        print("✅ Ollama 服務運行中")
        
        # 檢查模型是否存在
        models = models_response.get('models', [])
        model_names = [m.get('name', m.get('model', '')) for m in models]
        
        # 檢查 gemma4:e4b 是否存在（可能有不同的標籤）
        has_gemma4 = any('gemma4' in name and 'e4b' in name for name in model_names)
        
        if not has_gemma4:
            print("❌ gemma4:e4b 模型未安裝")
            print("   請運行：ollama pull gemma4:e4b")
            print(f"\n   已安裝的模型：{', '.join(model_names[:5])}")
            return
        
        print("✅ gemma4:e4b 模型已安裝\n")
        
    except Exception as e:
        print(f"❌ 無法連接到 Ollama 服務：{e}")
        print("   請確保 Ollama 正在運行：ollama serve")
        import traceback
        traceback.print_exc()
        return
    
    # 獲取圖片路徑
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 運行測試
    results = []
    
    # 測試 1: 純文字
    results.append(("純文字對話", test_vision_with_text()))
    
    # 測試 2: 圖片分析
    if image_path:
        results.append(("圖片分析", test_vision_with_image(image_path)))
        results.append(("詐騙檢測", test_scam_detection(image_path)))
    else:
        print("\n" + "=" * 60)
        print("💡 提示：提供圖片路徑以測試視覺功能")
        print("=" * 60)
        print("\n使用方法：")
        print("  python test_vision.py <圖片路徑>")
        print("\n範例：")
        print("  python test_vision.py screenshot.jpg")
        print("  python test_vision.py C:\\Users\\user\\Desktop\\scam.png")
        print("\n")
    
    # 顯示結果
    print("=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    print("\n" + "=" * 60)
    
    # 總結
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有測試通過！({passed}/{total})")
    else:
        print(f"⚠️ 部分測試失敗 ({passed}/{total})")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
