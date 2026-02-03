"""
合併所有訓練數據源
包括：對話訓練數據 + 防騙警示數據
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# 添加backend到路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log


class TrainingDataMerger:
    """
    合併多個來源的訓練數據
    """
    
    def __init__(self, output_dir: str = "backend/training_data/finetuning"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "dialogue_samples": 0,
            "alerts_samples": 0,
            "hotline_samples": 0,
            "total_samples": 0
        }
    
    def load_jsonl_files(self, pattern: str) -> List[Dict]:
        """加載所有符合模式的JSONL文件"""
        samples = []
        files = sorted(self.output_dir.glob(pattern))
        
        for filepath in files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            samples.append(data)
                log.info(f"   ✅ 加載: {filepath.name} ({len(samples)} 樣本)")
            except Exception as e:
                log.error(f"   ❌ 加載失敗: {filepath.name} - {e}")
        
        return samples
    
    def merge_expert_data(self) -> List[Dict]:
        """合併所有專家訓練數據"""
        log.info("📚 合併專家訓練數據...")
        
        all_samples = []
        
        # 1. 加載對話訓練數據
        log.info("   [1/3] 加載對話訓練數據...")
        dialogue_samples = self.load_jsonl_files("finetune_expert_*.jsonl")
        self.stats["dialogue_samples"] = len(dialogue_samples)
        all_samples.extend(dialogue_samples)
        
        # 2. 加載警示訓練數據
        log.info("   [2/3] 加載警示訓練數據...")
        alerts_samples = self.load_jsonl_files("alerts_expert_*.jsonl")
        self.stats["alerts_samples"] = len(alerts_samples)
        all_samples.extend(alerts_samples)
        
        # 3. 加載熱線訓練數據
        log.info("   [3/3] 加載熱線訓練數據...")
        hotline_samples = self.load_jsonl_files("hotline_training_*.jsonl")
        self.stats["hotline_samples"] = len(hotline_samples)
        all_samples.extend(hotline_samples)
        
        self.stats["total_samples"] = len(all_samples)
        
        log.info(f"✅ 合併完成！")
        log.info(f"   對話樣本: {self.stats['dialogue_samples']}")
        log.info(f"   警示樣本: {self.stats['alerts_samples']}")
        log.info(f"   熱線樣本: {self.stats['hotline_samples']}")
        log.info(f"   總樣本數: {self.stats['total_samples']}")
        
        return all_samples
    
    def save_merged_data(
        self,
        samples: List[Dict],
        prefix: str = "merged_expert",
        split_ratio: float = 0.9
    ) -> Dict[str, str]:
        """
        保存合併後的訓練數據
        
        Args:
            samples: 訓練樣本列表
            prefix: 文件名前綴
            split_ratio: 訓練集比例
            
        Returns:
            保存的文件路徑
        """
        if not samples:
            log.warning("⚠️ 沒有樣本可保存")
            return {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = {}
        
        # 分割訓練集和驗證集
        split_idx = int(len(samples) * split_ratio)
        train_samples = samples[:split_idx]
        val_samples = samples[split_idx:]
        
        # 保存訓練集
        train_file = self.output_dir / f"{prefix}_train_{timestamp}.jsonl"
        self._write_jsonl(train_samples, train_file)
        saved_files["train"] = str(train_file)
        log.info(f"✅ 訓練集: {train_file.name} ({len(train_samples)} 樣本)")
        
        # 保存驗證集
        if val_samples:
            val_file = self.output_dir / f"{prefix}_val_{timestamp}.jsonl"
            self._write_jsonl(val_samples, val_file)
            saved_files["val"] = str(val_file)
            log.info(f"✅ 驗證集: {val_file.name} ({len(val_samples)} 樣本)")
        
        # 保存統計信息
        stats_file = self.output_dir / f"{prefix}_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "stats": self.stats,
                "files": saved_files,
                "split_ratio": split_ratio,
                "train_samples": len(train_samples),
                "val_samples": len(val_samples)
            }, f, ensure_ascii=False, indent=2)
        
        log.info(f"📊 統計信息: {stats_file.name}")
        
        return saved_files
    
    def _write_jsonl(self, samples: List[Dict], filepath: Path):
        """寫入JSONL格式文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    def generate_modelfile(self, base_model: str = "gemma3:4b") -> str:
        """生成合併數據的Modelfile"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        modelfile_path = self.output_dir / f"Modelfile.expert_merged_{timestamp}"
        
        content = f"""FROM {base_model}

# 香港反詐騙專家模型 - 整合版
# 包含對話訓練 + 防騙警示知識庫

SYSTEM \"\"\"你是香港反詐騙專家黃sir，擁有30年處理詐騙案件的經驗。

你的專業能力：
1. 識別各種詐騙手法和話術
2. 提供清晰、可執行的防騙建議
3. 安撫受害者情緒並給予支持
4. 基於真實案例提供專業分析
5. 預測騙徒下一步行動

你的溝通風格：
- 用廣東話與市民溝通
- 先安撫情緒，再提供建議
- 給出具體的行動步驟
- 提供真實案例作為證據
- 保持專業但親切的態度

你的知識來源：
- 實際對話訓練數據
- 香港警方防騙警示
- 反詐騙協調中心公告
- 真實詐騙案例分析
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
"""
        
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        log.info(f"✅ Modelfile: {modelfile_path.name}")
        
        return str(modelfile_path)
    
    def run(self):
        """執行完整的合併流程"""
        log.info("=" * 60)
        log.info("🚀 合併所有訓練數據")
        log.info("=" * 60)
        
        # 合併專家數據
        samples = self.merge_expert_data()
        
        # 保存合併數據
        if samples:
            saved_files = self.save_merged_data(samples)
            
            # 生成Modelfile
            modelfile = self.generate_modelfile()
            saved_files["modelfile"] = modelfile
            
            log.info("=" * 60)
            log.info("✅ 完成！")
            log.info("=" * 60)
            log.info(f"📊 數據統計:")
            log.info(f"   對話訓練: {self.stats['dialogue_samples']} 樣本")
            log.info(f"   警示知識: {self.stats['alerts_samples']} 樣本")
            log.info(f"   總計: {self.stats['total_samples']} 樣本")
            log.info("=" * 60)
            log.info("📝 下一步：")
            log.info("   執行訓練命令：")
            log.info(f"   python backend/scripts/run_finetuning.py --model expert")
            log.info("=" * 60)
            
            return saved_files
        else:
            log.error("❌ 沒有可合併的數據")
            return {}


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="合併所有訓練數據")
    parser.add_argument(
        "--output-dir",
        default="backend/training_data/finetuning",
        help="輸出目錄"
    )
    
    args = parser.parse_args()
    
    merger = TrainingDataMerger(output_dir=args.output_dir)
    merger.run()


if __name__ == "__main__":
    main()
