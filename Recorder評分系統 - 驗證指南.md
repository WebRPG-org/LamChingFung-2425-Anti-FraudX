# Recorder 評分系統 - 驗證指南

## 🧪 如何驗證 Recorder 評分系統

### 步驟 1: 重啟服務器

```bash
# 停止當前服務器（如果正在運行）
Ctrl+C

# 重新啟動
.\本地启动.bat
```

**為什麼**: 確保新的 RecorderAgent instruction 被加載

---

### 步驟 2: 運行測試模擬

```
1. 打開瀏覽器訪問: http://localhost:8000
2. 選擇受害者畫像: average（或其他）
3. 選擇騙局類型: 假冒政府（或其他）
4. 點擊 "開始模擬"
5. 等待模擬完成（約2-5分鐘）
```

---

### 步驟 3: 檢查即時日誌

在服務器控制台中，應該看到**簡化版**的即時日誌：

#### ✅ 正確的日誌格式

```
📊 [騙徒][第1輪] 信任度 - 騙徒: 75/100, 專家: 40/100
📊 [專家][第1輪] 信任度變化 - 騙徒: 70/100, 專家: 50/100
📊 [騙徒][第2輪] 信任度 - 騙徒: 85/100, 專家: 50/100
📊 [專家][第2輪] 信任度變化 - 騙徒: 75/100, 專家: 65/100
```

**特點**:
- ✅ 只顯示信任度，不顯示評分
- ✅ 格式簡潔明了

#### ❌ 錯誤的日誌格式（如果看到這個，說明修改未生效）

```
📊 [騙徒][第1輪] 使用策略: [authority, urgency] 共2項, 信任變化: +30, 效果: ⏳進行中 | 累積評分 - 說服力: 53/100, ...
```

**如果看到這個**: 需要重新啟動服務器

---

### 步驟 4: 檢查 Recorder 最終評分

模擬結束後，應該看到：

```
================================================================================
📊 [Recorder 最終評分]
   🎭 騙徒總分: 78/100
      • 說服力: 75/100
      • 可信度: 80/100
      • 施壓效果: 70/100
      • 策略一致性: 85/100
      ✅ 成功之處: 3項
      ❌ 失敗之處: 2項
   👨‍⚕️ 專家總分: 60/100
      • 干預效果: 60/100
      • 清晰度: 70/100
      • 同理心: 65/100
      • 可執行性: 55/100
      • 時機把握: 50/100
      ✅ 成功之處: 2項
      ❌ 失敗之處: 3項
================================================================================
```

**檢查要點**:
- ✅ 是否顯示了分數（0-100）？
- ✅ 分數是否合理（不是全0或全100）？
- ✅ 是否顯示了成功和失敗之處？

---

### 步驟 5: 檢查詳細分析

#### 5.1 找到保存的 JSON 文件

```
backend/training_data/training_data_ws_[時間戳]_[ID].json
```

例如：
```
backend/training_data/training_data_ws_20251111_180000_abc12345.json
```

#### 5.2 打開文件並檢查

使用文本編輯器打開文件，檢查是否包含：

##### ✅ 應該包含 `scammer_performance`

```json
{
  "analysis": {
    "scammer_performance": {
      "persuasiveness": 75,
      "persuasiveness_analysis": "騙徒的話術流暢且專業，成功模仿銀行職員的語氣...",
      "credibility": 80,
      "credibility_analysis": "騙徒成功保持了銀行職員的角色一致性...",
      "pressure_effectiveness": 70,
      "pressure_analysis": "成功製造時間壓力和財務損失的恐懼...",
      "strategy_consistency": 85,
      "strategy_analysis": "策略一致，從頭到尾使用authority+urgency組合...",
      "overall_score": 78,
      "key_successes": [
        "第2輪：成功打消身份疑慮（提供工作編號）",
        "第4輪：成功製造恐慌（財務損失威脅）",
        "第7輪：靈活應對專家挑戰（製造對立）"
      ],
      "key_failures": [
        "第5輪：對專家反駁略顯生硬",
        "第6輪：面對密碼質疑時回應迴避"
      ]
    }
  }
}
```

**檢查要點**:
- ✅ 是否有 4 個評分維度？（persuasiveness, credibility, pressure_effectiveness, strategy_consistency）
- ✅ 每個維度是否有 `*_analysis` 分析文字？
- ✅ 分析文字是否有至少 50 字？
- ✅ 是否有 `key_successes` 和 `key_failures` 列表？
- ✅ `overall_score` 是否在 0-100 範圍內？

##### ✅ 應該包含 `expert_performance`

```json
{
  "analysis": {
    "expert_performance": {
      "intervention_effectiveness": 60,
      "intervention_analysis": "專家的介入引起了受害者注意，成功降低了部分信任度...",
      "clarity": 70,
      "clarity_analysis": "語言清晰，提供了具體證據和案例...",
      "empathy": 65,
      "empathy_analysis": "有嘗試安撫情緒，在第2輪說『婆婆唔使驚』...",
      "actionability": 55,
      "actionability_analysis": "提供了『打去銀行熱線』的建議，但未提供具體電話號碼...",
      "timing": 50,
      "timing_analysis": "介入時機略晚。當專家在第3輪介入時，受害者對騙徒的信任度已達80/100...",
      "overall_score": 60,
      "key_successes": [
        "第3輪：成功揭穿騙徒部分謊言",
        "第4輪：提供了真實的防騙案例"
      ],
      "key_failures": [
        "介入時機太晚（第3輪而非第2輪）",
        "情緒安撫不夠充分",
        "建議缺少具體執行步驟"
      ]
    }
  }
}
```

**檢查要點**:
- ✅ 是否有 5 個評分維度？（intervention_effectiveness, clarity, empathy, actionability, timing）
- ✅ 每個維度是否有 `*_analysis` 分析文字？
- ✅ 分析文字是否有至少 50 字？
- ✅ 是否有 `key_successes` 和 `key_failures` 列表？
- ✅ `overall_score` 是否在 0-100 範圍內？

---

### 步驟 6: 驗證評分的合理性

#### 6.1 評分範圍檢查

所有評分應該在 **0-100** 範圍內：

```python
# 騙徒評分
0 <= persuasiveness <= 100
0 <= credibility <= 100
0 <= pressure_effectiveness <= 100
0 <= strategy_consistency <= 100
0 <= overall_score <= 100

# 專家評分
0 <= intervention_effectiveness <= 100
0 <= clarity <= 100
0 <= empathy <= 100
0 <= actionability <= 100
0 <= timing <= 100
0 <= overall_score <= 100
```

#### 6.2 評分邏輯檢查

**如果模擬結果是 SUCCESS（專家勝利）**:
- ✅ 專家的 `overall_score` 應該 > 騙徒的 `overall_score`
- ✅ 專家的 `intervention_effectiveness` 應該較高（60+）
- ✅ 專家的 `timing` 應該合理（不要太低）

**如果模擬結果是 FAILURE（騙徒勝利）**:
- ✅ 騙徒的 `overall_score` 應該 > 專家的 `overall_score`
- ✅ 騙徒的 `persuasiveness` 應該較高（70+）
- ✅ 專家的 `intervention_effectiveness` 應該較低（<50）

#### 6.3 分析文字檢查

**好的分析文字應該**:
- ✅ 有至少 50 字
- ✅ 提到具體的輪次（如「第2輪」「第4輪」）
- ✅ 提到具體的策略或話術
- ✅ 解釋為什麼給這個分數

**範例（好的分析）**:
```
"騙徒的話術流暢且專業，成功模仿銀行職員的語氣。特別是在第2輪，當受害者質疑身份時，騙徒用『我可以提供工作編號XXX』來打消疑慮，這個細節非常真實。在第4輪使用的『你帳戶會被凍結』威脅，成功觸發了elderly型受害者對財務損失的恐懼。唯一的小瑕疵是在第5輪對專家的反駁略顯生硬，沒有完全打消受害者的疑慮（信任度從95下降到85）。整體說服力評分75/100。"
```

**不好的分析（如果看到這個，說明有問題）**:
```
"騙徒的話術很好。評分75/100。"  # ❌ 太短，沒有具體細節
```

---

## 🐛 常見問題排查

### 問題 1: 日誌中沒有顯示 Recorder 評分

**症狀**:
```
模擬結束後，只看到：
✅ RecorderAgent 分析完成，包含字段: ['outcome', 'victim_persona', ...]

但沒有看到：
================================================================================
📊 [Recorder 最終評分]
...
```

**原因**: `_log_recorder_scores` 沒有被調用，或者 JSON 中缺少 `scammer_performance` 或 `expert_performance` 字段

**解決方案**:
1. 檢查服務器是否重啟
2. 檢查 `_generate_recorder_analysis` 是否調用了 `_log_recorder_scores`
3. 檢查 RecorderAgent 是否正確生成了 `scammer_performance` 和 `expert_performance`

---

### 問題 2: JSON 中沒有性能評分

**症狀**:
打開 JSON 文件，沒有找到 `scammer_performance` 或 `expert_performance` 字段

**原因**: RecorderAgent 沒有按照新的 instruction 生成評分

**解決方案**:
1. **檢查 RecorderAgent 是否使用了新的 instruction**:
   ```bash
   # 查看日誌中 RecorderAgent 初始化信息
   # 應該看到：
   🎭 RecorderAgent 初始化 - 模型: gemma3:4b
   ```

2. **檢查 Recorder 的輸出是否包含評分**:
   - 如果沒有，可能是 AI 沒有遵循新的 instruction
   - 可能需要多次測試，或檢查 instruction 的格式

3. **檢查 fallback 邏輯是否被觸發**:
   ```bash
   # 查看日誌中是否有：
   ❌ RecorderAgent JSON 解析失敗
   ```
   - 如果有，說明 Recorder 輸出格式有問題

---

### 問題 3: 評分都是 0 或 100

**症狀**:
所有評分都是 0 或 100，沒有中間值

**原因**: Recorder 沒有正確理解評分標準

**解決方案**:
1. 檢查 RecorderAgent 的 instruction 是否完整
2. 多次運行測試，看是否是偶發問題
3. 檢查使用的模型（gemma3:4b）是否支持複雜的評分任務

---

### 問題 4: 分析文字太短或不相關

**症狀**:
`persuasiveness_analysis` 等字段只有幾個字，或者內容不相關

**原因**: Recorder 沒有充分分析對話

**解決方案**:
1. 在 instruction 中明確要求「至少50字」
2. 提供更詳細的示例
3. 在 prompt 中重複強調分析的重要性

---

## ✅ 驗證成功標準

當你看到以下所有項目都符合時，說明系統正常工作：

- [x] 即時日誌只顯示信任度，不顯示詳細評分
- [x] 模擬結束後顯示 Recorder 最終評分（格式化的文本）
- [x] JSON 文件中包含完整的 `scammer_performance`（4個維度 + 分析）
- [x] JSON 文件中包含完整的 `expert_performance`（5個維度 + 分析）
- [x] 每個評分都在 0-100 範圍內
- [x] 每個分析文字都有至少 50 字
- [x] `key_successes` 和 `key_failures` 列表包含具體條目
- [x] 評分結果符合模擬的實際情況（SUCCESS時專家分高，FAILURE時騙徒分高）

---

## 📧 報告問題

如果驗證失敗，請提供以下信息：

1. **服務器日誌**（特別是 RecorderAgent 相關的部分）
2. **生成的 JSON 文件**（`training_data_ws_*.json`）
3. **問題描述**（哪一步出錯了？）
4. **預期結果 vs 實際結果**

---

**文檔版本**: v1.0  
**創建時間**: 2024-11-11  
**更新時間**: 2024-11-11

