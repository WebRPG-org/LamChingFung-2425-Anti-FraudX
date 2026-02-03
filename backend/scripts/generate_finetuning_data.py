"""
Fine-Tuning訓練數據生成腳本
從現有的training_data中批量生成fine-tuning格式數據
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# 添加backend到路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.finetuning_formatter import FineTuningFormatter
from utils.logger import log


class FineTuningDataGenerator:
    """
    批量生成Fine-Tuning訓練數據
    """
    
    def __init__(
        self,
        source_dir: str = "backend/training_data",
        output_dir: str = "backend/training_data/finetuning"
    ):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.formatter = FineTuningFormatter(output_dir=str(self.output_dir))
        
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "expert_samples": 0,
            "scammer_samples": 0,
            "skipped_files": 0,
            "errors": 0
        }
    
    def load_training_file(self, filepath: Path) -> Dict:
        """加載訓練數據文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            log.error(f"❌ 加載文件失敗: {filepath} - {e}")
            self.stats["errors"] += 1
            return None
    
    def process_single_file(self, filepath: Path) -> Dict[str, int]:
        """處理單個訓練數據文件"""
        log.info(f"📄 處理文件: {filepath.name}")
        
        data = self.load_training_file(filepath)
        if not data:
            self.stats["skipped_files"] += 1
            return {"expert": 0, "scammer": 0}
        
        # 提取必要數據
        conversation_history = data.get("conversation_history", [])
        analysis = data.get("analysis", {})
        performance_report = data.get("performance_report", {})
        
        if not conversation_history:
            log.warning(f"⚠️ 文件無對話歷史: {filepath.name}")
            self.stats["skipped_files"] += 1
            return {"expert": 0, "scammer": 0}
        
        # 生成專家訓練樣本
        expert_samples = self.formatter.format_for_expert_training(
            conversation_history,
            analysis,
            performance_report
        )
        
        # 生成騙徒訓練樣本
        scammer_samples = self.formatter.format_for_scammer_training(
            conversation_history,
            analysis,
            performance_report
        )
        
        self.stats["processed_files"] += 1
        self.stats["expert_samples"] += len(expert_samples)
        self.stats["scammer_samples"] += len(scammer_samples)
        
        log.info(f"✅ 生成樣本: 專家={len(expert_samples)}, 騙徒={len(scammer_samples)}")
        
        return {
            "expert": expert_samples,
            "scammer": scammer_samples
        }
    
    def batch_process(self, pattern: str = "training_data_ws_*.json") -> Dict[str, List]:
        """批量處理訓練數據文件"""
        log.info(f"🚀 開始批量處理: {self.source_dir / pattern}")
        
        all_expert_samples = []
        all_scammer_samples = []
        
        # 查找所有符合模式的文件
        files = sorted(self.source_dir.glob(pattern))
        self.stats["total_files"] = len(files)
        
        if not files:
            log.warning(f"⚠️ 未找到符合模式的文件: {pattern}")
            return {"expert": [], "scammer": []}
        
        log.info(f"📁 找到 {len(files)} 個文件")
        
        # 處理每個文件
        for filepath in files:
            samples = self.process_single_file(filepath)
            all_expert_samples.extend(samples.get("expert", []))
            all_scammer_samples.extend(samples.get("scammer", []))
        
        log.info(f"✅ 批量處理完成")
        log.info(f"   總文件數: {self.stats['total_files']}")
        log.info(f"   處理成功: {self.stats['processed_files']}")
        log.info(f"   跳過文件: {self.stats['skipped_files']}")
        log.info(f"   錯誤數: {self.stats['errors']}")
        log.info(f"   專家樣本: {self.stats['expert_samples']}")
        log.info(f"   騙徒樣本: {self.stats['scammer_samples']}")
        
        return {
            "expert": all_expert_samples,
            "scammer": all_scammer_samples
        }
    
    def save_consolidated_dataset(
        self,
        expert_samples: List[Dict],
        scammer_samples: List[Dict],
        split_ratio: float = 0.9
    ) -> Dict[str, str]:
        """
        保存合併的訓練數據集，並分割為訓練集和驗證集
        
        Args:
            expert_samples: 專家訓練樣本
            scammer_samples: 騙徒訓練樣本
            split_ratio: 訓練集比例（默認90%）
            
        Returns:
            保存的文件路徑字典
        """
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存專家數據集
        if expert_samples:
            # 計算分割點
            split_idx = int(len(expert_samples) * split_ratio)
            train_samples = expert_samples[:split_idx]
            val_samples = expert_samples[split_idx:]
            
            # 保存訓練集
            train_file = self.output_dir / f"expert_train_{timestamp}.jsonl"
            self._write_jsonl(train_samples, train_file)
            saved_files["expert_train"] = str(train_file)
            log.info(f"✅ 專家訓練集: {train_file} ({len(train_samples)} 樣本)")
            
            # 保存驗證集
            if val_samples:
                val_file = self.output_dir / f"expert_val_{timestamp}.jsonl"
                self._write_jsonl(val_samples, val_file)
                saved_files["expert_val"] = str(val_file)
                log.info(f"✅ 專家驗證集: {val_file} ({len(val_samples)} 樣本)")
        
        # 保存騙徒數據集
        if scammer_samples:
            split_idx = int(len(scammer_samples) * split_ratio)
            train_samples = scammer_samples[:split_idx]
            val_samples = scammer_samples[split_idx:]
            
            train_file = self.output_dir / f"scammer_train_{timestamp}.jsonl"
            self._write_jsonl(train_samples, train_file)
            saved_files["scammer_train"] = str(train_file)
            log.info(f"✅ 騙徒訓練集: {train_file} ({len(train_samples)} 樣本)")
            
            if val_samples:
                val_file = self.output_dir / f"scammer_val_{timestamp}.jsonl"
                self._write_jsonl(val_samples, val_file)
                saved_files["scammer_val"] = str(val_file)
                log.info(f"✅ 騙徒驗證集: {val_file} ({len(val_samples)} 樣本)")
        
        # 保存統計信息
        stats_file = self.output_dir / f"generation_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "stats": self.stats,
                "files": saved_files,
                "split_ratio": split_ratio
            }, f, ensure_ascii=False, indent=2)
        
        log.info(f"📊 統計信息保存到: {stats_file}")
        
        return saved_files
    
    def _write_jsonl(self, samples: List[Dict], filepath: Path):
        """寫入JSONL格式文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for sample in samples:
                # 構建Ollama fine-tuning格式
                jsonl_line = {
                    "messages": [
                        {"role": "system", "content": sample["system"]},
                        {"role": "user", "content": sample["user"]},
                        {"role": "assistant", "content": sample["assistant"]}
                    ],
                    "metadata": sample.get("metadata", {})
                }
                f.write(json.dumps(jsonl_line, ensure_ascii=False) + '\n')
    
    def generate_modelfile(self, base_model: str = "gemma3:4b") -> Dict[str, str]:
        """
        生成Ollama Modelfile（用於fine-tuning）
        
        Args:
            base_model: 基礎模型名稱
            
        Returns:
            生成的Modelfile路徑
        """
        modelfiles = {}
        
        # 專家模型Modelfile
        expert_modelfile = self.output_dir / "Modelfile.expert"
        expert_content = f"""FROM {base_model}

# 香港反詐騙專家模型 - Fine-tuned for anti-fraud expertise

SYSTEM \"\"\"你是香港反詐騙專家黃sir。你的職責是：
1. 識別詐騙手法和話術
2. 安撫受害者情緒
3. 提供清晰、可執行的防騙建議
4. 預測騙徒下一步行動

你必須：
- 用廣東話溝通
- 先安撫情緒，再提供建議
- 給出具體的行動步驟
- 提供真實案例作為證據
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
"""
        
        with open(expert_modelfile, 'w', encoding='utf-8') as f:
            f.write(expert_content)
        
        modelfiles["expert"] = str(expert_modelfile)
        log.info(f"✅ 專家Modelfile: {expert_modelfile}")
        
        # 騙徒模型Modelfile
        scammer_modelfile = self.output_dir / "Modelfile.scammer"
        scammer_content = f"""FROM {base_model}

# 詐騙模擬模型 - Fine-tuned for scam simulation (訓練用途)

SYSTEM \"\"\"你是一個模擬詐騙者（僅用於反詐騙訓練）。
重要：此模型僅用於反詐騙教育和訓練，不得用於實際詐騙行為。
\"\"\"

PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
"""
        
        with open(scammer_modelfile, 'w', encoding='utf-8') as f:
            f.write(scammer_content)
        
        modelfiles["scammer"] = str(scammer_modelfile)
        log.info(f"✅ 騙徒Modelfile: {scammer_modelfile}")
        
        # 生成訓練腳本
        train_script = self.output_dir / "train.sh"
        train_script_content = f"""#!/bin/bash

# 香港反詐騙AI模型訓練腳本

echo "開始訓練反詐騙專家模型..."

# 找到最新的訓練數據
EXPERT_TRAIN=$(ls -t expert_train_*.jsonl | head -1)
SCAMMER_TRAIN=$(ls -t scammer_train_*.jsonl | head -1)

if [ -z "$EXPERT_TRAIN" ]; then
    echo "錯誤：未找到專家訓練數據"
    exit 1
fi

if [ -z "$SCAMMER_TRAIN" ]; then
    echo "錯誤：未找到騙徒訓練數據"
    exit 1
fi

echo "使用訓練數據："
echo "  專家: $EXPERT_TRAIN"
echo "  騙徒: $SCAMMER_TRAIN"

# 訓練專家模型
echo "\\n=== 訓練專家模型 ==="
ollama create anti-fraud-expert-hk -f Modelfile.expert --adapter $EXPERT_TRAIN

if [ $? -eq 0 ]; then
    echo "✅ 專家模型訓練完成: anti-fraud-expert-hk"
else
    echo "❌ 專家模型訓練失敗"
fi

# 訓練騙徒模擬模型
echo "\\n=== 訓練騙徒模擬模型 ==="
ollama create scam-simulator-hk -f Modelfile.scammer --adapter $SCAMMER_TRAIN

if [ $? -eq 0 ]; then
    echo "✅ 騙徒模擬模型訓練完成: scam-simulator-hk"
else
    echo "❌ 騙徒模擬模型訓練失敗"
fi

echo "\\n=== 訓練完成 ==="
echo "可用模型："
echo "  - anti-fraud-expert-hk (專家模型)"
echo "  - scam-simulator-hk (騙徒模擬模型)"
echo ""
echo "測試模型："
echo "  ollama run anti-fraud-expert-hk"
echo "  ollama run scam-simulator-hk"
"""
        
        with open(train_script, 'w', encoding='utf-8') as f:
            f.write(train_script_content)
        
        # 設置執行權限（Linux/Mac）
        try:
            os.chmod(train_script, 0o755)
        except Exception:
            pass
        
        modelfiles["train_script"] = str(train_script)
        log.info(f"✅ 訓練腳本: {train_script}")
        
        return modelfiles
    
    def run(self, generate_modelfiles: bool = True):
        """
        執行完整的生成流程
        
        Args:
            generate_modelfiles: 是否生成Modelfile和訓練腳本
        """
        log.info("=" * 60)
        log.info("🚀 開始生成Fine-Tuning訓練數據")
        log.info("=" * 60)
        
        # 批量處理
        samples = self.batch_process()
        
        # 保存數據集
        saved_files = self.save_consolidated_dataset(
            samples["expert"],
            samples["scammer"]
        )
        
        # 生成Modelfile
        if generate_modelfiles:
            modelfiles = self.generate_modelfile()
            saved_files.update(modelfiles)
        
        log.info("=" * 60)
        log.info("✅ 完成！")
        log.info("=" * 60)
        log.info(f"📊 總計生成:")
        log.info(f"   專家樣本: {self.stats['expert_samples']}")
        log.info(f"   騙徒樣本: {self.stats['scammer_samples']}")
        log.info(f"   保存文件: {len(saved_files)}")
        log.info("=" * 60)
        
        if generate_modelfiles:
            log.info("📝 下一步：")
            log.info("   1. 進入 backend/training_data/finetuning 目錄")
            log.info("   2. 執行 ./train.sh 開始訓練模型")
            log.info("   3. 訓練完成後，更新 .env 文件中的模型名稱")
            log.info("=" * 60)
        
        return saved_files


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成Fine-Tuning訓練數據")
    parser.add_argument(
        "--source-dir",
        default="backend/training_data",
        help="訓練數據源目錄"
    )
    parser.add_argument(
        "--output-dir",
        default="backend/training_data/finetuning",
        help="輸出目錄"
    )
    parser.add_argument(
        "--no-modelfiles",
        action="store_true",
        help="不生成Modelfile和訓練腳本"
    )
    
    args = parser.parse_args()
    
    generator = FineTuningDataGenerator(
        source_dir=args.source_dir,
        output_dir=args.output_dir
    )
    
    generator.run(generate_modelfiles=not args.no_modelfiles)


if __name__ == "__main__":
    main()

