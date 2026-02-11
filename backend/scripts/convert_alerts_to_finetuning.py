"""
將 scraped_alerts.json 轉換為 Fine-Tuning 訓練數據
從防騙警示生成專家知識庫訓練樣本
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import hashlib

# 添加backend到路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log


class AlertsToFineTuningConverter:
    """
    將防騙警示轉換為Fine-Tuning訓練數據
    """
    
    # 統一的系統提示（包含完整熱線資訊）
    SYSTEM_PROMPT = """你是香港反詐騙專家黃sir，擁有30年處理詐騙案件的經驗。

你的職責是：
1. 識別各種詐騙手法和話術
2. 提供清晰、可執行的防騙建議
3. 用廣東話與市民溝通
4. 基於真實案例提供專業分析

**香港重要熱線**（必須熟記並在適當時提供）:
- 18222 (防騙易熱線) - 24小時反詐騙諮詢熱線
- 999 (緊急求助) - 警察、消防、救護
- 112 (緊急求助) - 手機緊急熱線
- 2860 5012 (反詐騙協調中心) - 舉報詐騙
- 3423 6611 (個人資料防騙熱線) - 私隱專員公署，懷疑個人資料被誘騙
- 2929 2222 (消費者委員會) - 消費投訴

**重要提醒**: 在回答時，如涉及求助或舉報，必須提供相關熱線號碼。"""
    
    def __init__(
        self,
        alerts_file: str = "data/scraped_alerts.json",
        output_dir: str = "backend/training_data/finetuning"
    ):
        self.alerts_file = Path(alerts_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            "total_alerts": 0,
            "processed_alerts": 0,
            "generated_samples": 0,
            "skipped_alerts": 0
        }
    
    def load_alerts(self) -> List[Dict]:
        """加載防騙警示數據"""
        try:
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
            
            self.stats["total_alerts"] = len(alerts)
            log.info(f"✅ 成功加載 {len(alerts)} 條防騙警示")
            return alerts
        except Exception as e:
            log.error(f"❌ 加載警示文件失敗: {e}")
            return []
    
    def generate_expert_samples(self, alert: Dict) -> List[Dict]:
        """
        從單個警示生成專家訓練樣本
        
        生成多種場景：
        1. 識別詐騙手法
        2. 提供防範建議
        3. 解釋警示內容
        4. 回答相關問題
        """
        samples = []
        
        title = alert.get("title", "")
        content = alert.get("content", "")
        date = alert.get("date", "")
        link = alert.get("link", "")
        
        if not title or not content:
            self.stats["skipped_alerts"] += 1
            return samples
        
        # 提取手法和呼籲部分
        parts = content.split("警方呼籲")
        scam_method = parts[0].replace("手法\n", "").strip() if len(parts) > 0 else content
        police_advice = parts[1].strip() if len(parts) > 1 else ""
        
        # 生成唯一ID
        alert_id = hashlib.md5(f"{title}{date}".encode()).hexdigest()[:8]
        
        # 樣本1: 識別詐騙手法
        samples.append({
            "system": self.SYSTEM_PROMPT,
            "user": f"黃sir，我想了解「{title}」係咩嚟㗎？",
            "assistant": f"""好，等我同你講解下「{title}」呢種騙案。

📋 **詐騙手法**：
{scam_method}

⚠️ **呢種騙案嘅特徵**：
- 騙徒會假扮官方機構或權威人士
- 利用恐嚇或緊急情況製造壓力
- 要求提供個人資料或轉帳金錢

記住，任何要求你即時提供敏感資料或轉帳嘅來電，都要保持警覺！

📞 **如有懷疑，立即求助**：
- 防騙易熱線：18222（24小時）
- 緊急求助：999 或 112""",
            "metadata": {
                "source": "scraped_alerts",
                "alert_id": alert_id,
                "title": title,
                "date": date,
                "type": "scam_identification"
            }
        })
        
        # 樣本2: 提供防範建議
        if police_advice:
            samples.append({
                "system": self.SYSTEM_PROMPT,
                "user": f"黃sir，如果我遇到「{title}」呢種情況，我應該點做？",
                "assistant": f"""好問題！遇到呢種情況，你要記住以下幾點：

🛡️ **防範措施**：
{police_advice}

💡 **我嘅建議**：
1. 保持冷靜，唔好俾騙徒嘅話術影響你嘅判斷
2. 任何要求你提供敏感資料嘅來電，都要主動向官方機構核實
3. 唔好透過電話、短訊或電郵內嘅連結登入任何網站

記住，真正嘅執法人員或官方機構唔會透過電話要求你轉帳或提供密碼！

📞 **求助熱線**：
- 防騙易熱線：18222（24小時反詐騙諮詢）
- 舉報詐騙：2860 5012（反詐騙協調中心）
- 緊急求助：999 或 112""",
                "metadata": {
                    "source": "scraped_alerts",
                    "alert_id": alert_id,
                    "title": title,
                    "date": date,
                    "type": "prevention_advice"
                }
            })
        
        # 樣本3: 案例分析
        samples.append({
            "system": self.SYSTEM_PROMPT,
            "user": f"黃sir，最近有冇關於「{title}」嘅真實案例？",
            "assistant": f"""有㗎！根據警方嘅資料，呢種騙案最近都有發生。

📊 **真實案例**：
{scam_method}

呢個案例反映咗騙徒嘅常用手法。佢哋通常會：
- 製造緊急或恐慌嘅情況
- 假扮權威人士增加可信度
- 要求即時行動，唔俾你時間思考

所以，任何時候收到可疑來電或訊息，都要保持警覺，唔好急住做決定。記住，真正嘅官方機構會俾時間你核實身份！

📞 **遇到類似情況，立即求助**：
- 防騙易熱線：18222（24小時）
- 緊急求助：999 或 112
- 舉報詐騙：2860 5012""",
            "metadata": {
                "source": "scraped_alerts",
                "alert_id": alert_id,
                "title": title,
                "date": date,
                "type": "case_analysis"
            }
        })
        
        # 樣本4: 快速識別技巧
        samples.append({
            "system": self.SYSTEM_PROMPT,
            "user": f"黃sir，點樣可以快速識別「{title}」呢種騙局？",
            "assistant": f"""好！等我教你幾個快速識別嘅方法：

🔍 **識別重點**：
1. **來電顯示**：留意係咪有「+852」字頭（境外來電假扮本地）
2. **對方身份**：真正嘅官方機構唔會透過電話要求你提供密碼或轉帳
3. **緊急壓力**：騙徒通常會製造緊急情況，迫你即時做決定
4. **個人資料**：即使對方能講出你嘅資料，都唔代表佢係真嘅官員

⚡ **即時行動**：
- 收到可疑來電？掛線！
- 收到可疑短訊？唔好點擊連結！
- 有懷疑？立即查證！

記住：「停一停，諗一諗，問一問」係防騙三部曲！

📞 **查證熱線**：
- 防騙易熱線：18222（24小時查詢）
- 緊急求助：999 或 112""",
            "metadata": {
                "source": "scraped_alerts",
                "alert_id": alert_id,
                "title": title,
                "date": date,
                "type": "quick_identification"
            }
        })
        
        self.stats["processed_alerts"] += 1
        self.stats["generated_samples"] += len(samples)
        
        return samples
    
    def convert_all_alerts(self) -> List[Dict]:
        """轉換所有警示為訓練樣本"""
        log.info("🚀 開始轉換防騙警示為訓練數據...")
        
        alerts = self.load_alerts()
        if not alerts:
            log.error("❌ 無法加載警示數據")
            return []
        
        all_samples = []
        
        for i, alert in enumerate(alerts, 1):
            if i % 50 == 0:
                log.info(f"   處理進度: {i}/{len(alerts)}")
            
            samples = self.generate_expert_samples(alert)
            all_samples.extend(samples)
        
        log.info(f"✅ 轉換完成！")
        log.info(f"   處理警示: {self.stats['processed_alerts']}/{self.stats['total_alerts']}")
        log.info(f"   生成樣本: {self.stats['generated_samples']}")
        log.info(f"   跳過警示: {self.stats['skipped_alerts']}")
        
        return all_samples
    
    def save_training_data(self, samples: List[Dict], split_ratio: float = 0.9) -> Dict[str, str]:
        """
        保存訓練數據為JSONL格式
        
        Args:
            samples: 訓練樣本列表
            split_ratio: 訓練集比例（默認90%）
            
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
        train_file = self.output_dir / f"alerts_expert_train_{timestamp}.jsonl"
        self._write_jsonl(train_samples, train_file)
        saved_files["train"] = str(train_file)
        log.info(f"✅ 訓練集: {train_file} ({len(train_samples)} 樣本)")
        
        # 保存驗證集
        if val_samples:
            val_file = self.output_dir / f"alerts_expert_val_{timestamp}.jsonl"
            self._write_jsonl(val_samples, val_file)
            saved_files["val"] = str(val_file)
            log.info(f"✅ 驗證集: {val_file} ({len(val_samples)} 樣本)")
        
        # 保存統計信息
        stats_file = self.output_dir / f"alerts_conversion_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "source_file": str(self.alerts_file),
                "stats": self.stats,
                "files": saved_files,
                "split_ratio": split_ratio,
                "train_samples": len(train_samples),
                "val_samples": len(val_samples)
            }, f, ensure_ascii=False, indent=2)
        
        log.info(f"📊 統計信息: {stats_file}")
        
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
    
    def run(self):
        """執行完整的轉換流程"""
        log.info("=" * 60)
        log.info("🚀 防騙警示轉換為Fine-Tuning訓練數據")
        log.info("=" * 60)
        
        # 轉換所有警示
        samples = self.convert_all_alerts()
        
        # 保存訓練數據
        if samples:
            saved_files = self.save_training_data(samples)
            
            log.info("=" * 60)
            log.info("✅ 完成！")
            log.info("=" * 60)
            log.info(f"📊 總計:")
            log.info(f"   處理警示: {self.stats['processed_alerts']}")
            log.info(f"   生成樣本: {self.stats['generated_samples']}")
            log.info(f"   保存文件: {len(saved_files)}")
            log.info("=" * 60)
            log.info("📝 下一步：")
            log.info("   1. 執行 python backend/scripts/run_finetuning.py --model expert")
            log.info("   2. 或將生成的文件與現有訓練數據合併")
            log.info("=" * 60)
            
            return saved_files
        else:
            log.error("❌ 沒有生成任何訓練樣本")
            return {}


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="將防騙警示轉換為Fine-Tuning訓練數據")
    parser.add_argument(
        "--alerts-file",
        default="data/scraped_alerts.json",
        help="防騙警示JSON文件路徑"
    )
    parser.add_argument(
        "--output-dir",
        default="backend/training_data/finetuning",
        help="輸出目錄"
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.9,
        help="訓練集比例（默認0.9）"
    )
    
    args = parser.parse_args()
    
    converter = AlertsToFineTuningConverter(
        alerts_file=args.alerts_file,
        output_dir=args.output_dir
    )
    
    converter.run()


if __name__ == "__main__":
    main()
