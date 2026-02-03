"""
測試 Fine-Tuning 數據保存功能
"""

import sys
from pathlib import Path

# 添加路徑
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from utils.finetuning_formatter import FineTuningFormatter
from utils.logger import log

def test_save():
    """測試保存功能"""
    
    print("="*60)
    print("測試 Fine-Tuning 數據保存功能")
    print("="*60)
    print()
    
    # 創建 formatter
    print("[1/4] 創建 FineTuningFormatter...")
    formatter = FineTuningFormatter()
    print(f"✅ 輸出目錄: {formatter.output_dir}")
    print(f"✅ 目錄存在: {formatter.output_dir.exists()}")
    print()
    
    # 創建測試樣本
    print("[2/4] 創建測試訓練樣本...")
    test_samples = [
        {
            "system": "你是測試系統提示",
            "user": "這是測試用戶輸入",
            "assistant": "這是測試助手回應",
            "metadata": {
                "test": True,
                "round": 1
            }
        }
    ]
    print(f"✅ 創建了 {len(test_samples)} 個測試樣本")
    print()
    
    # 保存測試樣本
    print("[3/4] 保存測試樣本...")
    filepath = formatter.save_to_jsonl(
        samples=test_samples,
        model_type="test",
        simulation_id="test123456"
    )
    
    if filepath:
        print(f"✅ 保存成功: {filepath}")
    else:
        print("❌ 保存失敗")
        return False
    print()
    
    # 驗證文件
    print("[4/4] 驗證文件...")
    file_path = Path(filepath)
    if file_path.exists():
        print(f"✅ 文件存在")
        print(f"✅ 文件大小: {file_path.stat().st_size} bytes")
        
        # 讀取內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"✅ 文件內容長度: {len(content)} 字符")
            print()
            print("文件內容預覽:")
            print("-" * 60)
            print(content[:500])
            print("-" * 60)
        
        # 清理測試文件
        file_path.unlink()
        print()
        print("✅ 測試文件已清理")
        
        return True
    else:
        print("❌ 文件不存在")
        return False

if __name__ == "__main__":
    try:
        success = test_save()
        print()
        print("="*60)
        if success:
            print("✅ 測試通過！Fine-Tuning 數據保存功能正常")
        else:
            print("❌ 測試失敗！請檢查錯誤信息")
        print("="*60)
    except Exception as e:
        print()
        print("="*60)
        print(f"❌ 測試出錯: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()

