"""
Test Fine-Tuning Data Save Functionality
"""

import sys
from pathlib import Path

# Add path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from utils.finetuning_formatter import FineTuningFormatter
from utils.logger import log

def test_save():
    """Test save functionality"""
    
    print("="*60)
    print("Test Fine-Tuning Data Save")
    print("="*60)
    print()
    
    # Create formatter
    print("[1/4] Creating FineTuningFormatter...")
    formatter = FineTuningFormatter()
    print(f"Output dir: {formatter.output_dir}")
    print(f"Dir exists: {formatter.output_dir.exists()}")
    print()
    
    # Create test samples
    print("[2/4] Creating test samples...")
    test_samples = [
        {
            "system": "Test system prompt",
            "user": "Test user input",
            "assistant": "Test assistant response",
            "metadata": {
                "test": True,
                "round": 1
            }
        }
    ]
    print(f"Created {len(test_samples)} test samples")
    print()
    
    # Save test samples
    print("[3/4] Saving test samples...")
    filepath = formatter.save_to_jsonl(
        samples=test_samples,
        model_type="test",
        simulation_id="test123456"
    )
    
    if filepath:
        print(f"Saved successfully: {filepath}")
    else:
        print("Save failed")
        return False
    print()
    
    # Verify file
    print("[4/4] Verifying file...")
    file_path = Path(filepath)
    if file_path.exists():
        print("File exists!")
        print(f"File size: {file_path.stat().st_size} bytes")
        
        # Read content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Content length: {len(content)} characters")
            print()
            print("Content preview:")
            print("-" * 60)
            print(content[:500])
            print("-" * 60)
        
        # Cleanup
        file_path.unlink()
        print()
        print("Test file cleaned up")
        
        return True
    else:
        print("File does not exist!")
        return False

if __name__ == "__main__":
    try:
        success = test_save()
        print()
        print("="*60)
        if success:
            print("TEST PASSED! Fine-Tuning save works correctly")
        else:
            print("TEST FAILED! Check error messages")
        print("="*60)
    except Exception as e:
        print()
        print("="*60)
        print(f"TEST ERROR: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()

