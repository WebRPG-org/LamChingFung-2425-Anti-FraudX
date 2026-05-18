"""直接測試 Ollama"""
import ollama

print("測試 Ollama 連接...")

try:
    # 測試 1: 列出模型
    models = ollama.list()
    print(f"\n✅ Ollama 連接成功")
    print(f"可用模型數量: {len(models.get('models', []))}")
    
    # 測試 2: 簡單對話
    print("\n測試 gemma4:e4b 模型...")
    response = ollama.chat(
        model='gemma4:e4b',
        messages=[{
            'role': 'user',
            'content': '你好，請簡單介紹你自己。'
        }]
    )
    
    print(f"\n✅ 模型回應:")
    print(response['message']['content'][:200])
    
except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
