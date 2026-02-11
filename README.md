# 🛡️ AI 防詐騙訓練系統

一個創新的多智能體 AI 訓練平台，使用真實詐騙場景模擬幫助用戶識別和防範詐騙。結合 RPG 遊戲、個人對話和自動訓練三種模式，提供全方位的防詐教育體驗。

## ✨ 核心特色

### 🤖 多智能體系統
- **四大 AI 角色**：騙徒、受害者、防詐專家、記錄員
- **動態信任系統**：模擬真實心理變化
- **智能評估**：規則引擎 + AI 混合評估
- **版本控制**：Prompt 版本管理和 A/B 測試

### 🎮 三種訓練模式
- **RPG v2 遊戲**：Phaser.js 打造的 2D 開放世界（13 種騙案類型）
- **RPG v1 遊戲**：RPG Maker MV 經典版（手動/自動訓練）
- **個人對話**：一對一 AI 互動（10 種詐騙場景）
- **自動模擬**：觀看三方 AI 對話（持續生成訓練數據）

### 📊 先進技術
- **RAG 系統**：引用香港警方真實案例
- **混合評估**：每輪規則評分 + 每 3 輪 AI 校準
- **性能追蹤**：自動記錄和分析對話數據
- **GPU 加速**：支持 CUDA + Ollama 本地部署

## 🚀 快速開始

### 前置需求

- **Python 3.10+** - [下載](https://www.python.org/downloads/)
- **Node.js 18+** - [下載](https://nodejs.org/)
- **Ollama** - [安裝指南](https://ollama.ai/)
- **NVIDIA GPU**（可選）- 用於 GPU 加速

### 方法 1：一鍵啟動（推薦）⭐

**Windows 用戶：**
```bash
# 雙擊運行
.\scripts\本地启动.bat

# 或使用 V2 專用腳本
.\启动V2.bat
```

**Linux/Mac 用戶：**
```bash
# 啟動 Ollama
ollama serve &

# 啟動後端
cd backend && python main.py &

# 啟動 RPGv2
cd rpg-platform-v2 && npm install && npm run dev
```

### 方法 2：Docker 部署

```bash
# 構建並啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 方法 3：Ansible 自動化部署（生產環境）

```bash
# 1. 安裝 Ansible
pip install -r ansible/requirements.txt

# 2. 配置服務器
vim ansible/inventory/hosts.yml

# 3. 部署
cd ansible && ./deploy.sh
```

### 訪問地址

啟動成功後，訪問以下地址：

| 服務 | 地址 | 說明 |
|------|------|------|
| 🏠 **主頁** | http://localhost:8000/ | 統一入口，選擇訓練模式 |
| 🎮 **RPGv2** | http://localhost:5173 | 新版 2D RPG 遊戲 |
| 🎯 **RPGv1** | http://localhost:8000/rpg | 經典版 RPG 遊戲 |
| 💬 **個人對話** | http://localhost:8000/RPG_Project/personal_chat_redirect.html | 一對一 AI 對話 |
| 📚 **API 文檔** | http://localhost:8000/docs | FastAPI 自動生成文檔 |

## 📦 項目結構

```
AI-Agentv4/
├── backend/                      # 後端服務（FastAPI + Google ADK）
│   ├── main.py                  # 主應用入口
│   ├── agents/                  # 四大 AI 智能體
│   │   ├── victim.py           # 受害者 Agent
│   │   ├── scammer.py          # 騙徒 Agent
│   │   ├── expert.py           # 防詐專家 Agent
│   │   └── recorder.py         # 記錄員 Agent
│   ├── api/                     # API 路由
│   │   ├── game_routes_v2.py   # RPGv2 遊戲 API
│   │   ├── simulation_routes.py # 模擬訓練 API
│   │   └── prompt_version_routes.py # Prompt 版本管理 API
│   ├── services/                # 業務邏輯層
│   │   ├── agent_service.py    # Agent 服務
│   │   ├── simulation_runner.py # 模擬運行器
│   │   └── prompt_helper.py    # Prompt 輔助函數
│   ├── utils/                   # 工具類
│   │   ├── performance_tracker.py # 性能追蹤
│   │   ├── role_enforcer.py    # 角色一致性檢查
│   │   ├── hybrid_evaluation.py # 混合評估系統
│   │   └── validation.py       # 輸入驗證
│   ├── llms/                    # LLM 集成
│   │   └── ollama_llm.py       # Ollama 客戶端
│   ├── exceptions.py            # 自定義異常（20+ 類）
│   ├── config.py                # 配置管理
│   └── tests/                   # 測試套件（100+ 測試）
├── rpg-platform-v2/             # RPGv2 前端（Phaser.js + TypeScript）
│   ├── src/
│   │   ├── scenes/             # 遊戲場景
│   │   │   ├── WorldMapScene.ts # 世界地圖
│   │   │   ├── BattleScene.ts  # 對話戰鬥
│   │   │   └── ResultScene.ts  # 結果分析
│   │   ├── entities/           # 遊戲實體
│   │   │   ├── Player.ts       # 玩家
│   │   │   └── NPC.ts          # NPC（13 種騙案類型）
│   │   ├── systems/            # 遊戲系統
│   │   │   ├── TrustSystem.ts  # 信任度系統
│   │   │   └── RoleManager.ts  # 角色管理
│   │   ├── services/           # 服務層
│   │   │   └── BackendClient.ts # 後端 API 客戶端
│   │   └── types/
│   │       └── ScamTypes.ts    # 騙案類型定義
│   └── public/
│       └── assets/             # 遊戲資源
├── RPG_platform/                # RPGv1 前端（RPG Maker MV）
│   └── RPG_Project/            # RPG Maker 項目
├── frontend/                    # Web 前端（個人對話模式）
│   ├── index.html              # 主頁
│   ├── app.html                # 自動模擬
│   ├── personal_chat.html      # 個人對話
│   └── css/                    # 樣式文件
├── ansible/                     # 自動化部署
│   ├── playbooks/              # Ansible Playbooks
│   ├── roles/                  # Ansible 角色
│   └── inventory/              # 服務器配置
├── docker/                      # Docker 配置
│   ├── Dockerfile              # 應用容器
│   └── ollama/Dockerfile       # Ollama 容器
├── scripts/                     # 啟動腳本
│   └── 本地启动.bat            # Windows 一鍵啟動
├── docs/                        # 文檔目錄
│   ├── guides/                 # 使用指南
│   └── reports/                # 報告文檔
├── README.md                    # 本文件
├── ARCHITECTURE_DOCUMENTATION.md # 架構文檔（詳細版）
├── PROJECT_DOCUMENTATION.md     # 項目文檔（整合版）
└── docker-compose.yml          # Docker Compose 配置
```

## 🔧 技術棧

### 後端技術
- **框架**: FastAPI 0.104+
- **AI 框架**: Google ADK (Agent Development Kit)
- **LLM**: Ollama (Gemma 3 4B / Llama 3.1 8B)
- **語言**: Python 3.10+
- **數據庫**: SQLite + ChromaDB (向量數據庫)
- **WebSocket**: 實時通信

### 前端技術

**RPGv2（推薦）：**
- **遊戲引擎**: Phaser.js 3.60+
- **語言**: TypeScript
- **構建工具**: Vite
- **狀態管理**: Zustand
- **UI**: 現代化 RPG 風格

**RPGv1（經典）：**
- **引擎**: RPG Maker MV
- **插件**: 自定義 AI 對話插件

**Web 界面：**
- **技術**: HTML5 + CSS3 + JavaScript
- **設計**: Glassmorphism + 深色主題
- **字體**: Outfit + Noto Sans TC

### AI 技術
- **多智能體**: 4 個獨立 AI Agent
- **RAG**: 檢索增強生成（真實案例）
- **Prompt 工程**: 版本控制 + A/B 測試
- **評估系統**: 規則引擎 + AI 混合評估

### 部署技術
- **容器化**: Docker + Docker Compose
- **GPU 支持**: NVIDIA CUDA 12.4+
- **自動化**: Ansible
- **進程管理**: Uvicorn + Systemd
- **Web 服務器**: Nginx（可選）
- **支持系統**: Linux, macOS, Windows

## 📋 部署選項

### 1. 完整部署（前端 + 後端 + Nginx）
```bash
cd ansible
./deploy.sh
```

### 2. 只部署前端
```bash
./deploy.sh --frontend
```

### 3. 只部署後端
```bash
./deploy.sh --backend
```

### 4. 開發環境設置
```bash
./deploy.sh --dev
```

### 5. 更新現有安裝
```bash
./deploy.sh --update
```

## 🌐 多服務器部署

Ansible 支持同時部署到多台服務器：

```yaml
# ansible/inventory/hosts.yml
all:
  children:
    game_servers:
      hosts:
        server1:
          ansible_host: 192.168.1.10
        server2:
          ansible_host: 192.168.1.11
        server3:
          ansible_host: 192.168.1.12
```

```bash
# 部署到所有服務器
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml

# 部署到特定服務器
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml --limit server1
```

## 🎮 使用指南

### RPGv2 遊戲操作

**基本操作：**
- **移動**: WASD 或 方向鍵
- **互動**: E 鍵（靠近 NPC 時）
- **暫停**: ESC 鍵
- **開發者工具**: F12 鍵

**13 種騙案類型：**
1. 💰 虛假投資詐騙
2. 📱 釣魚短訊詐騙
3. 💕 愛情詐騙
4. 👮 假冒官員詐騙
5. 🛒 虛假購物詐騙
6. 💼 求職詐騙
7. 🎁 中獎詐騙
8. 💬 WhatsApp 詐騙
9. 🏦 假冒銀行詐騙
10. ₿ 加密貨幣詐騙
11. 🏠 租屋詐騙
12. 💻 技術支援詐騙
13. ❤️ 虛假慈善詐騙

### 個人對話模式

**兩種角色：**
- **助手模式**：AI 扮演防詐專家，幫助你識別詐騙
- **騙徒模式**：AI 扮演騙徒，測試你的防範能力

**10 種詐騙場景：**
- 假冒官員、投資詐騙、愛情詐騙、釣魚短訊等

**功能：**
- 文字輸入/語音輸入
- 圖片上傳（識別詐騙圖片）
- 實時信任度顯示
- 對話歷史記錄

### 自動模擬模式

**觀看 AI 三方對話：**
- 騙徒 vs 受害者 vs 防詐專家
- 自動生成訓練數據
- 實時信任度變化
- 完整分析報告

## 🔒 安全配置

### 使用 Ansible Vault 保護敏感數據

```bash
# 創建加密文件
ansible-vault create ansible/inventory/group_vars/vault.yml

# 編輯加密文件
ansible-vault edit ansible/inventory/group_vars/vault.yml

# 使用 vault 部署
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml --ask-vault-pass
```

### 配置 SSL/TLS

```yaml
# ansible/inventory/group_vars/all.yml
enable_ssl: true
ssl_cert_path: /etc/ssl/certs/game.crt
ssl_key_path: /etc/ssl/private/game.key
```

## 📊 監控和維護

### 查看服務狀態
```bash
# 在目標服務器上
sudo systemctl status hk-antiscam-rpg-frontend
sudo systemctl status hk-antiscam-rpg-backend
```

### 查看日誌
```bash
# 應用日誌
tail -f /var/log/hk-antiscam-rpg/frontend.log
tail -f /var/log/hk-antiscam-rpg/backend.log

# 系統日誌
sudo journalctl -u hk-antiscam-rpg-frontend -f
sudo journalctl -u hk-antiscam-rpg-backend -f
```

### 重啟服務
```bash
sudo systemctl restart hk-antiscam-rpg-frontend
sudo systemctl restart hk-antiscam-rpg-backend
```

## 🛠️ 開發

### 本地開發

```bash
# 前端
cd rpg-platform-v2
npm run dev

# 後端
cd backend
source venv/bin/activate
python app.py
```

### 使用 Ansible 設置開發環境

```bash
cd ansible
./deploy.sh --dev
```

這會自動：
- 安裝所有依賴
- 克隆代碼
- 配置環境變量
- 設置開發工具

## 📚 完整文檔

### 核心文檔
- **[README.md](README.md)** - 本文件（項目介紹）
- **[ARCHITECTURE_DOCUMENTATION.md](ARCHITECTURE_DOCUMENTATION.md)** - 系統架構（詳細版，974 行）
- **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - 項目文檔（整合版）

### 部署文檔
- **[Ansible 快速開始](ansible/QUICKSTART.md)** - Ansible 部署指南
- **[Ansible 完整文檔](ansible/README.md)** - Ansible 詳細說明
- **[部署總結](ansible/DEPLOYMENT_SUMMARY.md)** - 部署完成報告

### 開發文檔
- **[RPGv2 開發指南](rpg-platform-v2/README.md)** - Phaser.js 遊戲開發
- **[後端測試文檔](backend/tests/README.md)** - 測試套件說明
- **[API 文檔](http://localhost:8000/docs)** - FastAPI 自動生成（需啟動服務）

### 專項文檔
- **[視覺功能說明](docs/guides/視覺功能說明.md)** - 圖片上傳功能
- **[混合模式說明](docs/guides/混合模式說明.md)** - 混合評估系統
- **[語言設置說明](docs/guides/語言設置說明.md)** - 多語言支持

## 🎯 功能特性

### ✅ 已完成功能

**核心系統：**
- [x] 四大 AI 智能體（受害者、騙徒、專家、記錄員）
- [x] 動態信任度系統（慣性、疲勞、情緒乘數）
- [x] RAG 系統（引用真實案例）
- [x] 角色一致性檢查
- [x] WebSocket 實時通信

**Prompt 工程：**
- [x] Prompt 版本控制系統
- [x] 版本註冊、獲取、回退
- [x] A/B 測試框架
- [x] 自動性能記錄
- [x] 最佳版本推薦

**評估系統：**
- [x] 混合評估（規則 + AI）
- [x] 每 3 輪自動校準
- [x] 重複循環檢測
- [x] 明確決定檢測
- [x] 智能中止邏輯

**遊戲平台：**
- [x] RPGv2（Phaser.js，13 種騙案）
- [x] RPGv1（RPG Maker MV）
- [x] 個人對話模式（10 種場景）
- [x] 自動模擬模式

**代碼質量：**
- [x] 100+ 單元測試
- [x] 20+ 自定義異常
- [x] 配置管理系統
- [x] 輸入驗證 + 速率限制
- [x] 完整的錯誤處理

**部署：**
- [x] Docker + Docker Compose
- [x] GPU 支持（CUDA）
- [x] Ansible 自動化部署
- [x] 一鍵啟動腳本

### 🚧 開發中功能

- [ ] 成就系統
- [ ] 排行榜
- [ ] 移動端適配
- [ ] 多語言支持（英文、普通話）

### 💡 未來規劃

- [ ] 自定義騙案編輯器
- [ ] 社區分享平台
- [ ] 企業培訓版本
- [ ] 教育機構合作
- [ ] 數據分析儀表板

## 📊 項目統計

- **總代碼行數**: ~50,000 行
- **Python 代碼**: ~15,000 行
- **TypeScript/JavaScript**: ~10,000 行
- **測試覆蓋率**: 80%+（核心邏輯）
- **AI 智能體**: 4 個
- **騙案類型**: 13 種
- **API 端點**: 50+

## 🏆 技術亮點

1. **創新的多智能體架構** - 四個 AI 協同工作
2. **動態信任系統** - 模擬真實心理變化
3. **混合評估系統** - 平衡準確性和成本
4. **Prompt 版本控制** - 支持快速迭代
5. **RAG 增強** - 引用真實案例
6. **完整測試覆蓋** - 100+ 單元測試
7. **GPU 加速** - 本地部署，保護隱私

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 貢獻指南

1. Fork 本項目
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 許可證

MIT License

---

**🚀 現在支持一鍵啟動和多服務器部署！**

使用 `.\scripts\本地启动.bat` 快速開始，或使用 Ansible 部署到生產環境。
