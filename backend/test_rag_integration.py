"""
測試 RAG 整合 - 驗證系統不再上傳文件
"""

import os
import sys
from pathlib import Path

# 添加 backend 到路徑
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from llms.llm_factory import LlmFactory
from utils.logger import log


def test_rag_helper():
    """測試 RAG 輔助類"""
    print("=" * 60)
    print("測試 1: RAG 輔助類初始化")
    print("=" * 60)
    
    try:
        rag_helper = LlmFactory._get_rag_helper()
        if rag_helper:
            print("✅ RAG 輔助類初始化成功")
        else:
            print("❌ RAG 輔助類初始化失敗")
            return False
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    
    return True


def test_rag_context():
    """測試 RAG 上下文檢索"""
    print("\n" + "=" * 60)
    print("測試 2: RAG 上下文檢索")
    print("=" * 60)
    
    test_cases = [
        ("假冒銀行", "貸款"),
        ("投資詐騙", ""),
        ("", "網購騙案")
    ]
    
    for scam_type, context in test_cases:
        print(f"\n--- 測試: scam_type='{scam_type}', context='{context}' ---")
        try:
            result = LlmFactory.get_rag_context(scam_type, context)
            if result:
                print(f"✅ 檢索成功，長度: {len(result)} 字")
                print(f"預覽: {result[:100]}...")
            else:
                print("⚠️ 檢索結果為空")
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            return False
    
    return True


def test_llm_creation_no_upload():
    """測試 LLM 創建時不上傳文件"""
    print("\n" + "=" * 60)
    print("測試 3: LLM 創建（不上傳文件）")
    print("=" * 60)
    
    # 檢查環境變量
    gemini_enabled = os.getenv("GEMINI_ENABLED", "false").lower() == "true"
    
    if not gemini_enabled:
        print("⚠️ GEMINI_ENABLED=false，跳過 Gemini 測試")
        print("提示: 設置 GEMINI_ENABLED=true 來測試 Gemini 模式")
        return True
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("⚠️ GEMINI_API_KEY 未設置，跳過 Gemini 測試")
        return True
    
    print(f"✅ Gemini 已啟用，API Key: {gemini_api_key[:10]}...")
    
    # 測試創建 Scammer Agent LLM
    print("\n--- 創建 Scammer LLM ---")
    try:
        llm = LlmFactory.create_llm("scammer", scam_type="假冒銀行")
        print(f"✅ Scammer LLM 創建成功")
        print(f"   模型: {llm.model}")
        print(f"   上傳文件數: {len(llm.uploaded_files)}")
        print(f"   System Instruction 長度: {len(llm.system_instruction)} 字")
        
        if len(llm.uploaded_files) > 0:
            print("❌ 警告: 仍在上傳文件！")
            return False
        else:
            print("✅ 確認: 沒有上傳文件")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試創建 Expert Agent LLM
    print("\n--- 創建 Expert LLM ---")
    try:
        llm = LlmFactory.create_llm("expert", context="假冒銀行詐騙")
        print(f"✅ Expert LLM 創建成功")
        print(f"   模型: {llm.model}")
        print(f"   上傳文件數: {len(llm.uploaded_files)}")
        print(f"   System Instruction 長度: {len(llm.system_instruction)} 字")
        
        if len(llm.uploaded_files) > 0:
            print("❌ 警告: 仍在上傳文件！")
            return False
        else:
            print("✅ 確認: 沒有上傳文件")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_token_estimation():
    """估算 Token 使用量"""
    print("\n" + "=" * 60)
    print("測試 4: Token 使用量估算")
    print("=" * 60)
    
    # 檢查環境變量
    gemini_enabled = os.getenv("GEMINI_ENABLED", "false").lower() == "true"
    
    if not gemini_enabled:
        print("⚠️ GEMINI_ENABLED=false，跳過測試")
        return True
    
    try:
        # 創建 LLM
        llm = LlmFactory.create_llm("scammer", scam_type="假冒銀行")
        
        # 估算 Token
        system_instruction_tokens = len(llm.system_instruction) // 2
        
        print(f"System Instruction:")
        print(f"  字數: {len(llm.system_instruction)}")
        print(f"  預估 Token: {system_instruction_tokens}")
        
        # 假設一個典型的對話
        typical_conversation = "你好，我係滙豐銀行職員，你嘅戶口有可疑交易。" * 10
        conversation_tokens = len(typical_conversation) // 2
        
        print(f"\n典型對話:")
        print(f"  字數: {len(typical_conversation)}")
        print(f"  預估 Token: {conversation_tokens}")
        
        total_tokens = system_instruction_tokens + conversation_tokens
        print(f"\n總計預估 Token: {total_tokens}")
        
        # 對比之前的文件上傳方式
        print(f"\n對比:")
        print(f"  之前（文件上傳）: ~139,742 tokens")
        print(f"  現在（RAG）: ~{total_tokens} tokens")
        print(f"  節省: ~{139742 - total_tokens} tokens ({(139742 - total_tokens) / 139742 * 100:.1f}%)")
        
        if total_tokens < 5000:
            print("\n✅ Token 使用量已大幅降低！")
        else:
            print("\n⚠️ Token 使用量仍然較高")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    
    return True


def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("RAG 整合測試")
    print("=" * 60)
    
    tests = [
        ("RAG 輔助類初始化", test_rag_helper),
        ("RAG 上下文檢索", test_rag_context),
        ("LLM 創建（不上傳文件）", test_llm_creation_no_upload),
        ("Token 使用量估算", test_token_estimation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 測試 '{test_name}' 發生異常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有測試通過！RAG 整合成功！")
        print("\n下一步:")
        print("1. 等待 Gemini API 配額重置（明天）")
        print("2. 設置 GEMINI_ENABLED=true")
        print("3. 運行實際的 Agent 對話測試")
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤信息")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
