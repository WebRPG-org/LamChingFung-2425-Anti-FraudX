"""
診斷 Gemini API 地區和連接問題
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加 backend 到 path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 載入環境變量
env_path = backend_dir.parent / '.env'
if not env_path.exists():
    env_path = backend_dir / '.env'
load_dotenv(env_path)


def check_api_key():
    """檢查 API Key"""
    print("\n" + "=" * 60)
    print("1. Checking API Key")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY not set")
        return False
    
    print(f"[OK] API Key found: {api_key[:10]}...{api_key[-5:]}")
    return True


def check_region():
    """檢查地區支持"""
    print("\n" + "=" * 60)
    print("2. Checking Region Support")
    print("=" * 60)
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        
        print("[INFO] Attempting to list models...")
        
        # 嘗試列出模型（這個 API 通常不受地區限制）
        models = list(client.models.list())
        print(f"[OK] Found {len(models)} models")
        
        # 顯示可用模型
        print("\nAvailable models:")
        for model in models[:5]:  # 只顯示前 5 個
            print(f"  - {model.name}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"[FAIL] {error_msg}")
        
        if "location is not supported" in error_msg.lower():
            print("\n[ERROR] Your region is NOT supported for Gemini API")
            print("\nPossible solutions:")
            print("1. Use a VPN to connect from a supported region")
            print("2. Use a proxy server in a supported region")
            print("3. Wait for Google to expand Gemini API to your region")
            print("\nSupported regions (as of 2024):")
            print("  - United States")
            print("  - European Union countries")
            print("  - United Kingdom")
            print("  - Canada")
            print("  - Australia")
            print("  - Japan")
            print("  - South Korea")
            print("  - Singapore")
            print("  - And more...")
            print("\nNOT supported:")
            print("  - Mainland China")
            print("  - Hong Kong (sometimes restricted)")
            print("  - Some other regions")
        
        return False


def check_file_api():
    """檢查 File API"""
    print("\n" + "=" * 60)
    print("3. Checking File API")
    print("=" * 60)
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        
        print("[INFO] Attempting to list files...")
        
        # 嘗試列出文件
        files = list(client.files.list())
        print(f"[OK] Found {len(files)} uploaded files")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"[FAIL] {error_msg}")
        
        if "location is not supported" in error_msg.lower():
            print("\n[ERROR] File API is NOT available in your region")
            print("\nThis means you CANNOT use the File API (Long Context) feature.")
            print("\nAlternative approach:")
            print("1. Embed knowledge base directly in prompts (limited by token count)")
            print("2. Use RAG with local vector database")
            print("3. Use a VPN/proxy from a supported region")
        
        return False


def check_generation():
    """檢查生成功能"""
    print("\n" + "=" * 60)
    print("4. Checking Content Generation")
    print("=" * 60)
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        
        print("[INFO] Attempting to generate content...")
        
        # 嘗試生成內容（使用正確的模型名稱）
        response = client.models.generate_content(
            model="models/gemini-3-flash-preview",
            contents=types.Content(
                parts=[types.Part(text="Say 'Hello' in Chinese")]
            ),
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=100
            )
        )
        
        text = response.text
        print(f"[OK] Generation successful")
        print(f"Response: {text}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"[FAIL] {error_msg}")
        
        if "location is not supported" in error_msg.lower():
            print("\n[ERROR] Content generation is NOT available in your region")
        
        return False


def main():
    print("=" * 60)
    print("Gemini API Region & Connection Diagnostic")
    print("=" * 60)
    
    results = []
    
    # 檢查 API Key
    if not check_api_key():
        print("\n[ABORT] Cannot proceed without API Key")
        return 1
    
    # 檢查地區支持
    results.append(("Region Support", check_region()))
    
    # 檢查 File API
    results.append(("File API", check_file_api()))
    
    # 檢查生成功能
    results.append(("Content Generation", check_generation()))
    
    # 總結
    print("\n" + "=" * 60)
    print("Diagnostic Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == 0:
        print("\n[CRITICAL] Your region does NOT support Gemini API")
        print("\nRecommended actions:")
        print("1. Use a VPN to connect from a supported region (US, EU, etc.)")
        print("2. Or continue using Ollama (local models)")
        return 1
    elif passed < total:
        print("\n[WARNING] Some features are not available")
        print("You may need to use alternative approaches")
        return 0
    else:
        print("\n[SUCCESS] All checks passed! You can use Gemini API")
        return 0


if __name__ == "__main__":
    sys.exit(main())
