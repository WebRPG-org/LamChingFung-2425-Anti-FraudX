# 🎮 香港反詐騙 RPG 訓練系統

一個基於 Phaser.js 的互動式反詐騙訓練遊戲，結合 AI 技術提供個性化學習體驗。

## ✨ 主要功能

- 🎯 互動式 RPG 遊戲體驗
- 🤖 AI 驅動的 NPC 對話系統
- 👥 多角色扮演（受害者/騙徒/專家）
- 📚 真實詐騙案例學習
- 🎓 個性化訓練路徑
- 📊 學習進度追蹤

## 🚀 快速開始

### 方法 1：自動化部署（推薦）

使用 Ansible 一鍵部署到多台服務器：

```bash
# 1. 安裝 Ansible
pip install -r ansible/requirements.txt

# 2. 配置服務器
vim ansible/inventory/hosts.yml

# 3. 部署
cd ansible
./deploy.sh
```

詳細說明：[Ansible 部署文檔](ansible/QUICKSTART.md)

### 方法 2：手動安裝

#### 前端（RPG 遊戲）

```bash
cd rpg-platform-v2
npm install
npm run dev
```

訪問：http://localhost:3000

#### 後端（AI API）

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

API：http://localhost:5000

## 📦 項目結構

```
AI-Agentv4/
├── rpg-platform-v2/          # 前端遊戲
│   ├── src/
│   │   ├── scenes/           # 遊戲場景
│   │   ├── entities/         # 遊戲實體
│   │   └── systems/          # 遊戲系統
│   └── public/
│       ├── assets/           # 遊戲資源
│       └── maps/             # 地圖文件
├── backend/                  # 後端 API
│   ├── app.py               # Flask 應用
│   ├── models/              # AI 模型
│   └── routes/              # API 路由
├── ansible/                  # 自動化部署 ⭐ 新增
│   ├── playbooks/           # 部署腳本
│   ├── roles/               # Ansible 角色
│   ├── inventory/           # 服務器配置
│   ├── deploy.sh            # 部署腳本
│   └── QUICKSTART.md        # 快速開始
└── rpg_maker_plugins/       # RPG Maker 插件
```

## 🔧 技術棧

### 前端
- **遊戲引擎**: Phaser.js 3.90
- **構建工具**: Vite
- **語言**: TypeScript
- **UI**: 自定義 RPG 風格

### 後端
- **框架**: Flask
- **AI**: OpenAI GPT
- **語言**: Python 3.11

### 部署
- **自動化**: Ansible
- **進程管理**: PM2 + Systemd
- **Web 服務器**: Nginx
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

## 🎮 遊戲操作

- **移動**: 方向鍵 或 WASD
- **互動**: E 鍵
- **切換角色**: 1/2/3 鍵
- **顯示說明**: H 鍵
- **返回主頁**: 右上角按鈕

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

## 📚 文檔

- [Ansible 快速開始](ansible/QUICKSTART.md)
- [Ansible 完整文檔](ansible/README.md)
- [部署總結](ansible/DEPLOYMENT_SUMMARY.md)
- [遊戲開發文檔](rpg-platform-v2/README.md)
- [後端 API 文檔](backend/README.md)

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 許可證

MIT License

## 🎯 路線圖

- [x] 基礎 RPG 遊戲系統
- [x] AI 對話系統
- [x] 多角色系統
- [x] Ansible 自動化部署 ⭐ 新增
- [ ] 多人在線模式
- [ ] 成就系統
- [ ] 排行榜
- [ ] 移動端支持

---

**現在支持一鍵部署到多台服務器！** 🚀

使用 Ansible 自動化部署，輕鬆管理多個環境和服務器。
