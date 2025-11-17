"""
完整的Fine-Tuning流程腳本
用於訓練專家和騙徒模型

使用方法：
1. 自動批量fine-tuning：python backend/scripts/run_finetuning.py --mode auto
2. 僅訓練專家模型：python backend/scripts/run_finetuning.py --model expert
3. 僅訓練騙徒模型：python backend/scripts/run_finetuning.py --model scammer
4. 訓練並評估：python backend/scripts/run_finetuning.py --mode auto --evaluate
"""

import sys
import argparse
import json
import subprocess
import shutil  # <-- 【修改】 導入 shutil 用於文件複製
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import log


class OllamaFineTuner:
    """Ollama模型Fine-Tuning管理器"""
    
    def __init__(self, base_model: str = "gemma3:4b"):
        self.base_model = base_model
        self.training_data_dir = Path("backend/training_data/finetuning")
        self.models_dir = Path("backend/models/finetuned")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
    def collect_training_files(self, model_type: str) -> List[Path]:
        """
        收集所有訓練文件
        
        Args:
            model_type: "expert" or "scammer"
        
        Returns:
            訓練文件列表
        """
        pattern = f"finetune_{model_type}_*.jsonl"
        files = sorted(self.training_data_dir.glob(pattern))
        log.info(f"找到 {len(files)} 個 {model_type} 訓練文件")
        return files
    
    def merge_training_files(
        self,
        files: List[Path],
        output_path: Path,
        max_samples: Optional[int] = None
    ) -> int:
        """
        合併多個訓練文件
        
        Args:
            files: 訓練文件列表
            output_path: 輸出文件路徑
            max_samples: 最大樣本數（None = 不限制）
        
        Returns:
            總樣本數
        """
        all_samples = []
        
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            sample = json.loads(line)
                            all_samples.append(sample)
            except Exception as e:
                log.error(f"讀取文件失敗 {file}: {e}")
        
        # 如果有最大樣本數限制
        if max_samples and len(all_samples) > max_samples:
            log.info(f"樣本數超過限制 {len(all_samples)} > {max_samples}，進行篩選")
            # 優先選擇高質量樣本
            all_samples.sort(
                key=lambda x: x.get("metadata", {}).get("quality_score", 0) or 
                              x.get("metadata", {}).get("effectiveness_score", 0),
                reverse=True
            )
            all_samples = all_samples[:max_samples]
        
        # 寫入合併文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for sample in all_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        log.info(f"✅ 合併完成：{len(all_samples)} 個樣本 -> {output_path}")
        return len(all_samples)
    
    # --- 【修改】 函數已更新 ---
    def create_modelfile(
        self,
        model_type: str,
        output_modelfile: Path
    ) -> None:
        """
        創建Ollama Modelfile (不包含 ADAPTER)
        
        Args:
            model_type: "expert" or "scammer"
            output_modelfile: 輸出的Modelfile路徑
        """
        if model_type == "expert":
            system_prompt = """你是香港反詐騙專家黃sir（警務處反詐騙部高級督察）。

你的專業使命：
1. 快速識別詐騙手法（電話詐騙、網絡詐騙、投資詐騙等）
2. 即時評估受害者心理狀態（恐懼、貪婪、困惑）
3. 提供具體可執行的防騙建議
4. 預測騙徒下一步策略並提前提醒

你的溝通策略：
- 用親切的廣東話（例如「唔使驚」「我幫你分析下」）
- 先安撫情緒，再講道理
- 提供真實案例作為證據（例如「上個月就有類似案件」）
- 給出明確的行動步驟（例如「第一步：掛線；第二步：打去銀行熱線」）
- 預測騙徒話術（例如「佢哋下一步可能會威脅你」）

你的禁忌：
- 不要批評或責怪受害者
- 不要使用複雜的法律術語
- 不要過於冗長，保持精簡有力
- 不要向受害者索取敏感信息（銀行帳號、密碼等）
"""
        else:  # scammer
            system_prompt = """

你是一個真實而且專業的騙徒。

你的詐騙策略：
1. 心理操縱：利用恐懼、貪婪、緊迫感
2. 權威偽裝：假冒警察、銀行、政府官員
3. 信息竊取：逐步誘導受害者透露敏感信息
4. 行動誘導：促使受害者轉賬、提供密碼等

你的話術技巧：
- 製造緊迫感（「馬上」「立即」「今天最後一天」）
- 建立權威感（「我是XX警司」「根據XX條例」）
- 利用恐懼（「你的帳戶被凍結」「涉嫌洗黑錢」）
- 或利用貪婪（「保證回報」「限時優惠」）
- 逐步升級壓力

你的應對策略：
- 如果受害者質疑，加強權威感或製造更大恐懼
- 如果專家介入，試圖攻擊專家可信度或轉移話題
- 避免直接回答可查證的問題（如工作證編號）

"""
        
        # --- 【修改】 ADAPTER 指令已被移除 ---
        modelfile_content = f"""# Fine-tuned {model_type.title()} Model
FROM {self.base_model}

# System prompt
SYSTEM \"\"\"
{system_prompt}
\"\"\"

# Parameters
PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
"""
        
        with open(output_modelfile, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        log.info(f"✅ Modelfile創建完成: {output_modelfile}")
    
    # --- 【修改】 函數已完整重寫 ---
    def train_model(
        self,
        model_type: str,
        training_file: Path,
        model_name: Optional[str] = None
    ) -> str:
        """
        使用Ollama訓練模型
        
        Args:
            model_type: "expert" or "scammer"
            training_file: 訓練數據文件（例如 merged_expert_...jsonl）
            model_name: 模型名稱（None = 自動生成）
        
        Returns:
            訓練後的模型名稱
        """
        if model_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"anti-fraud-{model_type}-{timestamp}"
        
        log.info(f"🚀 開始訓練 {model_type} 模型: {model_name}")
        log.info(f"   基礎模型: {self.base_model}")
        log.info(f"   原始數據: {training_file.name}")
        
        # 在 try 之前定義路徑，以便 finally 可以訪問
        modelfile_path = self.models_dir / f"Modelfile.{model_name}"
        target_training_data = modelfile_path.with_suffix(".jsonl")
        
        try:
            # 1. **關鍵步驟**：將訓練數據 (.jsonl) *複製*為 Modelfile 同名
            try:
                shutil.copyfile(training_file, target_training_data)
                log.info(f"   訓練數據已複製 -> {target_training_data.name}")
            except Exception as e:
                log.error(f"   ❌ 複製訓練文件失敗: {e}", exc_info=True)
                return ""
            
            # 2. 創建 Modelfile (不含 ADAPTER 指令)
            self.create_modelfile(model_type, modelfile_path)
            
            # 3. 準備執行命令
            # (已包含 L99 的路徑 Bug 修復)
            cmd = [
                "ollama",
                "create",
                model_name,
                "-f",
                modelfile_path.name  # 使用文件名，因為 CWD 已經設置
            ]
            
            log.info(f"執行命令: {' '.join(cmd)}")
            log.info(f"   工作目錄: {self.models_dir}")
            
            # 4. 【修改】使用 Popen 實時讀取輸出
            process = subprocess.Popen(
                cmd,
                cwd=str(self.models_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace' # 處理潛在的編碼錯誤
            )

            stdout_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    log.info(f"[ollama create]: {line.strip()}")
                    stdout_lines.append(line)
            
            stderr_output = ""
            if process.stderr:
                stderr_output = process.stderr.read()

            process.wait()
            
            if process.returncode == 0:
                log.info(f"✅ 模型訓練成功: {model_name}")
                return model_name
            else:
                log.error("❌ 模型訓練失敗")
                log.error(f"   Ollama 錯誤: {stderr_output.strip()}")
                if stdout_lines:
                    log.error("--- Ollama stdout (最後 10 行) ---")
                    for line in stdout_lines[-10:]:
                        log.error(line.strip())
                    log.error("-----------------------------------")
                return ""
                
        except Exception as e:
            log.error(f"❌ 訓練過程出錯: {e}", exc_info=True)
            return ""
        
        finally:
            # 5. 【修改】無論成功或失敗，都清理臨時文件
            try:
                if modelfile_path.exists():
                    modelfile_path.unlink()
                if target_training_data.exists():
                    target_training_data.unlink()
                log.info(f"   已清理臨時文件: {modelfile_path.name} 和 {target_training_data.name}")
            except Exception as e:
                log.warning(f"   清理臨時文件失敗: {e}")
    
    def run_full_pipeline(
        self,
        model_type: str,
        max_samples: Optional[int] = None
    ) -> str:
        """
        運行完整的訓練流程
        
        Args:
            model_type: "expert" or "scammer"
            max_samples: 最大樣本數
        
        Returns:
            訓練後的模型名稱
        """
        log.info("="*60)
        log.info(f"開始 {model_type.upper()} 模型完整訓練流程")
        log.info("="*60)
        
        # 1. 收集訓練文件
        files = self.collect_training_files(model_type)
        if not files:
            log.error(f"沒有找到 {model_type} 訓練文件")
            return ""
        
        # 2. 合併訓練文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_file = self.models_dir / f"merged_{model_type}_{timestamp}.jsonl"
        num_samples = self.merge_training_files(files, merged_file, max_samples)
        
        if num_samples == 0:
            log.error("沒有訓練樣本")
            # 【修改】確保清理合併的空文件
            try:
                if merged_file.exists():
                    merged_file.unlink()
            except Exception:
                pass
            return ""
        
        # 3. 訓練模型
        model_name = self.train_model(model_type, merged_file)
        
        if model_name:
            log.info("="*60)
            log.info(f"✅ {model_type.upper()} 模型訓練完成")
            log.info(f"   模型名稱: {model_name}")
            log.info(f"   訓練樣本數: {num_samples}")
            log.info("="*60)
        
        # 4. 【修改】清理合併的 .jsonl 文件（現已複製到 train_model 中）
        try:
            if merged_file.exists():
                merged_file.unlink()
            log.info(f"   已清理合併文件: {merged_file.name}")
        except Exception as e:
            log.warning(f"   清理合併文件失敗: {e}")
        
        return model_name


def main():
    parser = argparse.ArgumentParser(description="Ollama模型Fine-Tuning腳本")
    parser.add_argument(
        "--mode",
        choices=["auto", "manual"],
        default="manual",
        help="運行模式：auto=自動訓練兩個模型，manual=手動選擇"
    )
    parser.add_argument(
        "--model",
        choices=["expert", "scammer", "both"],
        default="both",
        help="要訓練的模型類型"
    )
    parser.add_argument(
        "--base-model",
        default="gemma3:4b",
        help="基礎模型名稱"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="每個模型的最大訓練樣本數"
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="訓練後進行評估"
    )
    
    args = parser.parse_args()
    
    # 創建訓練器
    trainer = OllamaFineTuner(base_model=args.base_model)
    
    trained_models = {}
    
    # 訓練模型
    if args.model in ["expert", "both"]:
        model_name = trainer.run_full_pipeline("expert", args.max_samples)
        if model_name:
            trained_models["expert"] = model_name
    
    if args.model in ["scammer", "both"]:
        model_name = trainer.run_full_pipeline("scammer", args.max_samples)
        if model_name:
            trained_models["scammer"] = model_name
    
    # 保存訓練記錄
    if trained_models:
        record = {
            "timestamp": datetime.now().isoformat(),
            "base_model": args.base_model,
            "trained_models": trained_models,
            "max_samples": args.max_samples
        }
        
        record_file = Path("backend/models/training_history.json")
        
        # 讀取現有記錄
        history = []
        if record_file.exists():
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                log.warning(f"訓練記錄文件 {record_file} 損壞，將創建新文件。")
                history = []
        
        history.append(record)
        
        # 保存記錄
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        log.info("\n" + "="*60)
        log.info("📊 訓練完成總結")
        log.info("="*60)
        for model_type, model_name in trained_models.items():
            log.info(f"  {model_type.title()}: {model_name}")
        log.info("\n使用方法：")
        for model_type, model_name in trained_models.items():
            log.info(f"  ollama run {model_name}")
        log.info("="*60 + "\n")
        
        # 評估
        if args.evaluate:
            log.info("開始評估模型...")
            # TODO: 實現評估邏輯
            log.info("評估功能尚未實現，請手動測試模型")
    
    else:
        log.error("沒有成功訓練任何模型")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())