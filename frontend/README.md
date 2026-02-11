# 前端儀表板使用指南

**版本**: 1.0  
**創建日期**: 2026-02-10

---

## 📋 概述

前端儀表板提供了兩個主要界面：
1. **監控儀表板** (`dashboard.html`) - 實時監控系統性能和統計數據
2. **評估界面** (`evaluate.html`) - 交互式對話評估工具

---

## 🚀 快速開始

### 1. 啟動後端服務

```bash
# 確保在項目根目錄
cd /c:/Users/fungr/Documents/AI-Agentv4

# 啟動FastAPI服務
uvicorn backend.main:app --reload --port 8000
```

### 2. 打開前端界面

```bash
# 方法1: 直接在瀏覽器打開
# 打開 frontend/dashboard.html 或 frontend/evaluate.html

# 方法2: 使用簡單HTTP服務器
cd frontend
python -m http.server 8080

# 然後訪問:
# http://localhost:8080/dashboard.html
# http://localhost:8080/evaluate.html
```

---

## 📊 監控儀表板 (dashboard.html)

### 功能特性

#### 1. 實時統計卡片
- **總評估數** - 系統啟動以來的總評估次數
- **成功率** - 評估成功的百分比
- **平均延遲** - 評估的平均響應時間
- **平均信心度** - 評估結果的平均信心度

#### 2. 可視化圖表
- **評估方法分布** - 規則/Agent/混合評分的使用比例（圓餅圖）
- **人設分布** - 不同人設的評估次數（柱狀圖）
- **評估延遲趨勢** - 過去1小時的延遲變化（折線圖）
- **成功率趨勢** - 過去1小時的成功率變化（折線圖）

#### 3. 最近評估記錄
顯示最近20次評估的詳細信息：
- 時間戳
- 人設類型
- 信任度變化
- 信心度
- 評估方法
- 延遲時間
- 狀態

#### 4. 控制按鈕
- **刷新數據** - 手動刷新儀表板數據
- **清除緩存** - 清除評估器緩存
- **重置統計** - 重置所有統計數據
- **導出數據** - 導出監控數據為JSON

### 使用方法

1. **自動刷新**: 儀表板每30秒自動刷新一次
2. **手動刷新**: 點擊"刷新數據"按鈕立即更新
3. **查看詳情**: 將鼠標懸停在圖表上查看具體數值
4. **導出數據**: 點擊"導出數據"下載完整的監控數據

### 設計特色

- **深色主題** - 現代化的深色配色方案
- **漸變效果** - 使用青色到紫色的漸變
- **動畫效果** - 平滑的過渡和懸停效果
- **響應式設計** - 適配桌面和移動設備

---

## ✨ 評估界面 (evaluate.html)

### 功能特性

#### 1. 對話構建
- **添加訊息** - 逐條添加詐騙者和受害人的對話
- **角色選擇** - 選擇詐騙者或受害人
- **策略選擇** - 為詐騙者選擇策略（權威、緊急、同情等）
- **訊息管理** - 刪除、清空對話
- **載入示例** - 快速載入預設的對話示例

#### 2. 評估設置
- **受害人人設** - 選擇老年人/普通人/過度自信/學生
- **初始信任度** - 設置初始信任度（0-100）
- **規則權重** - 調整規則評分的權重（0-1）
- **Agent權重** - 調整Agent評分的權重（自動計算）
- **啟用Agent評分** - 開關Agent評分功能

#### 3. 評估結果
顯示評估結果：
- **信任度變化** - 正值表示警覺性上升，負值表示下降
- **信心度** - 評估結果的可信度
- **評估方法** - 使用的評分方法（rule/agent/hybrid）
- **評估時間** - 評估耗時（毫秒）

### 使用方法

#### 基本流程

1. **構建對話**
   ```
   1. 選擇角色（詐騙者/受害人）
   2. 如果是詐騙者，選擇策略
   3. 輸入訊息內容
   4. 點擊"添加訊息"
   5. 重複以上步驟構建完整對話
   ```

2. **配置設置**
   ```
   1. 選擇受害人人設
   2. 調整初始信任度
   3. 調整評分權重（推薦7:3）
   4. 決定是否啟用Agent評分
   ```

3. **執行評估**
   ```
   1. 點擊"開始評估"按鈕
   2. 等待評估完成（通常<1秒）
   3. 查看評估結果
   ```

#### 快速示例

點擊"載入示例"按鈕，系統會自動載入一個高壓詐騙案例：
```
詐騙者: 你好，我是警察局的，你的銀行帳戶涉嫌洗錢！
受害人: 什麼？我沒有做違法的事啊！
詐騙者: 現在必須立即配合調查，否則會凍結你所有資產！
受害人: 那我該怎麼辦？
```

### 設計特色

- **雙欄布局** - 左側對話構建，右側設置和結果
- **實時預覽** - 對話訊息實時顯示
- **顏色編碼** - 詐騙者（紅色）、受害人（綠色）
- **交互式控制** - 滑塊、下拉選單、複選框

---

## 🎨 設計系統

### 配色方案

```css
--bg-primary: #0a0e27        /* 主背景 - 深藍黑 */
--bg-secondary: #151932      /* 次背景 - 深藍 */
--bg-card: #1a1f3a          /* 卡片背景 - 藍灰 */
--accent-primary: #00d9ff    /* 主色調 - 青色 */
--accent-secondary: #7b2cbf  /* 次色調 - 紫色 */
--accent-success: #06ffa5    /* 成功色 - 綠色 */
--accent-warning: #ffb800    /* 警告色 - 黃色 */
--accent-danger: #ff006e     /* 危險色 - 紅色 */
--text-primary: #e8f1f5      /* 主文字 - 淺灰 */
--text-secondary: #8892b0    /* 次文字 - 灰藍 */
```

### 字體

- **主字體**: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI'
- **標題**: 700 (Bold)
- **正文**: 400 (Regular)
- **小標**: 600 (Semi-bold)

### 動畫效果

- **懸停效果**: 卡片上移4px，陰影增強
- **過渡時間**: 0.3s ease
- **載入動畫**: 旋轉動畫 0.8s
- **脈衝動畫**: 狀態指示器 2s

---

## 🔧 配置

### API端點配置

在HTML文件中修改API基礎URL：

```javascript
// 默認配置
const API_BASE = 'http://localhost:8000/api/v2';

// 如果後端在不同端口或域名
const API_BASE = 'http://your-server:8000/api/v2';
```

### 自動刷新間隔

在`dashboard.html`中修改：

```javascript
// 默認30秒
setInterval(refreshData, 30000);

// 修改為60秒
setInterval(refreshData, 60000);
```

---

## 📱 響應式設計

### 桌面端 (>1024px)
- 雙欄布局
- 完整圖表顯示
- 側邊欄固定

### 平板端 (768px-1024px)
- 單欄布局
- 圖表自適應
- 側邊欄滾動

### 移動端 (<768px)
- 單欄布局
- 簡化統計卡片
- 觸摸優化

---

## 🐛 故障排除

### 問題1: 無法連接到API

**症狀**: 顯示"無法連接到API服務"

**解決方案**:
```bash
# 1. 確認後端服務已啟動
curl http://localhost:8000/api/v2/scoring/health

# 2. 檢查端口是否正確
# 3. 檢查CORS設置（如果跨域）
```

### 問題2: 圖表不顯示

**症狀**: 圖表區域空白

**解決方案**:
```bash
# 1. 確認Chart.js已載入
# 2. 檢查瀏覽器控制台錯誤
# 3. 確認有評估數據
```

### 問題3: 評估失敗

**症狀**: 點擊"開始評估"後報錯

**解決方案**:
```bash
# 1. 確認對話不為空
# 2. 檢查權重總和是否為1.0
# 3. 查看後端日誌
```

---

## 🚀 部署建議

### 開發環境

```bash
# 使用Python簡單服務器
cd frontend
python -m http.server 8080
```

### 生產環境

#### 選項1: Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/frontend;
    index dashboard.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 選項2: Apache

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /path/to/frontend
    
    <Directory /path/to/frontend>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ProxyPass /api/ http://localhost:8000/api/
    ProxyPassReverse /api/ http://localhost:8000/api/
</VirtualHost>
```

---

## 📊 性能優化

### 1. 圖表優化

```javascript
// 限制數據點數量
const MAX_DATA_POINTS = 50;

// 使用防抖
let refreshTimeout;
function debouncedRefresh() {
    clearTimeout(refreshTimeout);
    refreshTimeout = setTimeout(refreshData, 300);
}
```

### 2. 緩存策略

```javascript
// 緩存API響應
const cache = new Map();
const CACHE_TTL = 30000; // 30秒

async function fetchWithCache(url) {
    const cached = cache.get(url);
    if (cached && Date.now() - cached.time < CACHE_TTL) {
        return cached.data;
    }
    
    const data = await fetch(url).then(r => r.json());
    cache.set(url, { data, time: Date.now() });
    return data;
}
```

---

## 🎓 最佳實踐

### 1. 監控儀表板
- 定期查看成功率和延遲
- 關注異常峰值
- 及時清理緩存

### 2. 評估界面
- 使用真實的對話場景
- 測試不同人設和策略組合
- 記錄有趣的評估結果

### 3. 性能
- 避免過於頻繁的刷新
- 限制對話長度（建議<20條）
- 使用純規則模式以獲得最快速度

---

## 📚 相關資源

- [Chart.js文檔](https://www.chartjs.org/docs/)
- [MDN Web文檔](https://developer.mozilla.org/)
- [API文檔](../DEPLOYMENT_GUIDE.md)

---

**最後更新**: 2026-02-10  
**維護者**: AI Agent Team
