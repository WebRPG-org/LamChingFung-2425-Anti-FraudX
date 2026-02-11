"""
測試 Gemini File API 整合
驗證文件上傳、System Instructions 和 LLM Factory 整合
"""

import os
import sys
import asyncio
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


async def test_file_upload():
    """測試文件上傳"""
    print("\n" + "=" * 60)
    print("Test 1: File Upload")
    print("=" * 60)
    
    from llms.gemini_file_manager import GeminiFileManager
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY not set")
        return False
    
    try:
        manager = GeminiFileManager(api_key)
        
        # 列出現有文件
        print("\n[1] Listing existing files...")
        existing = manager.list_files()
        print(f"Found {len(existing)} files")
        
        # 上傳知識庫
        print("\n[2] Uploading knowledge base...")
        base_dir = backend_dir.parent
        uploaded = manager.upload_knowledge_base(str(base_dir))
        
        if not uploaded:
            print("[FAIL] No files uploaded")
            return False
        
        print(f"[OK] Uploaded {len(uploaded)} files:")
        for name, file in uploaded.items():
            print(f"  - {name}: {file.uri}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_system_instructions():
    """測試 System Instructions"""
    print("\n" + "=" * 60)
    print("Test 2: System Instructions")
    print("=" * 60)
    
    try:
        from agents.system_instructions import get_system_instruction
        
        agent_types = ["scammer", "victim", "expert", "recorder"]
        
        for agent_type in agent_types:
            instruction = get_system_instruction(agent_type)
            print(f"\n[{agent_type}]")
            print(f"  Length: {len(instruction)} chars")
            print(f"  Preview: {instruction[:100]}...")
        
        print("\n[OK] All System Instructions loaded")
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_factory():
    """測試 LLM Factory 整合"""
    print("\n" + "=" * 60)
    print("Test 3: LLM Factory Integration")
    print("=" * 60)
    
    try:
        from llms.llm_factory import LlmFactory
        from config import config
        
        # 啟用 Gemini
        config.gemini.GEMINI_ENABLED = True
        
        print("\n[1] Creating Gemini LLM for each agent type...")
        
        agent_types = ["scammer", "victim", "expert", "recorder"]
        
        for agent_type in agent_types:
            print(f"\n  Creating {agent_type} LLM...")
            llm = LlmFactory.create_llm(agent_type, use_gemini=True)
            
            print(f"    Model: {llm.model}")
            print(f"    System Instruction: {len(llm.system_instruction)} chars")
            print(f"    Uploaded Files: {len(llm.uploaded_files)}")
            
            for file in llm.uploaded_files:
                print(f"      - {file.display_name}")
        
        print("\n[OK] All LLMs created successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_generation():
    """測試生成功能"""
    print("\n" + "=" * 60)
    print("Test 4: Content Generation")
    print("=" * 60)
    
    try:
        from llms.llm_factory import LlmFactory
        from google.adk.models import LlmRequest
        from google.genai import types
        
        print("\n[1] Creating Expert LLM...")
        llm = LlmFactory.create_llm("expert", use_gemini=True)
        
        print("\n[2] Generating content...")
        
        # 構建請求
        test_prompt = "根據已上傳的知識庫，簡單介紹一下假冒銀行詐騙的特徵。"
        
        request = LlmRequest(
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=test_prompt)]
                )
            ]
        )
        
        # 生成內容
        response_text = ""
        async for response in llm.generate_content_async(request):
            if hasattr(response.content, 'parts'):
                for part in response.content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text
        
        print(f"\n[3] Response ({len(response_text)} chars):")
        print("-" * 60)
        print(response_text[:500])
        if len(response_text) > 500:
            print("...")
        print("-" * 60)
        
        print("\n[OK] Content generation successful")
        return True
        
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """運行所有測試"""
    
    print("=" * 60)
    print("Gemini File API Integration Test")
    print("=" * 60)
    
    # 檢查 API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] GEMINI_API_KEY not set")
        print("Please set GEMINI_API_KEY in your .env file")
        return 1
    
    print(f"\nAPI Key: {api_key[:10]}...{api_key[-5:]}")
    
    # 運行測試
    tests = [
        ("File Upload", test_file_upload),
        ("System Instructions", test_system_instructions),
        ("LLM Factory", test_llm_factory),
        ("Content Generation", test_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # 總結
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
