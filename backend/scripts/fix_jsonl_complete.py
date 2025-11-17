"""完整修復 JSONL 文件中的所有格式錯誤"""
import json
import sys
from pathlib import Path

def fix_jsonl_file(filepath: Path) -> tuple[int, int]:
    """
    修復 JSONL 文件中的所有格式錯誤
    
    Returns:
        (fixed_count, total_lines) 元組
    """
    fixed_count = 0
    total_lines = 0
    
    try:
        # 讀取所有行
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # 修復每一行
        fixed_lines = []
        errors = []
        
        for i, line in enumerate(lines, 1):
            if not line.strip():
                fixed_lines.append(line)
                continue
            
            original_line = line
            fixed_line = line
            
            try:
                # 嘗試解析 JSON
                json.loads(line)
                fixed_lines.append(line)
            except json.JSONDecodeError as e:
                # 修復常見錯誤
                errors.append((i, str(e)))
                
                # 錯誤 1: {"role": "assistant": "..."} -> {"role": "assistant", "content": "..."}
                if '"role": "assistant":' in fixed_line:
                    fixed_line = fixed_line.replace('"role": "assistant":', '"role": "assistant", "content":')
                
                # 錯誤 2: {"role": "assistant" : "..."} (有空格) -> {"role": "assistant", "content": "..."}
                if '"role": "assistant" :' in fixed_line:
                    fixed_line = fixed_line.replace('"role": "assistant" :', '"role": "assistant", "content":')
                
                # 錯誤 3: 檢查是否缺少逗號
                if '"role": "assistant"' in fixed_line and '", "content":' not in fixed_line:
                    # 嘗試在 "assistant" 後面添加 ", "content":"
                    import re
                    fixed_line = re.sub(
                        r'"role":\s*"assistant"\s*:',
                        '"role": "assistant", "content":',
                        fixed_line
                    )
                
                # 再次嘗試解析
                try:
                    json.loads(fixed_line)
                    fixed_lines.append(fixed_line)
                    fixed_count += 1
                    print(f"  [OK] Line {i}: Fixed")
                except json.JSONDecodeError as e2:
                    print(f"  [ERROR] Line {i}: Cannot fix - {e2}")
                    print(f"     原始: {original_line[:100]}...")
                    # 跳過無法修復的行
                    continue
        
        # 寫回文件
        if fixed_count > 0 or errors:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            
            print(f"\n[SUCCESS] Fixed:")
            print(f"   Total lines: {total_lines}")
            print(f"   Fixed lines: {fixed_count}")
            print(f"   Error lines: {len(errors)}")
            print(f"   Valid lines: {len(fixed_lines)}")
        
        # 驗證修復後的文件
        print(f"\n[VERIFY] Validating fixed file...")
        valid_count = 0
        invalid_count = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                    valid_count += 1
                except json.JSONDecodeError as e:
                    invalid_count += 1
                    print(f"  [WARNING] Line {i} still has error: {e}")
        
        print(f"\n[RESULT] Validation:")
        print(f"   Valid JSON lines: {valid_count}")
        print(f"   Invalid JSON lines: {invalid_count}")
        
        return fixed_count, total_lines
        
    except Exception as e:
        print(f"❌ 處理文件時出錯: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_jsonl_complete.py <jsonl_file>")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"❌ 文件不存在: {filepath}")
        sys.exit(1)
    
    print(f"[FIX] Starting to fix {filepath}...")
    print("="*60)
    
    fixed, total = fix_jsonl_file(filepath)
    
    print("="*60)
    if fixed > 0:
        print(f"[SUCCESS] Fixed {fixed} lines")
    else:
        print("[INFO] No lines needed fixing, or all error lines were skipped")

