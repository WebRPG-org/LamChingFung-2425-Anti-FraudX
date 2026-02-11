"""
Fine-Tuning 格式化工具
將模擬對話轉換為 Ollama fine-tuning 所需的格式
支持 JSONL 格式輸出，用於訓練專家和騙徒模型
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils.logger import log

# 獲取項目根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent


class FineTuningFormatter:
    """
    將模擬對話數據轉換為 Fine-Tuning 格式
    
    支持兩種模型訓練：
    1. 專家模型 (Expert Model): 學習如何有效識破騙局並勸導受害者
    2. 騙徒模型 (Scammer Model): 學習常見騙術話術（僅用於模擬測試）
    """
    
    def __init__(self, output_dir: str = "backend/training_data/finetuning"):
        # 使用絕對路徑
        if Path(output_dir).is_absolute():
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = PROJECT_ROOT / output_dir
        
        # 確保目錄存在
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            log.info(f"📁 Fine-tuning 輸出目錄: {self.output_dir}")
        except Exception as e:
            log.error(f"❌ 創建輸出目錄失敗: {e}")
            raise
        
    def format_for_expert_training(
        self,
        conversation_history: List[Dict[str, str]],
        analysis: Dict[str, Any],
        performance_report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        將對話轉換為專家模型訓練格式
        
        策略：
        1. 成功案例：專家的所有回應都作為正面樣本
        2. 失敗案例：只提取導致信任度提升的回應（部分成功的干預）
        3. 每個樣本包含完整上下文，幫助模型學習策略調整
        """
        training_samples = []
        
        outcome = analysis.get("outcome", "UNKNOWN")
        expert_score = performance_report.get("expert_overall_score", 0)
        
        # 獲取信任度變化歷史
        trust_history = performance_report.get("victim_trust_history", [])
        
        log.info(f"🎯 處理專家訓練樣本 (outcome={outcome}, expert_score={expert_score})")
        
        # 提取每一輪專家的回應
        for i, turn in enumerate(conversation_history):
            if turn.get("speaker") != "專家":
                continue
            
            # 構建上下文：前4輪完整對話（更多上下文有助於學習）
            context_turns = conversation_history[max(0, i-4):i]
            
            # 構建system prompt - 包含專家的完整人設
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
            
            # 構建用戶輸入 - 更結構化的格式
            user_input = "【情境】正在進行的詐騙對話，請你作為反詐騙專家介入。\n\n"
            user_input += "【對話記錄】\n"
            
            for ctx_turn in context_turns:
                speaker = ctx_turn.get("speaker", "未知")
                dialogue = ctx_turn.get("dialogue", "")
                user_input += f"{speaker}：{dialogue}\n"
            
            user_input += "\n【你的任務】作為黃sir，請給出你的專業建議："
            
            # 專家的實際回應
            expert_response = turn.get("dialogue", "")
            
            # 判斷此回應的質量
            quality_score, reason = self._evaluate_expert_response(
                i, turn, conversation_history, trust_history, outcome
            )
            
            # 策略：
            # - 成功案例：所有回應都保留（quality_score >= 0）
            # - 失敗案例：只保留高質量回應（quality_score > 50）
            if outcome == "SUCCESS":
                should_include = True
            else:
                should_include = (quality_score > 50)
            
            if not should_include:
                log.debug(f"⏭️ 跳過第{i+1}輪專家回應 (quality={quality_score}, reason={reason})")
                continue
            
            # 構建訓練樣本
            sample = {
                "system": system_prompt,
                "user": user_input,
                "assistant": expert_response,
                "metadata": {
                    "round": i + 1,
                    "total_rounds": len(conversation_history),
                    "outcome": outcome,
                    "expert_score": expert_score,
                    "quality_score": quality_score,
                    "quality_reason": reason,
                    "victim_persona": analysis.get("victim_persona", "unknown"),
                    "scam_tactic": analysis.get("scam_tactic", "unknown"),
                    "data_quality": "high" if outcome == "SUCCESS" else "medium"
                }
            }
            
            training_samples.append(sample)
            log.debug(f"✅ 添加第{i+1}輪專家訓練樣本 (quality={quality_score})")
        
        log.info(f"📦 生成 {len(training_samples)} 個專家訓練樣本")
        return training_samples
    
    def format_for_scammer_training(
        self,
        conversation_history: List[Dict[str, str]],
        analysis: Dict[str, Any],
        performance_report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        將對話轉換為騙徒模型訓練格式
        
        策略：
        1. 成功迷惑受害者的話術作為正面樣本
        2. 被專家識破的話術作為負面樣本（可用於反向學習）
        3. 包含完整的騙術策略和心理操縱技巧
        
        注意：僅用於反詐騙訓練和測試，不得用於實際詐騙
        """
        training_samples = []
        
        outcome = analysis.get("outcome", "UNKNOWN")
        scammer_score = performance_report.get("scammer_overall_score", 0)
        scam_tactic = analysis.get("scam_tactic", "unknown")
        
        # 獲取信任度變化歷史
        trust_history = performance_report.get("victim_trust_history", [])
        
        log.info(f"🎭 處理騙徒訓練樣本 (outcome={outcome}, scammer_score={scammer_score})")
        
        # 策略：
        # - 失敗案例（騙徒成功）：所有騙徒話術都作為正面樣本
        # - 成功案例（專家成功）：只提取前期成功迷惑受害者的話術
        
        # 提取每一輪騙徒的回應
        for i, turn in enumerate(conversation_history):
            if turn.get("speaker") != "騙徒":
                continue
            
            # 構建上下文：前3輪對話
            context_turns = conversation_history[max(0, i-3):i]
            
            # 構建system prompt - 包含騙徒的完整策略
            system_prompt = f"""⚠️  ⚠️

你是一個真實而且專業的騙徒。
你正在扮演：{scam_tactic}

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
            
            # 構建用戶輸入 - 更結構化
            user_input = f"【模擬情境】你正在進行{scam_tactic}詐騙模擬（僅用於訓練）。\n\n"
            user_input += "【對話記錄】\n"
            
            for ctx_turn in context_turns:
                speaker = ctx_turn.get("speaker", "未知")
                dialogue = ctx_turn.get("dialogue", "")
                user_input += f"{speaker}：{dialogue}\n"
            
            user_input += "\n【你的任務】作為騙徒，請給出你的下一句話："
            
            # 騙徒的實際回應
            scammer_response = turn.get("dialogue", "")
            
            # 判斷此回應的質量（從騙徒角度）
            effectiveness_score, reason = self._evaluate_scammer_response(
                i, turn, conversation_history, trust_history, outcome
            )
            
            # 策略：
            # - 失敗案例（騙徒成功）：所有回應都保留
            # - 成功案例（專家成功）：只保留高效的話術（effectiveness > 50）
            if outcome == "FAILURE":
                should_include = True
            else:
                should_include = (effectiveness_score > 50)
            
            if not should_include:
                log.debug(f"⏭️ 跳過第{i+1}輪騙徒回應 (effectiveness={effectiveness_score}, reason={reason})")
                continue
            
            # 構建訓練樣本
            sample = {
                "system": system_prompt,
                "user": user_input,
                "assistant": scammer_response,
                "metadata": {
                    "round": i + 1,
                    "total_rounds": len(conversation_history),
                    "outcome": outcome,
                    "scammer_score": scammer_score,
                    "effectiveness_score": effectiveness_score,
                    "effectiveness_reason": reason,
                    "victim_persona": analysis.get("victim_persona", "unknown"),
                    "scam_tactic": scam_tactic,
                    "data_quality": "high" if outcome == "FAILURE" else "medium",
                    "warning": "⚠️ 僅用於反詐騙訓練，嚴禁用於實際詐騙"
                }
            }
            
            training_samples.append(sample)
            log.debug(f"✅ 添加第{i+1}輪騙徒訓練樣本 (effectiveness={effectiveness_score})")
        
        log.info(f"📦 生成 {len(training_samples)} 個騙徒訓練樣本")
        return training_samples
    
    def save_to_jsonl(
        self,
        samples: List[Dict[str, Any]],
        model_type: str,  # "expert" or "scammer"
        simulation_id: str
    ) -> str:
        """
        將訓練樣本保存為 JSONL 格式
        
        Args:
            samples: 訓練樣本列表
            model_type: 模型類型（expert/scammer）
            simulation_id: 模擬ID
            
        Returns:
            保存的文件路徑
        """
        if not samples:
            log.warning(f"沒有訓練樣本可保存 (model_type={model_type})")
            return ""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"finetune_{model_type}_{timestamp}_{simulation_id[:8]}.jsonl"
            filepath = self.output_dir / filename
            
            log.info(f"📝 準備保存到: {filepath}")
            log.info(f"   目錄存在: {self.output_dir.exists()}")
            log.info(f"   目錄可寫: {os.access(self.output_dir, os.W_OK)}")
            
            # 寫入 JSONL 格式
            with open(filepath, 'w', encoding='utf-8') as f:
                for sample in samples:
                    # Ollama fine-tuning 格式
                    jsonl_line = {
                        "messages": [
                            {"role": "system", "content": sample["system"]},
                            {"role": "user", "content": sample["user"]},
                            {"role": "assistant", "content": sample["assistant"]}
                        ],
                        "metadata": sample.get("metadata", {})
                    }
                    f.write(json.dumps(jsonl_line, ensure_ascii=False) + '\n')
            
            # 驗證文件已創建
            if filepath.exists():
                file_size = filepath.stat().st_size
                log.info(f"✅ 已保存 {len(samples)} 個訓練樣本到: {filepath}")
                log.info(f"   文件大小: {file_size} bytes")
                return str(filepath)
            else:
                log.error(f"❌ 文件保存失敗，文件不存在: {filepath}")
                return ""
                
        except Exception as e:
            log.error(f"❌ 保存訓練樣本時出錯: {e}", exc_info=True)
            return ""
    
    def save_unified_format(
        self,
        conversation_history: List[Dict[str, str]],
        analysis: Dict[str, Any],
        performance_report: Dict[str, Any],
        metadata: Dict[str, Any],
        simulation_id: str
    ) -> Dict[str, str]:
        """
        統一保存所有格式
        
        Returns:
            字典包含所有生成的文件路徑
        """
        saved_files = {}
        
        # 1. 生成專家訓練數據
        expert_samples = self.format_for_expert_training(
            conversation_history, analysis, performance_report
        )
        if expert_samples:
            expert_path = self.save_to_jsonl(expert_samples, "expert", simulation_id)
            saved_files["expert_training"] = expert_path
        
        # 2. 生成騙徒訓練數據
        scammer_samples = self.format_for_scammer_training(
            conversation_history, analysis, performance_report
        )
        if scammer_samples:
            scammer_path = self.save_to_jsonl(scammer_samples, "scammer", simulation_id)
            saved_files["scammer_training"] = scammer_path
        
        # 3. 保存完整的原始數據（用於分析）
        full_data = {
            "conversation_history": conversation_history,
            "analysis": analysis,
            "performance_report": performance_report,
            "metadata": metadata
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"training_data_ws_{timestamp}_{simulation_id[:8]}.json"
        full_filepath = Path("backend/training_data") / full_filename
        
        with open(full_filepath, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        saved_files["full_data"] = str(full_filepath)
        
        log.info(f"📊 訓練數據保存完成：")
        for key, path in saved_files.items():
            log.info(f"  - {key}: {path}")
        
        return saved_files
    
    def _evaluate_expert_response(
        self,
        round_index: int,
        turn: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        trust_history: List[Dict[str, Any]],
        outcome: str
    ) -> tuple[int, str]:
        """
        評估專家回應的質量
        
        返回：(quality_score, reason)
        - quality_score: 0-100，越高越好
        - reason: 評分原因
        """
        score = 50  # 基礎分
        reasons = []
        
        dialogue = turn.get("dialogue", "")
        
        # 1. 內容質量檢查
        if len(dialogue) < 20:
            score -= 20
            reasons.append("回應過短")
        elif len(dialogue) > 300:
            score -= 10
            reasons.append("回應過長")
        else:
            score += 10
            reasons.append("長度適中")
        
        # 2. 檢查是否包含關鍵要素
        if "唔使驚" in dialogue or "唔洗擔心" in dialogue or "冷靜" in dialogue:
            score += 15
            reasons.append("包含情緒安撫")
        
        if "騙" in dialogue or "詐騙" in dialogue or "假" in dialogue:
            score += 10
            reasons.append("直接指出詐騙")
        
        if "掛線" in dialogue or "報警" in dialogue or "打去銀行" in dialogue:
            score += 15
            reasons.append("提供具體行動建議")
        
        if "案例" in dialogue or "上次" in dialogue or "類似" in dialogue:
            score += 10
            reasons.append("引用真實案例")
        
        # 3. 檢查信任度變化
        # 查找此輪之後的信任度變化
        for i, trust_change in enumerate(trust_history):
            if trust_change.get("round", 0) > round_index:
                if trust_change.get("type") == "expert_trust":
                    change = trust_change.get("change", 0)
                    if change > 0:
                        score += min(20, change)
                        reasons.append(f"專家信任度提升{change}")
                        break
                elif trust_change.get("type") == "scammer_trust":
                    change = trust_change.get("change", 0)
                    if change < 0:
                        score += min(20, abs(change))
                        reasons.append(f"騙徒信任度下降{abs(change)}")
                        break
        
        # 4. 最終結果加成
        if outcome == "SUCCESS":
            score += 10
            reasons.append("最終成功")
        
        # 限制範圍
        score = max(0, min(100, score))
        
        reason_text = "; ".join(reasons) if reasons else "無特殊原因"
        return score, reason_text
    
    def _evaluate_scammer_response(
        self,
        round_index: int,
        turn: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        trust_history: List[Dict[str, Any]],
        outcome: str
    ) -> tuple[int, str]:
        """
        評估騙徒回應的有效性（從騙徒角度）
        
        返回：(effectiveness_score, reason)
        - effectiveness_score: 0-100，越高表示騙術越有效
        - reason: 評分原因
        """
        score = 50  # 基礎分
        reasons = []
        
        dialogue = turn.get("dialogue", "")
        
        # 1. 檢查關鍵詐騙話術
        if "立即" in dialogue or "馬上" in dialogue or "限時" in dialogue:
            score += 10
            reasons.append("製造緊迫感")
        
        if "警察" in dialogue or "警司" in dialogue or "銀行" in dialogue or "法院" in dialogue:
            score += 10
            reasons.append("偽裝權威")
        
        if "凍結" in dialogue or "洗黑錢" in dialogue or "涉嫌" in dialogue:
            score += 10
            reasons.append("製造恐懼")
        
        if "回報" in dialogue or "賺錢" in dialogue or "保證" in dialogue:
            score += 10
            reasons.append("利用貪婪")
        
        # 2. 檢查信任度變化
        for i, trust_change in enumerate(trust_history):
            if trust_change.get("round", 0) > round_index:
                if trust_change.get("type") == "scammer_trust":
                    change = trust_change.get("change", 0)
                    if change > 0:
                        score += min(25, change)
                        reasons.append(f"騙徒信任度提升{change}")
                        break
                elif trust_change.get("type") == "expert_trust":
                    change = trust_change.get("change", 0)
                    if change < 0:
                        score += min(15, abs(change))
                        reasons.append(f"專家信任度下降{abs(change)}")
                        break
        
        # 3. 最終結果加成
        if outcome == "FAILURE":
            score += 15
            reasons.append("最終騙局成功")
        
        # 限制範圍
        score = max(0, min(100, score))
        
        reason_text = "; ".join(reasons) if reasons else "無特殊原因"
        return score, reason_text


# 便捷函數
def format_and_save_training_data(
    conversation_history: List[Dict[str, str]],
    analysis: Dict[str, Any],
    performance_report: Dict[str, Any],
    metadata: Dict[str, Any],
    simulation_id: str
) -> Dict[str, str]:
    """
    便捷函數：一次性格式化並保存所有訓練數據
    """
    formatter = FineTuningFormatter()
    return formatter.save_unified_format(
        conversation_history,
        analysis,
        performance_report,
        metadata,
        simulation_id
    )


if __name__ == "__main__":
    # 測試代碼
    print("Fine-Tuning Formatter 工具已就緒")
    print(f"輸出目錄: backend/training_data/finetuning")

